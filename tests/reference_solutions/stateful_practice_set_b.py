from datetime import date
from enum import Enum
from threading import RLock
import re


class BillingStatus:
    def __init__(self, monetary_columns):
        self.columns = tuple(monetary_columns)
        self.amounts = {column: 0 for column in self.columns}
        self._applied = []
        self._undone = []

    def apply_regular(self, row):
        self._undone.clear()
        overwrite = row.get("overwrite") is True
        changes = {}
        for column in self.columns:
            if column not in row:
                continue
            before = self.amounts[column]
            after = row[column] if overwrite else before + row[column]
            changes[column] = (before, after)
        if not changes:
            return
        for column, (_before, after) in changes.items():
            self.amounts[column] = after
        self._applied.append(changes)

    def undo_last(self):
        if not self._applied:
            return
        changes = self._applied.pop()
        for column, (before, _after) in changes.items():
            self.amounts[column] = before
        self._undone.append(changes)

    def redo_last(self):
        if not self._undone:
            return
        changes = self._undone.pop()
        for column, (_before, after) in changes.items():
            self.amounts[column] = after
        self._applied.append(changes)

    def as_dict(self):
        return dict(self.amounts)


def replay_billing_transactions(monetary_columns, transactions):
    statuses = {}
    for _transaction_id, row in sorted(
        transactions.items(), key=lambda item: (item[1]["timestamp"], item[0])
    ):
        status = statuses.setdefault(row["user_id"], BillingStatus(monetary_columns))
        if row.get("undo_last") is True:
            status.undo_last()
        elif row.get("redo_last") is True:
            status.redo_last()
        else:
            status.apply_regular(row)
    return {user_id: status.as_dict() for user_id, status in statuses.items()}


_KEY_PATTERN = re.compile(rb"[A-Za-z0-9_-]+")


def _valid_key(key):
    return _KEY_PATTERN.fullmatch(key) is not None


def process_protocol(data):
    if not isinstance(data, bytes):
        raise ValueError("data must be bytes")
    store = {}
    output = []
    index = 0
    while index < len(data):
        line_end = data.find(b"\n", index)
        if line_end < 0:
            raise ValueError("unterminated command header")
        header = data[index:line_end]
        index = line_end + 1
        parts = header.split(b" ")
        if not parts or any(not part for part in parts):
            raise ValueError("malformed command header")
        command = parts[0]
        if command == b"set":
            if len(parts) != 3 or not _valid_key(parts[1]) or not parts[2].isdigit():
                raise ValueError("invalid set command")
            size = int(parts[2])
            if index + size >= len(data) or data[index + size:index + size + 1] != b"\n":
                raise ValueError("incomplete payload frame")
            store[parts[1]] = data[index:index + size]
            index += size + 1
            output.append(b"STORED\n")
        elif command == b"get":
            if len(parts) < 2 or any(not _valid_key(key) for key in parts[1:]):
                raise ValueError("invalid get command")
            for key in parts[1:]:
                if key in store:
                    value = store[key]
                    output.extend((b"VALUE " + key + b" " + str(len(value)).encode("ascii") + b"\n", value, b"\n"))
            output.append(b"END\n")
        else:
            raise ValueError("unknown command")
    return b"".join(output)


def _validated_players(players):
    result = tuple(players)
    if len(result) != 2 or result[0] == result[1]:
        raise ValueError("exactly two distinct players are required")
    return result


class Game:
    def __init__(self, players=("A", "B")):
        self.players = _validated_players(players)
        self.points = {player: 0 for player in self.players}

    @property
    def complete(self):
        first, second = (self.points[player] for player in self.players)
        return max(first, second) >= 4 and abs(first - second) >= 2

    @property
    def winner(self):
        if not self.complete:
            return None
        return max(self.players, key=lambda player: self.points[player])

    def record_point(self, player):
        if player not in self.points:
            raise ValueError("unknown player")
        if self.complete:
            raise RuntimeError("game is complete")
        self.points[player] += 1

    def displayed_score(self):
        first, second = (self.points[player] for player in self.players)
        if self.complete:
            return f"game {self.winner}"
        if first >= 3 and second >= 3:
            if first == second:
                return "deuce"
            return f"advantage {self.players[0] if first > second else self.players[1]}"
        labels = ("0", "15", "30", "40")
        return f"{labels[first]}-{labels[second]}"

    def state(self):
        return {
            "type": "game",
            "points": dict(self.points),
            "score": self.displayed_score(),
            "complete": self.complete,
            "winner": self.winner,
        }


