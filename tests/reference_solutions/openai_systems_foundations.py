import copy
import re
import threading
from collections import deque


_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_GENERIC = re.compile(r"[A-Z][0-9]*")


def parse_type(text):
    if not isinstance(text, str):
        raise ValueError("type text must be a string")
    index = 0

    def skip_space():
        nonlocal index
        while index < len(text) and text[index].isspace():
            index += 1

    def parse_node():
        nonlocal index
        skip_space()
        if index >= len(text):
            raise ValueError("missing type")
        if text[index] in "([":
            closing = ")" if text[index] == "(" else "]"
            index += 1
            skip_space()
            values = []
            if index < len(text) and text[index] == closing:
                index += 1
                return tuple(values)
            while True:
                values.append(parse_node())
                skip_space()
                if index >= len(text):
                    raise ValueError("unclosed tuple")
                if text[index] == closing:
                    index += 1
                    return tuple(values)
                if text[index] != ",":
                    raise ValueError("expected comma")
                index += 1
                skip_space()
                if index < len(text) and text[index] == closing:
                    index += 1
                    return tuple(values)
        match = _NAME.match(text, index)
        if not match:
            raise ValueError("invalid atomic type")
        index = match.end()
        return match.group(0)

    node = parse_node()
    skip_space()
    if index != len(text):
        raise ValueError("trailing type text")
    return node


def format_type(node):
    if isinstance(node, str):
        if not _NAME.fullmatch(node):
            raise ValueError("invalid atomic type")
        return node
    if isinstance(node, tuple):
        return "(" + ",".join(format_type(child) for child in node) + ")"
    raise ValueError("invalid type node")


def infer_return_type(actual_params, parameter_patterns, return_pattern):
    if not isinstance(actual_params, (list, tuple)) or not isinstance(parameter_patterns, (list, tuple)):
        raise ValueError("parameter lists required")
    if len(actual_params) != len(parameter_patterns):
        raise ValueError("arity mismatch")
    bindings = {}

    def valid(node):
        if isinstance(node, str):
            return bool(_NAME.fullmatch(node))
        return isinstance(node, tuple) and all(valid(child) for child in node)

    def unify(actual, pattern):
        if not valid(actual) or not valid(pattern):
            raise ValueError("invalid type node")
        if isinstance(pattern, str) and _GENERIC.fullmatch(pattern):
            if pattern in bindings and bindings[pattern] != actual:
                raise ValueError("conflicting generic binding")
            bindings.setdefault(pattern, copy.deepcopy(actual))
            return
        if isinstance(actual, tuple) != isinstance(pattern, tuple):
            raise ValueError("structure mismatch")
        if isinstance(actual, tuple):
            if len(actual) != len(pattern):
                raise ValueError("tuple length mismatch")
            for actual_child, pattern_child in zip(actual, pattern):
                unify(actual_child, pattern_child)
        elif actual != pattern:
            raise ValueError("atomic type mismatch")

    def substitute(node):
        if not valid(node):
            raise ValueError("invalid type node")
        if isinstance(node, str):
            if _GENERIC.fullmatch(node):
                if node not in bindings:
                    raise ValueError("unbound return generic")
                return copy.deepcopy(bindings[node])
            return node
        return tuple(substitute(child) for child in node)

    for actual, pattern in zip(actual_params, parameter_patterns):
        unify(actual, pattern)
    return substitute(return_pattern)


class ResumableIterator:
    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    def set_state(self, state):
        raise NotImplementedError


class MultiDimensionalIterator(ResumableIterator):
    def __init__(self, items):
        if not isinstance(items, (list, tuple)):
            raise ValueError("root must be a sequence")
        self._items = copy.deepcopy(items)
        if self._max_depth(self._items) > 3:
            raise ValueError("at most three dimensions")
        self._shape = self._build_shape(self._items)
        self._leaves = []
        self._collect(self._items, [])
        self._index = 0

    def _max_depth(self, value):
        if not isinstance(value, (list, tuple)):
            return 0
        if not value:
            return 1
        return 1 + max(self._max_depth(child) for child in value)

    def _build_shape(self, value):
        if not isinstance(value, (list, tuple)):
            return "leaf"
        return [self._build_shape(child) for child in value]

    def _collect(self, value, path):
        if isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                self._collect(child, path + [index])
        else:
            self._leaves.append((path, value))

    def next(self):
        if self._index >= len(self._leaves):
            raise StopIteration
        value = self._leaves[self._index][1]
        self._index += 1
        return copy.deepcopy(value)

    def get_state(self):
        path = None if self._index >= len(self._leaves) else list(self._leaves[self._index][0])
        return {"version": 1, "shape": copy.deepcopy(self._shape), "next_path": path}

    def set_state(self, state):
        if not isinstance(state, dict) or set(state) != {"version", "shape", "next_path"}:
            raise ValueError("invalid iterator state")
        if state["version"] != 1 or state["shape"] != self._shape:
            raise ValueError("incompatible iterator state")
        path = state["next_path"]
        if path is None:
            self._index = len(self._leaves)
            return
        if not isinstance(path, list) or any(not isinstance(part, int) or part < 0 for part in path):
            raise ValueError("invalid next path")
        for index, (candidate, _value) in enumerate(self._leaves):
            if candidate == path:
                self._index = index
                return
        raise ValueError("unknown next path")


class ModalLock:
    def __init__(self):
        self._condition = threading.Condition()
        self._active = {}

    def acquire(self, mode):
        with self._condition:
            while self._active and mode not in self._active:
                self._condition.wait()
            self._active[mode] = self._active.get(mode, 0) + 1

    def release(self, mode):
        with self._condition:
            count = self._active.get(mode, 0)
            if not count:
                raise RuntimeError("mode is not active")
            if count == 1:
                del self._active[mode]
            else:
                self._active[mode] = count - 1
            self._condition.notify_all()


class FairModalLock:
    def __init__(self):
        self._condition = threading.Condition()
        self._active = {}
        self._waiting = deque()

    def _can_acquire(self, ticket, mode):
        waiting = list(self._waiting)
        index = next(index for index, (candidate, _mode) in enumerate(waiting) if candidate is ticket)
        if self._active and mode not in self._active:
            return False
        if any(waiting[before][1] != mode for before in range(index)):
            return False
        return bool(self._active) or waiting[0][1] == mode

    def acquire(self, mode):
        ticket = object()
        with self._condition:
            self._waiting.append((ticket, mode))
            while not self._can_acquire(ticket, mode):
                self._condition.wait()
            for index, (candidate, _candidate_mode) in enumerate(self._waiting):
                if candidate is ticket:
                    del self._waiting[index]
                    break
            self._active[mode] = self._active.get(mode, 0) + 1
            self._condition.notify_all()

    def release(self, mode):
        with self._condition:
            count = self._active.get(mode, 0)
            if not count:
                raise RuntimeError("mode is not active")
            if count == 1:
                del self._active[mode]
            else:
                self._active[mode] = count - 1
            self._condition.notify_all()
