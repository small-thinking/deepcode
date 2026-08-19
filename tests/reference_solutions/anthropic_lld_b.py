import copy
import math


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value)


def _is_nonnegative_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_positive_int(value):
    return _is_nonnegative_int(value) and value > 0


class InsufficientFundsError(Exception):
    pass


class BankLedger:
    def __init__(self):
        self._balances = {}
        self._entries = {}
        self._next_entry = 1

    def _account(self, account_id):
        if not _is_nonempty_string(account_id):
            raise ValueError("invalid account")
        if account_id not in self._balances:
            raise KeyError(account_id)

    def _mutation(self, account_id, amount, memo, entry_type):
        self._account(account_id)
        if not _is_positive_int(amount) or not isinstance(memo, str):
            raise ValueError("invalid entry")
        if entry_type == "withdraw" and self._balances[account_id] < amount:
            raise InsufficientFundsError(account_id)
        if entry_type == "deposit":
            self._balances[account_id] += amount
        else:
            self._balances[account_id] -= amount
        entry_id = f"entry-{self._next_entry}"
        self._next_entry += 1
        self._entries[account_id].append(
            {
                "id": entry_id,
                "type": entry_type,
                "amount": amount,
                "balance_after": self._balances[account_id],
                "memo": memo,
            }
        )
        return entry_id

    def open_account(self, account_id, opening_balance=0):
        if not _is_nonempty_string(account_id) or not _is_nonnegative_int(opening_balance):
            raise ValueError("invalid account")
        if account_id in self._balances:
            raise ValueError("duplicate account")
        self._balances[account_id] = opening_balance
        self._entries[account_id] = []

    def deposit(self, account_id, amount, memo=""):
        return self._mutation(account_id, amount, memo, "deposit")

    def withdraw(self, account_id, amount, memo=""):
        return self._mutation(account_id, amount, memo, "withdraw")

    def balance(self, account_id):
        self._account(account_id)
        return self._balances[account_id]

    def statement(self, account_id):
        self._account(account_id)
        return copy.deepcopy(self._entries[account_id])


class VersionConflictError(Exception):
    pass


def _is_scalar(value):
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _validate_fields(fields, allow_empty=False):
    if not isinstance(fields, dict) or (not allow_empty and not fields):
        raise ValueError("invalid fields")
    for key, value in fields.items():
        if not _is_nonempty_string(key) or not _is_scalar(value):
            raise ValueError("invalid field")


class VersionedRecordDatabase:
    def __init__(self):
        self._records = {}

    def _record(self, record_id):
        if not _is_nonempty_string(record_id):
            raise ValueError("invalid record id")
        if record_id not in self._records:
            raise KeyError(record_id)
        return self._records[record_id]

    def _expected_version(self, expected_version):
        if not _is_positive_int(expected_version):
            raise ValueError("invalid expected version")

    def _view(self, record_id, record):
        return {"id": record_id, "version": record["version"], "fields": dict(record["fields"])}

    def insert(self, record_id, fields):
        if not _is_nonempty_string(record_id):
            raise ValueError("invalid record id")
        _validate_fields(fields)
        if record_id in self._records:
            raise ValueError("duplicate record")
        self._records[record_id] = {"version": 1, "fields": dict(fields)}

    def get(self, record_id):
        return self._view(record_id, self._record(record_id))

    def patch(self, record_id, expected_version, changes, remove=()):
        record = self._record(record_id)
        self._expected_version(expected_version)
        _validate_fields(changes, allow_empty=True)
        if isinstance(remove, str) or not isinstance(remove, (list, tuple)):
            raise ValueError("invalid removal list")
        if not changes and not remove:
            raise ValueError("empty patch")
        if any(not _is_nonempty_string(field) for field in remove) or len(set(remove)) != len(remove):
            raise ValueError("invalid removal field")
        if set(changes).intersection(remove):
            raise ValueError("overlapping patch")
        if record["version"] != expected_version:
            raise VersionConflictError(record_id)
        if any(field not in record["fields"] for field in remove):
            raise KeyError("missing field")
        next_fields = dict(record["fields"])
        next_fields.update(changes)
        for field in remove:
            del next_fields[field]
        record["fields"] = next_fields
        record["version"] += 1
        return record["version"]

    def find(self, field, value):
        if not _is_nonempty_string(field) or not _is_scalar(value):
            raise ValueError("invalid query")
        rows = []
        for record_id in sorted(self._records):
            record = self._records[record_id]
            if record["fields"].get(field) == value and field in record["fields"]:
                rows.append(self._view(record_id, record))
        return rows

    def delete(self, record_id, expected_version):
        record = self._record(record_id)
        self._expected_version(expected_version)
        if record["version"] != expected_version:
            raise VersionConflictError(record_id)
        del self._records[record_id]


