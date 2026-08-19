import bisect
import json
import struct
import threading
from collections import defaultdict, deque
from heapq import heappop, heappush


class EventBus:
    def __init__(self):
        self._callbacks = defaultdict(list)

    def subscribe(self, name, callback):
        self._callbacks[name].append(callback)

    def emit(self, name, payload):
        for callback in list(self._callbacks[name]):
            callback(payload)


class ChatRoom:
    def __init__(self):
        self.bus = EventBus()
        self.history = []

    def register(self, bot):
        bot.attach(self)

    def send(self, sender, text):
        message = {"sender": sender, "text": text, "kind": "user"}
        self.history.append(message)
        self.bus.emit("message_received", message)

    def post_bot(self, bot, text):
        self.history.append({"sender": bot.name, "text": text, "kind": "bot"})


class AwayBot:
    def __init__(self, owner):
        self.owner = owner
        self.name = "away-bot:" + owner
        self.away = False

    def attach(self, room):
        self.room = room
        room.bus.subscribe("message_received", self._on_message)

    def _on_message(self, message):
        if message["sender"] == self.owner and message["text"] == "/away":
            self.away = not self.away
            self.room.bus.emit("away_status_changed", {"owner": self.owner, "away": self.away})
        elif self.away and message["sender"] != self.owner:
            self.room.post_bot(self, self.owner + " is away")


class MeetingBot:
    def __init__(self):
        self.name = "meeting-bot"

    def attach(self, room):
        self.room = room
        room.bus.subscribe("message_received", self._on_message)

    def _on_message(self, message):
        prefix = "/meet "
        if message["text"].startswith(prefix) and message["text"][len(prefix):].strip():
            self.room.bus.emit("meeting_started", {
                "host": message["sender"],
                "topic": message["text"][len(prefix):].strip(),
            })


class TacoBot:
    def __init__(self):
        self.name = "taco-bot"
        self._balances = defaultdict(int)

    def attach(self, room):
        self.room = room
        room.bus.subscribe("message_received", self._on_message)

    def _on_message(self, message):
        parts = message["text"].split()
        if len(parts) == 2 and parts[0] == "/taco":
            self._balances[parts[1]] += 1
            self.room.post_bot(self, "taco recorded for " + parts[1])

    def balance_for(self, recipient):
        return self._balances[recipient]


def _encode_map(values):
    out = bytearray()
    for key in sorted(values):
        key_bytes = key.encode("utf-8")
        value_bytes = values[key].encode("utf-8")
        out.extend(struct.pack(">I", len(key_bytes)))
        out.extend(key_bytes)
        out.extend(struct.pack(">I", len(value_bytes)))
        out.extend(value_bytes)
    return bytes(out)


def _decode_map(blob):
    index = 0
    values = {}
    while index < len(blob):
        if index + 4 > len(blob):
            raise ValueError("truncated key length")
        key_length = struct.unpack(">I", blob[index:index + 4])[0]
        index += 4
        if index + key_length > len(blob):
            raise ValueError("truncated key")
        key = blob[index:index + key_length].decode("utf-8")
        index += key_length
        if index + 4 > len(blob):
            raise ValueError("truncated value length")
        value_length = struct.unpack(">I", blob[index:index + 4])[0]
        index += 4
        if index + value_length > len(blob):
            raise ValueError("truncated value")
        value = blob[index:index + value_length].decode("utf-8")
        index += value_length
        values[key] = value
    return values


class BasicKVStore:
    def __init__(self, files, name="snapshot.bin"):
        self.files = files
        self.name = name
        self.values = {}

    def set(self, key, value):
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("keys and values must be strings")
        self.values[key] = value

    def get(self, key, default=None):
        return self.values.get(key, default)

    def snapshot(self):
        self.files.write(self.name, _encode_map(self.values))

    def restore(self):
        blob = self.files.read(self.name)
        if blob is None:
            return False
        restored = _decode_map(blob)
        self.values = restored
        return True


