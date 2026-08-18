from collections.abc import Mapping
from dataclasses import dataclass
import csv
import io


class PrefixTrie:
    def __init__(self, words=()):
        self._root = {}
        for word in words:
            self.insert(word)

    @staticmethod
    def _require_word(word):
        if not isinstance(word, str) or not word:
            raise TypeError("word must be a nonempty string")

    def insert(self, word):
        self._require_word(word)
        node = self._root
        for character in word:
            node = node.setdefault(character, {})
        node[None] = True

    def contains(self, word):
        self._require_word(word)
        node = self._root
        for character in word:
            if character not in node:
                return False
            node = node[character]
        return None in node

    def complete(self, prefix):
        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string")
        node = self._root
        for character in prefix:
            if character not in node:
                return []
            node = node[character]

        results = []

        def visit(current, suffix):
            if None in current:
                results.append(prefix + suffix)
            for character in sorted(key for key in current if key is not None):
                visit(current[character], suffix + character)

        visit(node, "")
        return results


@dataclass(frozen=True)
class ShotResult:
    outcome: str
    ship_id: str | None
    game_over: bool


@dataclass(frozen=True)
class BattleshipState:
    size: int
    fleet: tuple
    shots: frozenset

    @property
    def is_complete(self):
        all_cells = {cell for _ship_id, cells in self.fleet for cell in cells}
        return all_cells <= self.shots


def _point(row, column, size=None):
    if type(row) is not int or type(column) is not int:
        raise ValueError("coordinates must be integers")
    point = (row, column)
    if size is not None and not (0 <= row < size and 0 <= column < size):
        raise ValueError("coordinate is outside the board")
    return point


def _normalized_ship_cells(cells, size):
    try:
        normalized = tuple(_point(row, column, size) for row, column in cells)
    except (TypeError, ValueError):
        raise ValueError("invalid ship cells") from None
    if not normalized or len(set(normalized)) != len(normalized):
        raise ValueError("ship cells must be nonempty and unique")

    rows = {row for row, _column in normalized}
    columns = {column for _row, column in normalized}
    if len(rows) == 1:
        ordered = sorted(column for _row, column in normalized)
    elif len(columns) == 1:
        ordered = sorted(row for row, _column in normalized)
    else:
        raise ValueError("ships must be straight")
    if ordered != list(range(ordered[0], ordered[-1] + 1)):
        raise ValueError("ships must be contiguous")
    return tuple(sorted(normalized))


def create_game(size, ships):
    if type(size) is not int or size <= 0 or not isinstance(ships, Mapping) or not ships:
        raise ValueError("invalid board or fleet")
    fleet = []
    occupied = set()
    for ship_id, cells in ships.items():
        if not isinstance(ship_id, str) or not ship_id:
            raise ValueError("ship ID must be a nonempty string")
        normalized = _normalized_ship_cells(cells, size)
        if occupied.intersection(normalized):
            raise ValueError("ships may not overlap")
        occupied.update(normalized)
        fleet.append((ship_id, normalized))
    return BattleshipState(size=size, fleet=tuple(sorted(fleet)), shots=frozenset())


def fire(state, row, column):
    if not isinstance(state, BattleshipState):
        raise ValueError("state must be a BattleshipState")
    point = _point(row, column, state.size)
    if point in state.shots:
        return state, ShotResult("repeat", None, state.is_complete)

    next_state = BattleshipState(state.size, state.fleet, state.shots | frozenset({point}))
    for ship_id, cells in state.fleet:
        if point in cells:
            sunk = set(cells) <= next_state.shots
            return next_state, ShotResult("sunk" if sunk else "hit", ship_id, next_state.is_complete)
    return next_state, ShotResult("miss", None, next_state.is_complete)


def _validated_events(events, horizon):
    try:
        values = tuple(events)
    except TypeError:
        raise ValueError("events must be iterable") from None
    previous = None
    for event in values:
        if not isinstance(event, (tuple, list)) or len(event) != 2:
            raise ValueError("events must be timestamp-active tuples")
        timestamp, active = event
        if type(timestamp) is not int or not isinstance(active, bool):
            raise ValueError("invalid event fields")
        if not 0 <= timestamp < horizon or (previous is not None and timestamp <= previous):
            raise ValueError("invalid event timestamp")
        previous = timestamp
    return values


def active_overlap_intervals(left_events, right_events, horizon):
    if type(horizon) is not int or horizon <= 0:
        raise ValueError("horizon must be a positive integer")
    left = _validated_events(left_events, horizon)
    right = _validated_events(right_events, horizon)
    left_index = right_index = 0
    left_active = right_active = False
    started_at = None
    intervals = []

    while left_index < len(left) or right_index < len(right):
        candidates = []
        if left_index < len(left):
            candidates.append(left[left_index][0])
        if right_index < len(right):
            candidates.append(right[right_index][0])
        timestamp = min(candidates)
        was_active = left_active and right_active
        if left_index < len(left) and left[left_index][0] == timestamp:
            left_active = left[left_index][1]
            left_index += 1
        if right_index < len(right) and right[right_index][0] == timestamp:
            right_active = right[right_index][1]
            right_index += 1
        now_active = left_active and right_active
        if not was_active and now_active:
            started_at = timestamp
        elif was_active and not now_active:
            intervals.append((started_at, timestamp))
            started_at = None

    if left_active and right_active:
        intervals.append((started_at, horizon))
    return intervals


def parse_csv_records(text, required_columns=(), converters=None):
    if not isinstance(text, str) or isinstance(required_columns, str):
        raise ValueError("text and required columns are invalid")
    try:
        required = tuple(required_columns)
    except TypeError:
        raise ValueError("required_columns must be iterable") from None
    if any(not isinstance(column, str) or not column for column in required):
        raise ValueError("invalid required column")
    if len(set(required)) != len(required):
        raise ValueError("duplicate required column")

    if converters is None:
        converters = {}
    if not isinstance(converters, Mapping) or any(
        not isinstance(column, str) or not callable(converter)
        for column, converter in converters.items()
    ):
        raise ValueError("invalid converters")

    try:
        reader = csv.reader(io.StringIO(text, newline=""))
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("CSV must include a header") from None
        if not header or any(not column for column in header) or len(set(header)) != len(header):
            raise ValueError("invalid header")
        if any(column not in header for column in required):
            raise ValueError("required column is missing")
        if any(column not in header for column in converters):
            raise ValueError("converter column is missing")

        records = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError("row width does not match header")
            record = dict(zip(header, row))
            for column, converter in converters.items():
                try:
                    record[column] = converter(record[column])
                except Exception as error:
                    raise ValueError(f"converter failed for {column}") from error
            records.append(record)
        return records
    except csv.Error as error:
        raise ValueError("invalid CSV") from error
