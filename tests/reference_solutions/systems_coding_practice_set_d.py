from bisect import bisect_left, bisect_right
from collections import defaultdict, deque
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from functools import cmp_to_key


class Player(Enum):
    X = "X"
    O = "O"


class GameStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    PLAYER_X_WINS = "PLAYER_X_WINS"
    PLAYER_O_WINS = "PLAYER_O_WINS"
    DRAW = "DRAW"


class ConnectKGame:
    def __init__(self, rows, columns, k):
        if any(type(value) is not int or value <= 0 for value in (rows, columns, k)):
            raise ValueError("rows, columns, and k must be positive integers")
        self._rows = rows
        self._columns = columns
        self._k = k
        self._board = [[None for _column in range(columns)] for _row in range(rows)]
        self._heights = [0] * columns
        self.current_player = Player.X
        self.status = GameStatus.IN_PROGRESS

    def make_move(self, player, column):
        if self.status is not GameStatus.IN_PROGRESS:
            raise ValueError("the game is already complete")
        if not isinstance(player, Player) or player is not self.current_player:
            raise ValueError("player is not allowed to move now")
        if type(column) is not int or not 0 <= column < self._columns:
            raise ValueError("column is outside the board")
        row = self._heights[column]
        if row == self._rows:
            raise ValueError("column is full")

        self._board[row][column] = player
        self._heights[column] += 1
        if self._wins_from(row, column, player):
            self.status = (
                GameStatus.PLAYER_X_WINS if player is Player.X else GameStatus.PLAYER_O_WINS
            )
        elif sum(self._heights) == self._rows * self._columns:
            self.status = GameStatus.DRAW
        else:
            self.current_player = Player.O if player is Player.X else Player.X
        return self.status

    def _wins_from(self, row, column, player):
        for row_step, column_step in ((1, 0), (0, 1), (1, 1), (1, -1)):
            total = 1
            for direction in (-1, 1):
                current_row = row + direction * row_step
                current_column = column + direction * column_step
                while (
                    0 <= current_row < self._rows
                    and 0 <= current_column < self._columns
                    and self._board[current_row][current_column] is player
                ):
                    total += 1
                    current_row += direction * row_step
                    current_column += direction * column_step
            if total >= self._k:
                return True
        return False


@dataclass(frozen=True)
class Box:
    id: object
    candies: int
    keys: tuple
    children: tuple


def get_max_candies(boxes, initially_open, key_to_box):
    catalog = {}
    for box in boxes:
        if not isinstance(box, Box) or box.id in catalog:
            raise ValueError("boxes must have unique IDs")
        catalog[box.id] = box
    if not isinstance(key_to_box, Mapping):
        raise ValueError("key_to_box must be a mapping")

    discovered = {box_id for box_id in initially_open if box_id in catalog}
    unlocked = set(discovered)
    opened = set()
    queued = set()
    pending = deque()

    def enqueue_available():
        for box_id in discovered & unlocked:
            if box_id not in opened and box_id not in queued:
                pending.append(box_id)
                queued.add(box_id)

    enqueue_available()
    total = 0
    while pending:
        box_id = pending.popleft()
        queued.remove(box_id)
        if box_id in opened or box_id not in discovered or box_id not in unlocked:
            continue
        box = catalog[box_id]
        opened.add(box_id)
        total += box.candies
        for key in box.keys:
            target = key_to_box.get(key)
            if target in catalog:
                unlocked.add(target)
        for child_id in box.children:
            if child_id in catalog:
                discovered.add(child_id)
        enqueue_available()
    return total


