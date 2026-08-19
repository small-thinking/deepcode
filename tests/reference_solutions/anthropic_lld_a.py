import copy
import math


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value)


def _is_nonnegative_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_positive_int(value):
    return _is_nonnegative_int(value) and value > 0


class TransferLedger:
    def __init__(self):
        self._balances = {}
        self._transfers = {}
        self._next_transfer = 1

    def open(self, account_id, initial_balance=0):
        if not _is_nonempty_string(account_id) or not _is_nonnegative_int(initial_balance):
            raise ValueError("invalid account")
        if account_id in self._balances:
            raise ValueError("account already exists")
        self._balances[account_id] = initial_balance

    def balance(self, account_id):
        if not _is_nonempty_string(account_id):
            raise ValueError("invalid account")
        if account_id not in self._balances:
            raise KeyError(account_id)
        return self._balances[account_id]

    def create_transfer(self, source, destination, amount):
        if not _is_positive_int(amount) or not _is_nonempty_string(source) or not _is_nonempty_string(destination):
            raise ValueError("invalid transfer")
        if source not in self._balances or destination not in self._balances:
            raise KeyError("unknown account")
        if source == destination:
            raise ValueError("self transfer")
        transfer_id = f"transfer-{self._next_transfer}"
        self._next_transfer += 1
        self._transfers[transfer_id] = {
            "id": transfer_id,
            "source": source,
            "destination": destination,
            "amount": amount,
            "status": "pending",
        }
        return transfer_id

    def _pending_transfer(self, transfer_id):
        if not _is_nonempty_string(transfer_id):
            raise ValueError("invalid transfer id")
        if transfer_id not in self._transfers:
            raise KeyError(transfer_id)
        transfer = self._transfers[transfer_id]
        if transfer["status"] != "pending":
            raise ValueError("transfer is terminal")
        return transfer

    def accept(self, transfer_id):
        transfer = self._pending_transfer(transfer_id)
        if self._balances[transfer["source"]] < transfer["amount"]:
            transfer["status"] = "rejected"
            return False
        self._balances[transfer["source"]] -= transfer["amount"]
        self._balances[transfer["destination"]] += transfer["amount"]
        transfer["status"] = "accepted"
        return True

    def cancel(self, transfer_id):
        self._pending_transfer(transfer_id)["status"] = "cancelled"

    def merge_accounts(self, keep, absorb):
        if not _is_nonempty_string(keep) or not _is_nonempty_string(absorb) or keep == absorb:
            raise ValueError("invalid merge")
        if keep not in self._balances or absorb not in self._balances:
            raise KeyError("unknown account")
        self._balances[keep] += self._balances.pop(absorb)
        for transfer in self._transfers.values():
            if transfer["status"] != "pending":
                continue
            if transfer["source"] == absorb:
                transfer["source"] = keep
            if transfer["destination"] == absorb:
                transfer["destination"] = keep
            if transfer["source"] == transfer["destination"]:
                transfer["status"] = "cancelled"

    def transfer(self, transfer_id):
        if not _is_nonempty_string(transfer_id):
            raise ValueError("invalid transfer id")
        if transfer_id not in self._transfers:
            raise KeyError(transfer_id)
        return dict(self._transfers[transfer_id])