class TiebreakGame(Game):
    @property
    def complete(self):
        first, second = (self.points[player] for player in self.players)
        return max(first, second) >= 7 and abs(first - second) >= 2

    def displayed_score(self):
        return f"{self.points[self.players[0]]}-{self.points[self.players[1]]}"

    def state(self):
        result = super().state()
        result["type"] = "tiebreak"
        return result


class TennisSet:
    def __init__(self, players=("A", "B")):
        self.players = _validated_players(players)
        self.games = []
        self.games_won = {player: 0 for player in self.players}
        self.current_game = Game(self.players)
        self._winner = None

    @property
    def complete(self):
        return self._winner is not None

    @property
    def winner(self):
        return self._winner

    def record_point(self, player):
        if self.complete:
            raise RuntimeError("set is complete")
        self.current_game.record_point(player)
        if not self.current_game.complete:
            return

        finished_game = self.current_game
        self.games.append(finished_game)
        self.games_won[finished_game.winner] += 1
        if isinstance(finished_game, TiebreakGame):
            self._winner = finished_game.winner
            return

        first, second = (self.games_won[player] for player in self.players)
        if max(first, second) >= 6 and abs(first - second) >= 2:
            self._winner = self.players[0] if first > second else self.players[1]
        elif first == second == 6:
            self.current_game = TiebreakGame(self.players)
        else:
            self.current_game = Game(self.players)

    def state(self):
        return {
            "games": dict(self.games_won),
            "complete": self.complete,
            "winner": self.winner,
            "current_game": self.current_game.state(),
        }


class Match:
    def __init__(self, players=("A", "B"), best_of=3):
        self.players = _validated_players(players)
        if not isinstance(best_of, int) or best_of <= 0 or best_of % 2 == 0:
            raise ValueError("best_of must be a positive odd integer")
        self.best_of = best_of
        self.sets_won = {player: 0 for player in self.players}
        self.sets = [TennisSet(self.players)]
        self._winner = None

    @property
    def current_set(self):
        return self.sets[-1]

    @property
    def complete(self):
        return self._winner is not None

    @property
    def winner(self):
        return self._winner

    def record_point(self, player):
        if self.complete:
            raise RuntimeError("match is complete")
        self.current_set.record_point(player)
        if not self.current_set.complete:
            return
        winner = self.current_set.winner
        self.sets_won[winner] += 1
        if self.sets_won[winner] == self.best_of // 2 + 1:
            self._winner = winner
        else:
            self.sets.append(TennisSet(self.players))

    def state(self):
        return {
            "sets": dict(self.sets_won),
            "complete": self.complete,
            "winner": self.winner,
            "current_set": self.current_set.state(),
        }


class PaymentStatus(Enum):
    UNPAID = "unpaid"
    PAID = "paid"


class BillStatusTracker:
    def __init__(self):
        self._bills = {}
        self._lock = RLock()

    @staticmethod
    def _validate_bill(bill_id, amount_cents, due_date):
        if not isinstance(bill_id, str) or not bill_id:
            raise ValueError("bill_id must be a nonempty string")
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 0:
            raise ValueError("amount_cents must be a non-negative integer")
        if not isinstance(due_date, date):
            raise ValueError("due_date must be a date")

    def add_bill(self, bill_id, amount_cents, due_date):
        self._validate_bill(bill_id, amount_cents, due_date)
        with self._lock:
            if bill_id in self._bills:
                raise ValueError("duplicate bill_id")
            self._bills[bill_id] = {
                "bill_id": bill_id,
                "amount_cents": amount_cents,
                "due_date": due_date,
                "status": PaymentStatus.UNPAID,
            }

    def update_payment_status(self, bill_id, status):
        if not isinstance(status, PaymentStatus):
            raise ValueError("status must be a PaymentStatus")
        with self._lock:
            if bill_id not in self._bills:
                raise KeyError(bill_id)
            self._bills[bill_id] = {**self._bills[bill_id], "status": status}

    def get_unpaid_bills(self):
        with self._lock:
            snapshot = [dict(bill) for bill in self._bills.values() if bill["status"] == PaymentStatus.UNPAID]
        return sorted(snapshot, key=lambda bill: (bill["due_date"], bill["bill_id"]))