class KeyStore:
    def __init__(self):
        self._values = {}
        self._formulas = {}
        self._dependents = defaultdict(set)

    @staticmethod
    def _require_key(key):
        if not isinstance(key, str) or not key:
            raise TypeError("key must be a nonempty string")

    @staticmethod
    def _require_value(value):
        if type(value) is not int:
            raise TypeError("value must be an integer")

    def set_value(self, key, value):
        self._require_key(key)
        self._require_value(value)
        old_value = self._values.get(key)
        had_value = key in self._values
        old_refs = self._formulas.pop(key, ())
        for ref in old_refs:
            self._dependents[ref].discard(key)
        self._values[key] = value
        if not had_value or old_value != value:
            self._propagate_from(key)

    def set_sum(self, key, refs):
        self._require_key(key)
        if isinstance(refs, (str, bytes)):
            raise TypeError("refs must be an iterable of keys")
        try:
            refs = tuple(refs)
        except TypeError as error:
            raise TypeError("refs must be an iterable of keys") from error
        for ref in refs:
            self._require_key(ref)
            if ref not in self._values:
                raise KeyError(ref)

        candidate = dict(self._formulas)
        candidate[key] = refs
        if self._has_cycle(candidate):
            raise ValueError("formula would create a cycle")

        old_refs = self._formulas.pop(key, ())
        for ref in old_refs:
            self._dependents[ref].discard(key)
        old_value = self._values.get(key)
        had_value = key in self._values
        self._formulas[key] = refs
        for ref in refs:
            self._dependents[ref].add(key)
        self._values[key] = sum(self._values[ref] for ref in refs)
        if not had_value or self._values[key] != old_value:
            self._propagate_from(key)

    def get_value(self, key):
        self._require_key(key)
        if key not in self._values:
            raise KeyError(key)
        return self._values[key]

    @staticmethod
    def _has_cycle(formulas):
        active = set()
        visited = set()

        def visit(key):
            if key in active:
                return True
            if key in visited:
                return False
            active.add(key)
            for ref in formulas.get(key, ()):
                if ref in formulas and visit(ref):
                    return True
            active.remove(key)
            visited.add(key)
            return False

        return any(visit(key) for key in formulas)

    def _propagate_from(self, key):
        pending = deque(self._dependents[key])
        while pending:
            dependent = pending.popleft()
            value = sum(self._values[ref] for ref in self._formulas[dependent])
            if value != self._values[dependent]:
                self._values[dependent] = value
                pending.extend(self._dependents[dependent])


class OverdraftError(Exception):
    pass


@dataclass(frozen=True)
class _Transaction:
    timestamp: int
    amount: int


class Account:
    def __init__(self):
        self._entries = []
        self._times = []
        self._balances = []

    @staticmethod
    def _require_timestamp(timestamp):
        if type(timestamp) is not int:
            raise ValueError("timestamp must be an integer")

    @staticmethod
    def _require_amount(amount):
        if type(amount) is not int or amount <= 0:
            raise ValueError("amount must be a positive integer")

    def _validate_append_timestamp(self, timestamp):
        self._require_timestamp(timestamp)
        if self._times and timestamp < self._times[-1]:
            raise ValueError("timestamps must be nondecreasing")

    def _append(self, timestamp, signed_amount):
        self._entries.append(_Transaction(timestamp, signed_amount))
        self._times.append(timestamp)
        previous = self._balances[-1] if self._balances else 0
        self._balances.append(previous + signed_amount)

    def deposit(self, timestamp, amount):
        self._validate_append_timestamp(timestamp)
        self._require_amount(amount)
        self._append(timestamp, amount)

    def withdraw(self, timestamp, amount):
        self._validate_append_timestamp(timestamp)
        self._require_amount(amount)
        current = self._balances[-1] if self._balances else 0
        if current < amount:
            raise OverdraftError("withdrawal would overdraw the account")
        self._append(timestamp, -amount)

    def transactions(self, start, end):
        self._require_timestamp(start)
        self._require_timestamp(end)
        if start > end:
            raise ValueError("start must not exceed end")
        first = bisect_left(self._times, start)
        last = bisect_right(self._times, end)
        return [(entry.timestamp, entry.amount) for entry in self._entries[first:last]]

    def balance(self, timestamp):
        self._require_timestamp(timestamp)
        index = bisect_right(self._times, timestamp) - 1
        return 0 if index < 0 else self._balances[index]