class SnapshotTaskManager:
    def __init__(self):
        self._tasks = {}

    def _validate_time(self, timestamp):
        if not _is_nonnegative_int(timestamp):
            raise ValueError("invalid timestamp")

    def _expire(self, timestamp):
        self._validate_time(timestamp)
        expired = [task_id for task_id, task in self._tasks.items() if timestamp >= task["expires_at"]]
        for task_id in expired:
            del self._tasks[task_id]
        for task in self._tasks.values():
            if task["lease"] is not None and timestamp >= task["lease"]["expires_at"]:
                task["lease"] = None

    def create(self, task_id, payload, timestamp, ttl):
        self._validate_time(timestamp)
        if not _is_nonempty_string(task_id) or not _is_nonempty_string(payload) or not _is_positive_int(ttl):
            raise ValueError("invalid task")
        self._expire(timestamp)
        if task_id in self._tasks:
            raise ValueError("duplicate live task")
        self._tasks[task_id] = {
            "payload": payload,
            "expires_at": timestamp + ttl,
            "lease": None,
        }

    def claim(self, task_id, worker, timestamp, lease_ttl):
        self._validate_time(timestamp)
        if not _is_nonempty_string(task_id) or not _is_nonempty_string(worker) or not _is_positive_int(lease_ttl):
            raise ValueError("invalid claim")
        self._expire(timestamp)
        task = self._tasks.get(task_id)
        if task is None or task["lease"] is not None:
            return False
        task["lease"] = {"worker": worker, "expires_at": timestamp + lease_ttl}
        return True

    def finish(self, task_id, worker, timestamp):
        self._validate_time(timestamp)
        if not _is_nonempty_string(task_id) or not _is_nonempty_string(worker):
            raise ValueError("invalid finish")
        self._expire(timestamp)
        task = self._tasks.get(task_id)
        if task is None or task["lease"] is None or task["lease"]["worker"] != worker:
            return False
        del self._tasks[task_id]
        return True

    def ready(self, timestamp):
        self._expire(timestamp)
        return sorted(task_id for task_id, task in self._tasks.items() if task["lease"] is None)

    def get(self, task_id, timestamp):
        self._validate_time(timestamp)
        if not _is_nonempty_string(task_id):
            raise ValueError("invalid task id")
        self._expire(timestamp)
        task = self._tasks.get(task_id)
        if task is None:
            return None
        lease = task["lease"]
        return {
            "task_id": task_id,
            "payload": task["payload"],
            "status": "leased" if lease is not None else "ready",
            "worker": None if lease is None else lease["worker"],
        }

    def snapshot(self, timestamp):
        self._expire(timestamp)
        tasks = {}
        for task_id, task in self._tasks.items():
            lease = task["lease"]
            tasks[task_id] = {
                "payload": task["payload"],
                "remaining_ttl": task["expires_at"] - timestamp,
                "lease": None
                if lease is None
                else {
                    "worker": lease["worker"],
                    "remaining_ttl": lease["expires_at"] - timestamp,
                },
            }
        return {"tasks": copy.deepcopy(tasks)}

    def restore(self, snapshot, timestamp):
        self._validate_time(timestamp)
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("tasks"), dict):
            raise ValueError("invalid snapshot")
        rebuilt = {}
        for task_id, saved in snapshot["tasks"].items():
            if not _is_nonempty_string(task_id) or not isinstance(saved, dict):
                raise ValueError("invalid snapshot")
            payload = saved.get("payload")
            remaining_ttl = saved.get("remaining_ttl")
            lease = saved.get("lease")
            if not _is_nonempty_string(payload) or not _is_positive_int(remaining_ttl):
                raise ValueError("invalid snapshot")
            rebuilt_lease = None
            if lease is not None:
                if not isinstance(lease, dict) or not _is_nonempty_string(lease.get("worker")) or not _is_positive_int(lease.get("remaining_ttl")):
                    raise ValueError("invalid snapshot")
                rebuilt_lease = {
                    "worker": lease["worker"],
                    "expires_at": timestamp + lease["remaining_ttl"],
                }
            rebuilt[task_id] = {
                "payload": payload,
                "expires_at": timestamp + remaining_ttl,
                "lease": rebuilt_lease,
            }
        self._tasks = rebuilt


