from queue import Queue

import numpy as np


class Communicator:
    def __init__(self, num_devices):
        self.num_devices = num_devices
        self.inboxes = [Queue() for _ in range(num_devices)]

    def send(self, src, dst, data):
        self.inboxes[dst].put((src, data))

    def recv(self, dst):
        return self.inboxes[dst].get()


def _inputs(a, b, num_devices):
    a = np.asarray(a)
    b = np.asarray(b)
    assert a.ndim == b.ndim == 2
    assert isinstance(num_devices, int) and num_devices > 0
    assert a.shape[1] == b.shape[0]
    assert a.shape[0] % num_devices == 0
    assert b.shape[1] % num_devices == 0
    return a, b


def dp_mat_mul(a, b, num_devices):
    a, b = _inputs(a, b, num_devices)
    comm = Communicator(num_devices)
    a_rows = np.split(a, num_devices, axis=0)
    outputs = [a_rows[0] @ b]
    for rank in range(1, num_devices):
        comm.send(0, rank, b)
        _, replica = comm.recv(rank)
        comm.send(rank, 0, a_rows[rank] @ replica)
    for _ in range(1, num_devices):
        _, block = comm.recv(0)
        outputs.append(block)
    return np.concatenate(outputs, axis=0)


def fsdp_mat_mul_all_gather(a, b, num_devices):
    a, b = _inputs(a, b, num_devices)
    comm = Communicator(num_devices)
    a_rows = np.split(a, num_devices, axis=0)
    b_shards = np.split(b, num_devices, axis=1)
    for owner, shard in enumerate(b_shards):
        for rank in range(num_devices):
            if rank != owner:
                comm.send(owner, rank, shard)
    outputs = []
    for rank in range(num_devices):
        owned = {rank: b_shards[rank]}
        for _ in range(num_devices - 1):
            owner, shard = comm.recv(rank)
            owned[owner] = shard
        block = np.concatenate(
            [a_rows[rank] @ owned[owner] for owner in range(num_devices)],
            axis=1,
        )
        if rank == 0:
            outputs.append(block)
        else:
            comm.send(rank, 0, block)
    for _ in range(1, num_devices):
        _, block = comm.recv(0)
        outputs.append(block)
    return np.concatenate(outputs, axis=0)


def fsdp_mat_mul_ring(a, b, num_devices):
    a, b = _inputs(a, b, num_devices)
    comm = Communicator(num_devices)
    a_rows = np.split(a, num_devices, axis=0)
    b_shards = np.split(b, num_devices, axis=1)
    known = [{rank: b_shards[rank]} for rank in range(num_devices)]
    current = [(rank, b_shards[rank]) for rank in range(num_devices)]
    for _ in range(num_devices - 1):
        for rank, payload in enumerate(current):
            comm.send(rank, (rank + 1) % num_devices, payload)
        following = []
        for rank in range(num_devices):
            _, payload = comm.recv(rank)
            owner, shard = payload
            known[rank][owner] = shard
            following.append(payload)
        current = following
    outputs = []
    for rank in range(num_devices):
        block = np.concatenate(
            [a_rows[rank] @ known[rank][owner] for owner in range(num_devices)],
            axis=1,
        )
        if rank == 0:
            outputs.append(block)
        else:
            comm.send(rank, 0, block)
    for _ in range(1, num_devices):
        _, block = comm.recv(0)
        outputs.append(block)
    return np.concatenate(outputs, axis=0)