class ChunkedKVStore(BasicKVStore):
    def __init__(self, files, prefix="kv", chunk_size=1024):
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            raise ValueError("positive chunk size required")
        super().__init__(files)
        self.prefix = prefix
        self.chunk_size = chunk_size
        self._generation = 0

    @property
    def _manifest_name(self):
        return self.prefix + ".manifest"

    def snapshot(self):
        self._generation += 1
        blob = _encode_map(self.values)
        chunks = [blob[index:index + self.chunk_size] for index in range(0, len(blob), self.chunk_size)] or [b""]
        names = []
        for index, chunk in enumerate(chunks):
            name = f"{self.prefix}.{self._generation}.{index}"
            self.files.write(name, chunk)
            names.append(name)
        manifest = json.dumps({"generation": self._generation, "chunks": names}, separators=(",", ":")).encode("utf-8")
        self.files.write(self._manifest_name, manifest)

    def restore(self):
        manifest_blob = self.files.read(self._manifest_name)
        if manifest_blob is None:
            return False
        try:
            manifest = json.loads(manifest_blob.decode("utf-8"))
            generation = manifest["generation"]
            names = manifest["chunks"]
            if not isinstance(generation, int) or not isinstance(names, list) or not names:
                raise ValueError("invalid manifest")
            expected_prefix = f"{self.prefix}.{generation}."
            if any(not isinstance(name, str) or not name.startswith(expected_prefix) for name in names):
                raise ValueError("invalid chunk name")
            parts = []
            for name in names:
                part = self.files.read(name)
                if part is None or len(part) > self.chunk_size:
                    raise ValueError("missing or oversized chunk")
                parts.append(part)
            restored = _decode_map(b"".join(parts))
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            if isinstance(error, ValueError):
                raise
            raise ValueError("invalid chunked snapshot") from error
        self.values = restored
        self._generation = max(self._generation, generation)
        return True


class Job:
    def __init__(self, job_id, dependencies=(), priority=0, retries=0):
        if not isinstance(job_id, str) or not job_id or retries < 0:
            raise ValueError("invalid job")
        self.job_id = job_id
        self.dependencies = tuple(dependencies)
        self.priority = priority
        self.retries = retries


class ConcurrencyLimiter:
    def __init__(self, limit):
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("positive limit required")
        self.limit = limit
        self.active = 0
        self._condition = threading.Condition()

    def acquire(self):
        with self._condition:
            while self.active >= self.limit:
                self._condition.wait()
            self.active += 1

    def release(self):
        with self._condition:
            if not self.active:
                raise RuntimeError("release without an active claim")
            self.active -= 1
            self._condition.notify()


class Scheduler:
    def __init__(self, jobs, limiter, run_attempt):
        jobs = list(jobs)
        self.jobs = {job.job_id: job for job in jobs}
        if len(self.jobs) != len(jobs):
            raise ValueError("duplicate job IDs")
        if any(dependency not in self.jobs for job in self.jobs.values() for dependency in job.dependencies):
            raise ValueError("unknown dependency")
        self.limiter = limiter
        self.run_attempt = run_attempt

    def run(self):
        statuses = {job_id: "pending" for job_id in self.jobs}
        remaining = {job_id: len(job.dependencies) for job_id, job in self.jobs.items()}
        dependents = defaultdict(list)
        for job in self.jobs.values():
            for dependency in job.dependencies:
                dependents[dependency].append(job.job_id)
        ready = []
        for job_id, count in remaining.items():
            if count == 0:
                job = self.jobs[job_id]
                heappush(ready, (-job.priority, job_id))
        condition = threading.Condition()
        running = 0

        def skip_descendants(start):
            queue = deque([start])
            while queue:
                job_id = queue.popleft()
                if statuses[job_id] != "pending":
                    continue
                statuses[job_id] = "skipped"
                queue.extend(dependents[job_id])

        def worker(job):
            nonlocal running
            succeeded = False
            self.limiter.acquire()
            try:
                for attempt in range(job.retries + 1):
                    try:
                        if self.run_attempt(job, attempt):
                            succeeded = True
                            break
                    except Exception:
                        pass
            finally:
                self.limiter.release()
            with condition:
                statuses[job.job_id] = "succeeded" if succeeded else "failed"
                running -= 1
                if succeeded:
                    for child in dependents[job.job_id]:
                        if statuses[child] == "pending":
                            remaining[child] -= 1
                            if remaining[child] == 0:
                                child_job = self.jobs[child]
                                heappush(ready, (-child_job.priority, child))
                else:
                    for child in dependents[job.job_id]:
                        skip_descendants(child)
                condition.notify_all()

        with condition:
            while True:
                while ready:
                    _priority, job_id = heappop(ready)
                    if statuses[job_id] != "pending":
                        continue
                    statuses[job_id] = "running"
                    running += 1
                    threading.Thread(target=worker, args=(self.jobs[job_id],), daemon=True).start()
                if all(status in {"succeeded", "failed", "skipped"} for status in statuses.values()):
                    return statuses
                if running == 0:
                    for job_id, status in list(statuses.items()):
                        if status == "pending":
                            statuses[job_id] = "skipped"
                    return statuses
                condition.wait()