class EmployeeGrantManager:
    _LEVELS = {"read": 1, "write": 2, "admin": 3}

    def __init__(self):
        self._managers = {}
        self._grants = {}

    def _employee(self, employee_id):
        if not _is_nonempty_string(employee_id):
            raise ValueError("invalid employee")
        if employee_id not in self._managers:
            raise KeyError(employee_id)

    def _resource(self, resource):
        if not _is_nonempty_string(resource):
            raise ValueError("invalid resource")

    def _level(self, level):
        if not _is_nonempty_string(level) or level not in self._LEVELS:
            raise ValueError("invalid level")

    def add_employee(self, employee_id, manager_id=None):
        if not _is_nonempty_string(employee_id):
            raise ValueError("invalid employee")
        if employee_id in self._managers:
            raise ValueError("duplicate employee")
        if manager_id is not None:
            if not _is_nonempty_string(manager_id):
                raise ValueError("invalid manager")
            self._employee(manager_id)
        self._managers[employee_id] = manager_id
        self._grants[employee_id] = {}

    def set_manager(self, employee_id, manager_id):
        self._employee(employee_id)
        if manager_id is not None:
            if not _is_nonempty_string(manager_id):
                raise ValueError("invalid manager")
            self._employee(manager_id)
            if manager_id == employee_id:
                raise ValueError("self manager")
            current = manager_id
            while current is not None:
                if current == employee_id:
                    raise ValueError("manager cycle")
                current = self._managers[current]
        self._managers[employee_id] = manager_id

    def grant(self, employee_id, resource, level):
        self._employee(employee_id)
        self._resource(resource)
        self._level(level)
        self._grants[employee_id][resource] = level

    def revoke(self, employee_id, resource):
        self._employee(employee_id)
        self._resource(resource)
        return self._grants[employee_id].pop(resource, None) is not None

    def access_level(self, employee_id, resource):
        self._employee(employee_id)
        self._resource(resource)
        best = None
        current = employee_id
        while current is not None:
            level = self._grants[current].get(resource)
            if level is not None and (best is None or self._LEVELS[level] > self._LEVELS[best]):
                best = level
            current = self._managers[current]
        return best

    def allowed(self, employee_id, resource, minimum_level):
        self._level(minimum_level)
        actual = self.access_level(employee_id, resource)
        return actual is not None and self._LEVELS[actual] >= self._LEVELS[minimum_level]

    def audit(self, resource):
        self._resource(resource)
        rows = []
        for employee_id in self._managers:
            level = self.access_level(employee_id, resource)
            if level is not None:
                rows.append((employee_id, level))
        return sorted(rows)


def _is_scalar(value):
    if isinstance(value, bool) or isinstance(value, str) or isinstance(value, int):
        return True
    return isinstance(value, float) and math.isfinite(value)


class MLConfigRegistry:
    def __init__(self):
        self._models = {}
        self._active = {}

    def _model(self, model):
        if not _is_nonempty_string(model):
            raise ValueError("invalid model")

    def _version(self, version):
        if not _is_positive_int(version):
            raise ValueError("invalid version")

    def _values(self, values):
        if not isinstance(values, dict):
            raise ValueError("values must be a dict")
        for key, value in values.items():
            if not _is_nonempty_string(key) or not _is_scalar(value):
                raise ValueError("invalid config value")

    def _lookup(self, model, version):
        if model not in self._models:
            raise KeyError(model)
        if version not in self._models[model]:
            raise KeyError(version)
        return self._models[model][version]

    def register(self, model, version, values, base_version=None):
        self._model(model)
        self._version(version)
        self._values(values)
        versions = self._models.get(model)
        if versions is None:
            if base_version is not None:
                self._version(base_version)
                raise ValueError("unknown base version")
            versions = {}
        if version in versions:
            raise ValueError("duplicate version")
        if base_version is not None:
            self._version(base_version)
            if base_version not in versions:
                raise ValueError("unknown base version")
        versions[version] = {"values": dict(values), "base_version": base_version}
        self._models[model] = versions

    def activate(self, model, version):
        self._model(model)
        self._version(version)
        self._lookup(model, version)
        self._active[model] = version

    def _resolve_stored(self, model, version):
        record = self._lookup(model, version)
        result = {}
        if record["base_version"] is not None:
            result.update(self._resolve_stored(model, record["base_version"]))
        result.update(record["values"])
        return result

    def resolve(self, model, version=None, overrides=None):
        self._model(model)
        if version is None:
            if model not in self._active:
                raise KeyError(model)
            version = self._active[model]
        self._version(version)
        result = self._resolve_stored(model, version)
        if overrides is not None:
            self._values(overrides)
            if any(key not in result for key in overrides):
                raise ValueError("unknown override")
            result.update(overrides)
        return dict(result)

    def versions(self, model):
        self._model(model)
        if model not in self._models:
            raise KeyError(model)
        return sorted(self._models[model])
