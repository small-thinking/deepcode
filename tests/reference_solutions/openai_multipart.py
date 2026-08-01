from bisect import bisect_right
from collections import Counter, defaultdict, deque
import heapq
import json
import os
from pathlib import Path
import uuid

import numpy as np


# Infection Spread Simulation

HEALTHY, INFECTED, IMMUNE, DEAD, BURNED = range(5)
DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _copy_grid(grid, allowed):
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    copied = [list(row) for row in grid]
    if any(cell not in allowed for row in copied for cell in row):
        raise ValueError("unknown cell state")
    return copied


def _positive(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _infected_neighbors(grid, row, col, directions):
    rows, cols = len(grid), len(grid[0])
    return sum(
        0 <= row + dr < rows
        and 0 <= col + dc < cols
        and grid[row + dr][col + dc] == INFECTED
        for dr, dc in directions
    )


def _static_spread(grid, allowed, infection_threshold, directions):
    _positive("infection_threshold", infection_threshold)
    current = _copy_grid(grid, allowed)
    days = 0
    while True:
        infected = [
            (row, col)
            for row in range(len(current))
            for col in range(len(current[0]))
            if current[row][col] == HEALTHY
            and _infected_neighbors(current, row, col, directions)
            >= infection_threshold
        ]
        if not infected:
            return days, current
        for row, col in infected:
            current[row][col] = INFECTED
        days += 1


def simulate_basic(grid, infection_threshold=1, directions=DIR4):
    return _static_spread(
        grid, {HEALTHY, INFECTED}, infection_threshold, directions
    )


def simulate_with_immunity(grid, infection_threshold=1, directions=DIR4):
    return _static_spread(
        grid, {HEALTHY, INFECTED, IMMUNE}, infection_threshold, directions
    )


def simulate_recovery(
    grid, infectious_days, infection_threshold=1, directions=DIR4
):
    _positive("infectious_days", infectious_days)
    _positive("infection_threshold", infection_threshold)
    current = _copy_grid(grid, {HEALTHY, INFECTED, IMMUNE})
    rows, cols = len(current), len(current[0])
    remaining = [
        [infectious_days if current[r][c] == INFECTED else 0 for c in range(cols)]
        for r in range(rows)
    ]
    days = 0
    while any(INFECTED in row for row in current):
        counts = [
            [_infected_neighbors(current, r, c, directions) for c in range(cols)]
            for r in range(rows)
        ]
        following = [row[:] for row in current]
        next_remaining = [row[:] for row in remaining]
        for r in range(rows):
            for c in range(cols):
                if current[r][c] == HEALTHY and counts[r][c] >= infection_threshold:
                    following[r][c] = INFECTED
                    next_remaining[r][c] = infectious_days
                elif current[r][c] == INFECTED:
                    next_remaining[r][c] -= 1
                    if next_remaining[r][c] == 0:
                        following[r][c] = IMMUNE
        current, remaining = following, next_remaining
        days += 1
    return days, current


def simulate_pending_death(
    grid,
    infectious_days,
    death_threshold,
    infection_threshold=1,
    directions=DIR4,
):
    _positive("infectious_days", infectious_days)
    _positive("death_threshold", death_threshold)
    _positive("infection_threshold", infection_threshold)
    current = _copy_grid(grid, {HEALTHY, INFECTED, IMMUNE, DEAD, BURNED})
    rows, cols = len(current), len(current[0])
    remaining = [
        [infectious_days if current[r][c] == INFECTED else 0 for c in range(cols)]
        for r in range(rows)
    ]
    doomed = [[False] * cols for _ in range(rows)]
    days = 0
    while any(INFECTED in row for row in current):
        counts = [
            [_infected_neighbors(current, r, c, directions) for c in range(cols)]
            for r in range(rows)
        ]
        following = [row[:] for row in current]
        next_remaining = [row[:] for row in remaining]
        next_doomed = [row[:] for row in doomed]
        for r in range(rows):
            for c in range(cols):
                if current[r][c] == INFECTED:
                    if counts[r][c] >= death_threshold:
                        next_doomed[r][c] = True
                    next_remaining[r][c] -= 1
                    if next_remaining[r][c] == 0:
                        following[r][c] = DEAD if next_doomed[r][c] else IMMUNE
                elif current[r][c] == HEALTHY and counts[r][c] >= infection_threshold:
                    following[r][c] = INFECTED
                    next_remaining[r][c] = infectious_days
                    next_doomed[r][c] = counts[r][c] >= death_threshold
        current, remaining, doomed = following, next_remaining, next_doomed
        days += 1
    dead_count = sum(cell == DEAD for row in current for cell in row)
    return days, dead_count, current


def best_initial_burn(
    grid,
    infectious_days,
    death_threshold,
    infection_threshold=1,
    directions=DIR4,
):
    original = _copy_grid(grid, {HEALTHY, INFECTED, IMMUNE})
    rows, cols = len(original), len(original[0])
    best_key = None
    best_result = None
    candidates = [("row", index) for index in range(rows)] + [
        ("col", index) for index in range(cols)
    ]
    for axis, index in candidates:
        burned = [row[:] for row in original]
        if axis == "row":
            burned[index] = [BURNED] * cols
            axis_rank = 0
        else:
            for row in range(rows):
                burned[row][index] = BURNED
            axis_rank = 1
        days, dead_count, final_grid = simulate_pending_death(
            burned,
            infectious_days,
            death_threshold,
            infection_threshold,
            directions,
        )
        key = (dead_count, days, axis_rank, index)
        if best_key is None or key < best_key:
            best_key = key
            best_result = (dead_count, days, axis, index, final_grid)
    return best_result


# Session Tracker


class RecentInteractionTracker:
    def __init__(self, window=15):
        _positive("window", window)
        self.window = window
        self.events = deque()
        self.counts = Counter()
        self.max_ts = None

    def _evict(self, now):
        cutoff = now - self.window + 1
        while self.events and self.events[0][0] < cutoff:
            _, user_id, chat_id = self.events.popleft()
            key = (user_id, chat_id)
            self.counts[key] -= 1
            if self.counts[key] == 0:
                del self.counts[key]

    def process_event(self, user_id, chat_id, timestamp):
        if self.max_ts is not None and timestamp < self.max_ts:
            raise ValueError("timestamps must be non-decreasing")
        self.max_ts = timestamp
        self._evict(timestamp)
        self.events.append((timestamp, user_id, chat_id))
        self.counts[(user_id, chat_id)] += 1

    def get_num_recent_interactions(self, user_id, chat_id):
        return self.counts.get((user_id, chat_id), 0)


class OrderedActiveSessionTracker:
    def __init__(self, window=15):
        _positive("window", window)
        self.window = window
        self.latest_interaction = {}
        self.expirations = []
        self.active_per_user = Counter()
        self.max_ts = None

    def _deactivate(self, key):
        if key not in self.latest_interaction:
            return
        del self.latest_interaction[key]
        user_id, _ = key
        self.active_per_user[user_id] -= 1
        if self.active_per_user[user_id] == 0:
            del self.active_per_user[user_id]

    def _evict(self, now):
        cutoff = now - self.window + 1
        while self.expirations and self.expirations[0][0] < cutoff:
            timestamp, user_id, chat_id = heapq.heappop(self.expirations)
            key = (user_id, chat_id)
            if self.latest_interaction.get(key) == timestamp:
                self._deactivate(key)

    def process_event(self, user_id, chat_id, timestamp, event_type):
        if event_type not in {"interact", "end"}:
            raise ValueError("unknown event type")
        if self.max_ts is not None and timestamp < self.max_ts:
            raise ValueError("timestamps must be non-decreasing")
        self.max_ts = timestamp
        self._evict(timestamp)
        key = (user_id, chat_id)
        if event_type == "end":
            self._deactivate(key)
        else:
            if key not in self.latest_interaction:
                self.active_per_user[user_id] += 1
            self.latest_interaction[key] = timestamp
            heapq.heappush(self.expirations, (timestamp, user_id, chat_id))

    def get_num_active_sessions(self, user_id):
        return self.active_per_user.get(user_id, 0)


class OutOfOrderActiveSessionTracker:
    _PRIORITY = {"interact": 0, "end": 1}

    def __init__(self, window=15, allowed_lateness=2):
        _positive("window", window)
        if (
            isinstance(allowed_lateness, bool)
            or not isinstance(allowed_lateness, int)
            or allowed_lateness < 0
        ):
            raise ValueError("allowed_lateness must be a non-negative integer")
        self.window = window
        self.allowed_lateness = allowed_lateness
        self.max_seen = None
        self.watermark = None
        self.sequence = 0
        self.buffer = []
        self.latest_interaction = {}
        self.expirations = []
        self.active_per_user = Counter()

    def _deactivate(self, key):
        if key not in self.latest_interaction:
            return
        del self.latest_interaction[key]
        user_id, _ = key
        self.active_per_user[user_id] -= 1
        if self.active_per_user[user_id] == 0:
            del self.active_per_user[user_id]

    def _apply(self, timestamp, user_id, chat_id, event_type):
        key = (user_id, chat_id)
        if event_type == "end":
            self._deactivate(key)
        else:
            if key not in self.latest_interaction:
                self.active_per_user[user_id] += 1
            self.latest_interaction[key] = timestamp
            heapq.heappush(self.expirations, (timestamp, user_id, chat_id))

    def _flush(self):
        while self.buffer and self.buffer[0][0] <= self.watermark:
            timestamp, _, _, user_id, chat_id, event_type = heapq.heappop(
                self.buffer
            )
            self._apply(timestamp, user_id, chat_id, event_type)
        cutoff = self.watermark - self.window + 1
        while self.expirations and self.expirations[0][0] < cutoff:
            timestamp, user_id, chat_id = heapq.heappop(self.expirations)
            key = (user_id, chat_id)
            if self.latest_interaction.get(key) == timestamp:
                self._deactivate(key)

    def process_event(self, user_id, chat_id, timestamp, event_type):
        if event_type not in self._PRIORITY:
            raise ValueError("unknown event type")
        if self.watermark is not None and timestamp <= self.watermark:
            return False
        self.max_seen = (
            timestamp if self.max_seen is None else max(self.max_seen, timestamp)
        )
        self.sequence += 1
        heapq.heappush(
            self.buffer,
            (
                timestamp,
                self._PRIORITY[event_type],
                self.sequence,
                user_id,
                chat_id,
                event_type,
            ),
        )
        self.watermark = self.max_seen - self.allowed_lateness
        self._flush()
        return True

    def get_num_active_sessions(self, user_id):
        return self.active_per_user.get(user_id, 0)


# Durable In-Memory Key-Value Store


def _json_record(record):
    try:
        return (
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be JSON serializable") from exc


def _string_key(key):
    if not isinstance(key, str):
        raise ValueError("keys must be strings")


class LogBackedKVStore:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {}
        self._replay()

    def _apply(self, record):
        if not isinstance(record, dict) or not isinstance(record.get("key"), str):
            raise ValueError("invalid log record")
        if record.get("op") == "set" and "value" in record:
            self.data[record["key"]] = record["value"]
        elif record.get("op") == "delete" and set(record) == {"op", "key"}:
            self.data.pop(record["key"], None)
        else:
            raise ValueError("invalid log record")

    def _replay(self):
        try:
            lines = self.path.read_bytes().splitlines(keepends=True)
        except FileNotFoundError:
            return
        for index, raw in enumerate(lines):
            try:
                record = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                if index == len(lines) - 1 and not raw.endswith(b"\n"):
                    break
                raise ValueError("malformed complete log record") from exc
            self._apply(record)

    def _persist(self, record):
        raw = _json_record(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())

    def set(self, key, value):
        _string_key(key)
        record = {"op": "set", "key": key, "value": value}
        _json_record(record)
        self._persist(record)
        self._apply(record)

    def get(self, key, default=None):
        _string_key(key)
        return self.data.get(key, default)

    def delete(self, key):
        _string_key(key)
        record = {"op": "delete", "key": key}
        self._persist(record)
        self._apply(record)


class MultiFileSnapshotKVStore:
    def __init__(self, root, max_file_bytes=1024):
        _positive("max_file_bytes", max_file_bytes)
        self.root = Path(root)
        self.max_file_bytes = max_file_bytes
        self.data = {}

    def set(self, key, value):
        _string_key(key)
        _json_record({"key": key, "value": value})
        self.data[key] = value

    def get(self, key, default=None):
        _string_key(key)
        return self.data.get(key, default)

    def delete(self, key):
        _string_key(key)
        self.data.pop(key, None)

    def _records(self):
        records = []
        for key in sorted(self.data):
            raw = _json_record({"key": key, "value": self.data[key]})
            if len(raw) > self.max_file_bytes:
                raise ValueError("one record exceeds max_file_bytes")
            records.append(raw)
        return records

    def save_snapshot(self):
        records = self._records()
        self.root.mkdir(parents=True, exist_ok=True)
        generation = f"generation-{uuid.uuid4().hex}"
        generation_dir = self.root / generation
        generation_dir.mkdir()
        chunks = [bytearray()]
        for record in records:
            if chunks[-1] and len(chunks[-1]) + len(record) > self.max_file_bytes:
                chunks.append(bytearray())
            chunks[-1].extend(record)
        for index, chunk in enumerate(chunks):
            path = generation_dir / f"part-{index:05d}.jsonl"
            with path.open("wb") as handle:
                handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        temporary = self.root / f"CURRENT-{uuid.uuid4().hex}.tmp"
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(generation + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.root / "CURRENT")
        return generation

    def load_snapshot(self):
        manifest = self.root / "CURRENT"
        if not manifest.exists():
            self.data = {}
            return
        generation = manifest.read_text(encoding="utf-8").strip()
        loaded = {}
        for path in sorted((self.root / generation).glob("*.jsonl")):
            if path.stat().st_size > self.max_file_bytes:
                raise ValueError("snapshot file exceeds max_file_bytes")
            raw_file = path.read_bytes()
            if raw_file and not raw_file.endswith(b"\n"):
                raise ValueError("snapshot record is incomplete")
            for raw in raw_file.splitlines():
                try:
                    record = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError("invalid snapshot record") from exc
                if (
                    not isinstance(record, dict)
                    or set(record) != {"key", "value"}
                    or not isinstance(record["key"], str)
                ):
                    raise ValueError("invalid snapshot record")
                loaded[record["key"]] = record["value"]
        self.data = loaded


# Sharded Matrix Multiplication


def _matmul_inputs(a, b_shards):
    a = np.asarray(a)
    shards = [np.asarray(shard) for shard in b_shards]
    if a.ndim != 2 or not shards:
        raise ValueError("a must be 2-D and b_shards must be non-empty")
    arrays = [a, *shards]
    if any(not np.issubdtype(value.dtype, np.number) for value in arrays):
        raise ValueError("inputs must be numeric")
    if any(
        shard.ndim != 2
        or shard.shape[0] != a.shape[1]
        or shard.shape[1] == 0
        for shard in shards
    ):
        raise ValueError("invalid shard shape")
    return a, shards


def column_sharded_matmul(a, b_shards):
    a, shards = _matmul_inputs(a, b_shards)
    return np.concatenate([a @ shard for shard in shards], axis=1)


def column_sharded_matmul_with_grads(a, b_shards, dy):
    a, shards = _matmul_inputs(a, b_shards)
    y = np.concatenate([a @ shard for shard in shards], axis=1)
    dy = np.asarray(dy)
    if not np.issubdtype(dy.dtype, np.number) or dy.shape != y.shape:
        raise ValueError("dy must be numeric and have the same shape as y")
    widths = [shard.shape[1] for shard in shards]
    dy_shards = np.split(dy, np.cumsum(widths)[:-1], axis=1)
    gradient_dtype = np.result_type(a, dy, *shards)
    da = np.zeros(a.shape, dtype=gradient_dtype)
    for dy_shard, shard in zip(dy_shards, shards):
        da += dy_shard @ shard.T
    db_shards = [a.T @ dy_shard for dy_shard in dy_shards]
    return y, da, db_shards


# Versioned Social Graph


class VersionedSocialGraph:
    def __init__(self):
        self._version = 0
        self._history = defaultdict(lambda: [[], []])
        self._current_edges = set()
        self._ever_out = defaultdict(set)
        self._ever_in = defaultdict(set)

    @staticmethod
    def _user(user):
        if not isinstance(user, str):
            raise ValueError("user IDs must be strings")

    def _edge(self, follower, followee):
        self._user(follower)
        self._user(followee)

    def _snapshot_version(self, snapshot_id):
        if snapshot_id is None:
            return self._version
        if (
            isinstance(snapshot_id, bool)
            or not isinstance(snapshot_id, int)
            or snapshot_id < 0
            or snapshot_id > self._version
        ):
            raise ValueError("invalid snapshot ID")
        return snapshot_id

    def _is_following_at(self, follower, followee, version):
        versions, states = self._history.get((follower, followee), ((), ()))
        index = bisect_right(versions, version) - 1
        return index >= 0 and states[index]

    def follow(self, follower, followee):
        self._edge(follower, followee)
        if follower == followee:
            raise ValueError("self-follow is not allowed")
        edge = (follower, followee)
        if edge in self._current_edges:
            return False
        self._version += 1
        self._history[edge][0].append(self._version)
        self._history[edge][1].append(True)
        self._current_edges.add(edge)
        self._ever_out[follower].add(followee)
        self._ever_in[followee].add(follower)
        return True

    def unfollow(self, follower, followee):
        self._edge(follower, followee)
        if follower == followee:
            raise ValueError("self-follow is not allowed")
        edge = (follower, followee)
        if edge not in self._current_edges:
            return False
        self._version += 1
        self._history[edge][0].append(self._version)
        self._history[edge][1].append(False)
        self._current_edges.remove(edge)
        return True

    def snapshot(self):
        return self._version

    def is_following(self, follower, followee, snapshot_id=None):
        self._edge(follower, followee)
        return self._is_following_at(
            follower, followee, self._snapshot_version(snapshot_id)
        )

    def get_followees(self, user, snapshot_id=None):
        self._user(user)
        version = self._snapshot_version(snapshot_id)
        return sorted(
            followee
            for followee in self._ever_out.get(user, ())
            if self._is_following_at(user, followee, version)
        )

    def get_followers(self, user, snapshot_id=None):
        self._user(user)
        version = self._snapshot_version(snapshot_id)
        return sorted(
            follower
            for follower in self._ever_in.get(user, ())
            if self._is_following_at(follower, user, version)
        )

    def recommend(self, user, k, snapshot_id=None):
        self._user(user)
        if isinstance(k, bool) or not isinstance(k, int) or k < 0:
            raise ValueError("k must be a non-negative integer")
        version = self._snapshot_version(snapshot_id)
        if k == 0:
            return []
        direct = set(self.get_followees(user, version))
        scores = Counter()
        for middle in direct:
            for candidate in self.get_followees(middle, version):
                if candidate != user and candidate not in direct:
                    scores[candidate] += 1
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return ranked[:k]