class FrozenClock:
    def __init__(self, initial=0):
        self._value = initial

    def now(self):
        return self._value

    def set(self, value):
        self._value = value


class TimeMap:
    def __init__(self, clock):
        self.clock = clock
        self._values = defaultdict(list)
        self._sequence = 0
        self._lock = threading.RLock()

    def set(self, key, value, timestamp=None):
        with self._lock:
            timestamp = self.clock.now() if timestamp is None else timestamp
            self._sequence += 1
            records = self._values[key]
            bisect.insort_right(records, (timestamp, self._sequence, value))
            return timestamp

    def get(self, key, timestamp=None):
        with self._lock:
            timestamp = self.clock.now() if timestamp is None else timestamp
            records = self._values.get(key, [])
            index = bisect.bisect_right(records, (timestamp, float("inf"), chr(0x10FFFF))) - 1
            return "" if index < 0 else records[index][2]


class MonotonicTimeMap(TimeMap):
    def __init__(self, clock):
        super().__init__(clock)
        self._last_assigned = None

    def set(self, key, value, timestamp=None):
        with self._lock:
            if timestamp is None:
                candidate = self.clock.now()
                timestamp = candidate if self._last_assigned is None else max(candidate, self._last_assigned + 1)
                self._last_assigned = timestamp
            return super().set(key, value, timestamp)


class Message:
    def __init__(self, content, sender, seq, timestamp, causal_deps):
        self.content = content
        self.sender = sender
        self.seq = seq
        self.timestamp = timestamp
        self.causal_deps = list(causal_deps)


class MessageHandler:
    def __init__(self, machine_id, n, topology, mode, request_retransmit=None):
        if mode not in {"at-most-once", "at-least-once", "exactly-once"}:
            raise ValueError("unknown mode")
        if not (0 <= machine_id < n):
            raise ValueError("invalid machine")
        if any(not (0 <= left < n and 0 <= right < n) for left, right in topology):
            raise ValueError("invalid topology")
        self.mode = mode
        self.request_retransmit = request_retransmit or (lambda sender, seq: None)
        self.delivered = []
        self.delivered_ids = set()
        self.requested = set()
        self.next_expected = defaultdict(int)
        self.by_sender = defaultdict(dict)
        self.pending = {}
        self.waiting = defaultdict(set)

    def _id(self, message):
        return (message.sender, message.seq)

    def _request(self, identity):
        if identity not in self.requested:
            self.requested.add(identity)
            self.request_retransmit(*identity)

    def _deliver(self, message):
        identity = self._id(message)
        if identity in self.delivered_ids:
            return
        self.delivered_ids.add(identity)
        self.delivered.append(message)
        for dependent in list(self.waiting.pop(identity, set())):
            pending = self.pending.get(dependent)
            if pending is None:
                continue
            _blocked_message, unresolved = pending
            unresolved.discard(identity)
            if not unresolved:
                blocked = self.pending.pop(dependent)
                self._deliver(blocked[0])

    def receive(self, message):
        identity = self._id(message)
        if identity in self.delivered_ids:
            return
        if self.mode == "at-most-once":
            self._deliver(message)
        elif self.mode == "at-least-once":
            expected = self.next_expected[message.sender]
            if message.seq < expected:
                return
            if message.seq > expected:
                self.by_sender[message.sender].setdefault(message.seq, message)
                for seq in range(expected, message.seq):
                    self._request((message.sender, seq))
                return
            self._deliver(message)
            self.next_expected[message.sender] += 1
            while self.next_expected[message.sender] in self.by_sender[message.sender]:
                next_message = self.by_sender[message.sender].pop(self.next_expected[message.sender])
                self._deliver(next_message)
                self.next_expected[message.sender] += 1
        else:
            if identity in self.pending:
                return
            missing = {dependency for dependency in message.causal_deps if dependency not in self.delivered_ids}
            if not missing:
                self._deliver(message)
                return
            self.pending[identity] = (message, missing)
            for dependency in missing:
                self.waiting[dependency].add(identity)
                self._request(dependency)

    def get_delivered(self):
        return list(self.delivered)
