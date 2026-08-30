from collections import deque
from collections.abc import Sequence
from copy import deepcopy


class SnapshotSet:
    def __init__(self):
        self._versions = [set()]

    @staticmethod
    def _check_hashable(value):
        try:
            hash(value)
        except TypeError as error:
            raise TypeError("value must be hashable") from error

    def add(self, value):
        self._check_hashable(value)
        values = set(self._versions[-1])
        changed = value not in values
        values.add(value)
        self._versions.append(values)
        return changed

    def remove(self, value):
        self._check_hashable(value)
        values = set(self._versions[-1])
        changed = value in values
        values.discard(value)
        self._versions.append(values)
        return changed

    def snapshot(self):
        return len(self._versions) - 1

    def values_at(self, snapshot_id):
        if type(snapshot_id) is not int or not 0 <= snapshot_id < len(self._versions):
            raise IndexError("unknown snapshot")
        return set(self._versions[snapshot_id])


class PrefixCache:
    def __init__(self):
        self._entries = {}

    @staticmethod
    def _tokens(tokens):
        if isinstance(tokens, (str, bytes)) or not isinstance(tokens, Sequence):
            raise TypeError("tokens must be a non-string sequence")
        normalized = tuple(tokens)
        if not normalized:
            raise ValueError("tokens must not be empty")
        if any(type(token) is not int or token < 0 for token in normalized):
            raise TypeError("tokens must be non-negative integers")
        return normalized

    def store(self, tokens, value):
        key = self._tokens(tokens)
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        if not value:
            raise ValueError("value must not be empty")
        self._entries[key] = value

    def lookup(self, tokens):
        query = self._tokens(tokens)
        for size in range(len(query), 0, -1):
            value = self._entries.get(query[:size])
            if value is not None:
                return size, value
        return None

    def remove(self, tokens):
        return self._entries.pop(self._tokens(tokens), None) is not None


class EngineFlightLedger:
    def __init__(self):
        self._events = {}
        self._engine_records = {}
        self._mission_records = {}

    @staticmethod
    def _identifier(value, label):
        if not isinstance(value, str) or not value:
            raise TypeError(f"{label} must be a non-empty string")

    @staticmethod
    def _time(value, label):
        if type(value) is not int:
            raise TypeError(f"{label} must be an integer")

    def record(self, event_id, engine_id, mission_id, start, end):
        self._identifier(event_id, "event_id")
        self._identifier(engine_id, "engine_id")
        self._identifier(mission_id, "mission_id")
        self._time(start, "start")
        self._time(end, "end")
        if end < start:
            raise ValueError("end must be at least start")
        if event_id in self._events:
            return False
        records = self._engine_records.setdefault(engine_id, [])
        if any(start < record["end"] and end > record["start"] for record in records):
            raise ValueError("engine intervals may not overlap")
        record = {"event_id": event_id, "engine_id": engine_id, "mission_id": mission_id, "start": start, "end": end}
        self._events[event_id] = record
        records.append(record)
        self._mission_records.setdefault(mission_id, []).append(record)
        return True

    def engine_flight_time(self, engine_id, start=None, end=None):
        if engine_id not in self._engine_records:
            raise KeyError(engine_id)
        if (start is None) != (end is None):
            raise ValueError("start and end must be supplied together")
        if start is None:
            return sum(record["end"] - record["start"] for record in self._engine_records[engine_id])
        self._time(start, "start")
        self._time(end, "end")
        if end < start:
            raise ValueError("end must be at least start")
        return sum(max(0, min(end, record["end"]) - max(start, record["start"])) for record in self._engine_records[engine_id])

    def mission_flight_time(self, mission_id):
        if mission_id not in self._mission_records:
            raise KeyError(mission_id)
        return sum(record["end"] - record["start"] for record in self._mission_records[mission_id])


class LeasedWorkQueue:
    def __init__(self, max_attempts):
        if type(max_attempts) is not int:
            raise TypeError("max_attempts must be an integer")
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        self._max_attempts = max_attempts
        self._tasks = {}
        self._pending = deque()
        self._dead = []
        self._lease_counter = 0

    @staticmethod
    def _time(value, label):
        if type(value) is not int:
            raise TypeError(f"{label} must be an integer")

    def enqueue(self, task_id, payload):
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")
        if task_id in self._tasks:
            raise ValueError("task already exists")
        self._tasks[task_id] = {"task_id": task_id, "payload": deepcopy(payload), "attempt": 0, "status": "pending", "lease_token": None, "expires_at": None}
        self._pending.append(task_id)

    def reserve(self, now, lease_seconds):
        self._time(now, "now")
        if type(lease_seconds) is not int:
            raise TypeError("lease_seconds must be an integer")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        self.reclaim(now)
        if not self._pending:
            return None
        task = self._tasks[self._pending.popleft()]
        task["attempt"] += 1
        self._lease_counter += 1
        task["status"] = "leased"
        task["lease_token"] = f"lease-{self._lease_counter}"
        task["expires_at"] = now + lease_seconds
        return {key: deepcopy(task[key]) for key in ("task_id", "payload", "lease_token", "attempt")}

    def _current_lease(self, task_id, lease_token):
        task = self._tasks.get(task_id)
        return task if task and task["status"] == "leased" and task["lease_token"] == lease_token else None

    def complete(self, task_id, lease_token):
        task = self._current_lease(task_id, lease_token)
        if task is None:
            return False
        task["status"] = "done"
        task["lease_token"] = None
        task["expires_at"] = None
        return True

    def fail(self, task_id, lease_token, now):
        self._time(now, "now")
        task = self._current_lease(task_id, lease_token)
        if task is None:
            return None
        task["lease_token"] = None
        task["expires_at"] = None
        if task["attempt"] >= self._max_attempts:
            task["status"] = "dead"
            self._dead.append({"task_id": task["task_id"], "payload": deepcopy(task["payload"]), "attempts": task["attempt"]})
            return "dead"
        task["status"] = "pending"
        self._pending.append(task_id)
        return "pending"

    def reclaim(self, now):
        self._time(now, "now")
        expired = sorted((task for task in self._tasks.values() if task["status"] == "leased" and task["expires_at"] <= now), key=lambda task: (task["expires_at"], task["task_id"]))
        for task in expired:
            task["status"] = "pending"
            task["lease_token"] = None
            task["expires_at"] = None
            self._pending.append(task["task_id"])
        return [task["task_id"] for task in expired]

    def dead_letters(self):
        return deepcopy(self._dead)