class _Node:
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class ManualLRUCache:
    def __init__(self, capacity):
        if not _is_positive_int(capacity):
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._nodes = {}
        self._head = _Node()
        self._tail = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    def _check_key(self, key):
        hash(key)

    def _detach(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _insert_mru(self, node):
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node

    def _promote(self, node):
        self._detach(node)
        self._insert_mru(node)

    def get(self, key, default=None):
        self._check_key(key)
        node = self._nodes.get(key)
        if node is None:
            return default
        self._promote(node)
        return node.value

    def put(self, key, value):
        self._check_key(key)
        node = self._nodes.get(key)
        if node is not None:
            node.value = value
            self._promote(node)
            return None
        node = _Node(key, value)
        self._nodes[key] = node
        self._insert_mru(node)
        if len(self._nodes) <= self._capacity:
            return None
        lru = self._tail.prev
        self._detach(lru)
        del self._nodes[lru.key]
        return (lru.key, lru.value)

    def remove(self, key):
        self._check_key(key)
        node = self._nodes.pop(key, None)
        if node is None:
            return False
        self._detach(node)
        return True

    def keys_mru_to_lru(self):
        keys = []
        node = self._head.next
        while node is not self._tail:
            keys.append(node.key)
            node = node.next
        return keys


def _valid_json(value):
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_valid_json(item) for item in value)
    if isinstance(value, dict):
        return all(_is_nonempty_string(key) and _valid_json(item) for key, item in value.items())
    return False


class BackupDatabase:
    def __init__(self):
        self._data = {}
        self._revision = 0
        self._backups = {}
        self._backup_order = []

    def _key(self, key):
        if not _is_nonempty_string(key):
            raise ValueError("invalid key")

    def _label(self, label):
        if not _is_nonempty_string(label):
            raise ValueError("invalid backup label")

    def set(self, key, value):
        self._key(key)
        if not _valid_json(value):
            raise ValueError("invalid value")
        self._data[key] = copy.deepcopy(value)
        self._revision += 1

    def get(self, key, default=None):
        self._key(key)
        if key in self._data:
            return copy.deepcopy(self._data[key])
        return copy.deepcopy(default)

    def contains(self, key):
        self._key(key)
        return key in self._data

    def delete(self, key):
        self._key(key)
        if key not in self._data:
            return False
        del self._data[key]
        self._revision += 1
        return True

    def backup(self, label):
        self._label(label)
        if label in self._backups:
            raise ValueError("duplicate backup")
        self._backups[label] = {
            "source_revision": self._revision,
            "data": copy.deepcopy(self._data),
        }
        self._backup_order.append(label)
        return self._revision

    def restore(self, label):
        self._label(label)
        if label not in self._backups:
            raise KeyError(label)
        self._data = copy.deepcopy(self._backups[label]["data"])
        self._revision += 1
        return self._revision

    def list_backups(self):
        return [
            {
                "label": label,
                "source_revision": self._backups[label]["source_revision"],
                "key_count": len(self._backups[label]["data"]),
            }
            for label in self._backup_order
        ]

    def drop_backup(self, label):
        self._label(label)
        if label not in self._backups:
            raise KeyError(label)
        del self._backups[label]
        self._backup_order.remove(label)
