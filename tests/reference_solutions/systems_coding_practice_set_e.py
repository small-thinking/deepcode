import re
import threading


_CELL_LABEL = re.compile(r"[A-Z]+[1-9]\d*\Z")
_INTEGER = re.compile(r"[+-]?\d+\Z")


def _is_cell_label(value):
    return isinstance(value, str) and _CELL_LABEL.fullmatch(value) is not None


def _parse_content(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value, set()
    if not isinstance(value, str):
        return None
    if _INTEGER.fullmatch(value) is not None:
        return int(value), set()
    if not value.startswith("="):
        return None

    raw_terms = value[1:].split("+")
    if not raw_terms or any(term == "" for term in raw_terms):
        return None

    terms = []
    dependencies = set()
    for term in raw_terms:
        if _INTEGER.fullmatch(term) is not None:
            terms.append(int(term))
        elif _is_cell_label(term):
            terms.append(term)
            dependencies.add(term)
        else:
            return None
    return tuple(terms), dependencies


def _evaluate(definitions, cell, memo):
    if cell in memo:
        return memo[cell]

    definition = definitions.get(cell)
    if definition is None:
        value = 0
    elif isinstance(definition, int):
        value = definition
    else:
        value = 0
        for term in definition:
            value += term if isinstance(term, int) else _evaluate(definitions, term, memo)
    memo[cell] = value
    return value


class Spreadsheet:
    def __init__(self):
        self._values = {}

    def set_cell(self, cell, value):
        self._values[cell] = value

    def get_cell(self, cell):
        return self._values.get(cell, 0)


class EagerSpreadsheet:
    def __init__(self):
        self._definitions = {}
        self._dependencies = {}
        self._dependents = {}
        self._values = {}

    def set_cell(self, cell, value):
        parsed = _parse_content(value)
        if parsed is None:
            raise ValueError("value must be an integer, numeric string, or additive formula")
        definition, dependencies = parsed

        for dependency in self._dependencies.get(cell, set()):
            dependents = self._dependents.get(dependency)
            if dependents is not None:
                dependents.discard(cell)
                if not dependents:
                    del self._dependents[dependency]

        self._definitions[cell] = definition
        if dependencies:
            self._dependencies[cell] = dependencies
            for dependency in dependencies:
                self._dependents.setdefault(dependency, set()).add(cell)
        else:
            self._dependencies.pop(cell, None)

        affected = set()
        pending = [cell]
        while pending:
            current = pending.pop()
            if current in affected:
                continue
            affected.add(current)
            pending.extend(self._dependents.get(current, set()))

        memo = {}
        for current in affected:
            self._values[current] = _evaluate(self._definitions, current, memo)

    def get_cell(self, cell):
        return self._values.get(cell, 0)


class LazySpreadsheet:
    def __init__(self):
        self._definitions = {}

    def set_cell(self, cell, value):
        parsed = _parse_content(value)
        if parsed is None:
            raise ValueError("value must be an integer, numeric string, or additive formula")
        definition, _ = parsed
        self._definitions[cell] = definition

    def get_cell(self, cell):
        return _evaluate(self._definitions, cell, {})


class ValidatedSpreadsheet:
    def __init__(self):
        self._definitions = {}
        self._dependencies = {}
        self._dependents = {}

    def _would_create_cycle(self, target, new_dependencies):
        pending = list(new_dependencies)
        visited = set()
        while pending:
            current = pending.pop()
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)
            pending.extend(self._dependencies.get(current, set()))
        return False

    def set_cell(self, cell, value):
        if not _is_cell_label(cell):
            return False
        parsed = _parse_content(value)
        if parsed is None:
            return False
        definition, dependencies = parsed
        if self._would_create_cycle(cell, dependencies):
            return False

        for dependency in self._dependencies.get(cell, set()):
            dependents = self._dependents.get(dependency)
            if dependents is not None:
                dependents.discard(cell)
                if not dependents:
                    del self._dependents[dependency]

        self._definitions[cell] = definition
        if dependencies:
            self._dependencies[cell] = dependencies
            for dependency in dependencies:
                self._dependents.setdefault(dependency, set()).add(cell)
        else:
            self._dependencies.pop(cell, None)
        return True

    def get_cell(self, cell):
        if not _is_cell_label(cell):
            raise ValueError("invalid cell label")
        return _evaluate(self._definitions, cell, {})


class ConnectionPool:
    def __init__(self, connections):
        self._idle = list(connections)
        seen = set()
        for connection in self._idle:
            identity = id(connection)
            if identity in seen:
                raise ValueError("connection objects must be unique")
            seen.add(identity)
        self._in_use = {}
        self._available = threading.Condition(threading.Lock())

    def acquire(self):
        with self._available:
            while not self._idle:
                self._available.wait()
            connection = self._idle.pop()
            self._in_use[id(connection)] = connection
            return connection

    def release(self, connection):
        with self._available:
            identity = id(connection)
            if self._in_use.get(identity) is not connection:
                raise ValueError("connection is not currently checked out by this pool")
            del self._in_use[identity]
            self._idle.append(connection)
            self._available.notify()