def _numeric(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            converted = Decimal(str(value))
        except InvalidOperation:
            return None
    elif isinstance(value, str) and value.strip():
        try:
            converted = Decimal(value.strip())
        except InvalidOperation:
            return None
    else:
        return None
    return converted if converted.is_finite() else None


def _compare_values(left, right):
    if left is None or right is None:
        if left is right:
            return 0
        return -1 if left is None else 1
    left_numeric = _numeric(left)
    right_numeric = _numeric(right)
    if left_numeric is not None and right_numeric is not None:
        return (left_numeric > right_numeric) - (left_numeric < right_numeric)
    try:
        return (left > right) - (left < right)
    except TypeError as error:
        raise ValueError("values are not comparable") from error


class _Table:
    def __init__(self, columns):
        self.columns = columns
        self.column_set = set(columns)
        self.rows = []


class Database:
    def __init__(self):
        self._tables = {}

    @staticmethod
    def _require_name(value, label):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} must be a nonempty string")

    @classmethod
    def _names(cls, values, label):
        if isinstance(values, str):
            raise ValueError(f"{label} must be a sequence")
        try:
            names = tuple(values)
        except TypeError as error:
            raise ValueError(f"{label} must be a sequence") from error
        if not names:
            raise ValueError(f"{label} must not be empty")
        for name in names:
            cls._require_name(name, label[:-1] if label.endswith("s") else label)
        if len(set(names)) != len(names):
            raise ValueError(f"{label} must be unique")
        return names

    def create_table(self, table_name, columns):
        self._require_name(table_name, "table name")
        if table_name in self._tables:
            raise ValueError("table already exists")
        self._tables[table_name] = _Table(self._names(columns, "columns"))

    def _table(self, table_name):
        self._require_name(table_name, "table name")
        if table_name not in self._tables:
            raise KeyError(table_name)
        return self._tables[table_name]

    @staticmethod
    def _validate_columns(table, columns, label):
        unknown = [column for column in columns if column not in table.column_set]
        if unknown:
            raise ValueError(f"unknown {label} column")

    def insert(self, table_name, row):
        table = self._table(table_name)
        if not isinstance(row, Mapping) or set(row) != table.column_set:
            raise ValueError("row schema does not match table")
        table.rows.append({column: row[column] for column in table.columns})

    def query(self, table_name, columns, where=None, order_by=None):
        table = self._table(table_name)
        projection = self._names(columns, "projection columns")
        self._validate_columns(table, projection, "projection")
        predicate, conditions = self._where(table, where)
        rows = []
        for stored in table.rows:
            if predicate is not None and not predicate(dict(stored)):
                continue
            if not all(self._matches(stored[column], operator, value) for column, operator, value in conditions):
                continue
            rows.append(dict(stored))
        sort_columns, ascending = self._order_by(table, order_by)
        if sort_columns:
            rows.sort(key=cmp_to_key(lambda left, right: self._row_compare(left, right, sort_columns, ascending)))
        return [{column: row[column] for column in projection} for row in rows]

    def _where(self, table, where):
        if where is None:
            return None, ()
        if callable(where):
            return where, ()
        if isinstance(where, (str, bytes)):
            raise ValueError("where must be a callable or condition list")
        try:
            conditions = tuple(where)
        except TypeError as error:
            raise ValueError("where must be a callable or condition list") from error
        validated = []
        for condition in conditions:
            if not isinstance(condition, (tuple, list)) or len(condition) != 3:
                raise ValueError("condition is invalid")
            column, operator, value = condition
            if column not in table.column_set or operator not in {"=", "!=", "<", "<=", ">", ">="}:
                raise ValueError("condition is invalid")
            validated.append((column, operator, value))
        return None, tuple(validated)

    def _order_by(self, table, order_by):
        if order_by is None:
            return (), True
        if isinstance(order_by, str):
            columns, ascending = (order_by,), True
        elif isinstance(order_by, tuple) and len(order_by) == 2 and type(order_by[1]) is bool:
            columns = self._names(order_by[0], "order columns")
            ascending = order_by[1]
        else:
            raise ValueError("order_by is invalid")
        self._validate_columns(table, columns, "order")
        return columns, ascending

    @staticmethod
    def _matches(left, operator, right):
        comparison = _compare_values(left, right)
        return {
            "=": comparison == 0,
            "!=": comparison != 0,
            "<": comparison < 0,
            "<=": comparison <= 0,
            ">": comparison > 0,
            ">=": comparison >= 0,
        }[operator]

    @staticmethod
    def _row_compare(left, right, columns, ascending):
        for column in columns:
            comparison = _compare_values(left[column], right[column])
            if comparison:
                return comparison if ascending else -comparison
        return 0
