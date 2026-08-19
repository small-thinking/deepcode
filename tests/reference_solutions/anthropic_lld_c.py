import copy
import math
from bisect import bisect_right


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value)


def _is_nonnegative_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_positive_int(value):
    return _is_nonnegative_int(value) and value > 0


class ObjectStorageNamespace:
    def __init__(self):
        self._namespaces = {}

    def _namespace(self, namespace):
        if not _is_nonempty_string(namespace):
            raise ValueError("invalid namespace")
        if namespace not in self._namespaces:
            raise KeyError(namespace)
        return self._namespaces[namespace]

    def _owner(self, entry, actor):
        if not _is_nonempty_string(actor):
            raise ValueError("invalid actor")
        if entry["owner"] != actor:
            raise PermissionError(actor)

    def create_namespace(self, namespace, owner):
        if not _is_nonempty_string(namespace) or not _is_nonempty_string(owner):
            raise ValueError("invalid namespace or owner")
        if namespace in self._namespaces:
            raise ValueError("duplicate namespace")
        self._namespaces[namespace] = {"owner": owner, "objects": {}}

    def put(self, namespace, key, content, actor):
        entry = self._namespace(namespace)
        if not _is_nonempty_string(key) or not isinstance(content, str):
            raise ValueError("invalid object")
        self._owner(entry, actor)
        entry["objects"][key] = content

    def get(self, namespace, key, actor):
        entry = self._namespace(namespace)
        if not _is_nonempty_string(key):
            raise ValueError("invalid object key")
        self._owner(entry, actor)
        if key not in entry["objects"]:
            raise KeyError(key)
        return entry["objects"][key]

    def list_objects(self, namespace, actor, prefix=""):
        entry = self._namespace(namespace)
        if not isinstance(prefix, str):
            raise ValueError("invalid prefix")
        self._owner(entry, actor)
        return [
            {"key": key, "size": len(entry["objects"][key])}
            for key in sorted(entry["objects"])
            if key.startswith(prefix)
        ]

    def delete(self, namespace, key, actor):
        entry = self._namespace(namespace)
        if not _is_nonempty_string(key):
            raise ValueError("invalid object key")
        self._owner(entry, actor)
        if key not in entry["objects"]:
            return False
        del entry["objects"][key]
        return True

    def transfer_owner(self, namespace, new_owner, actor):
        entry = self._namespace(namespace)
        if not _is_nonempty_string(new_owner):
            raise ValueError("invalid owner")
        self._owner(entry, actor)
        entry["owner"] = new_owner


class Resource:
    def __init__(self, name, kind, payload):
        self.name = name
        self.kind = kind
        self.payload = payload


def _is_scalar(value):
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return True
    return isinstance(value, float) and math.isfinite(value)


class TypedResourceRegistry:
    _KINDS = {"text", "count", "labels", "properties"}

    def __init__(self):
        self._resources = {}

    def _name(self, name):
        if not _is_nonempty_string(name):
            raise ValueError("invalid name")

    def _kind(self, kind):
        if not _is_nonempty_string(kind) or kind not in self._KINDS:
            raise ValueError("invalid kind")

    def _payload(self, kind, payload):
        if kind == "text":
            valid = isinstance(payload, str)
        elif kind == "count":
            valid = _is_nonnegative_int(payload)
        elif kind == "labels":
            valid = (
                isinstance(payload, (list, tuple))
                and bool(payload)
                and all(_is_nonempty_string(value) for value in payload)
                and len(set(payload)) == len(payload)
            )
        else:
            valid = (
                isinstance(payload, dict)
                and bool(payload)
                and all(_is_nonempty_string(key) and _is_scalar(value) for key, value in payload.items())
            )
        if not valid:
            raise ValueError("invalid payload")

    def _copy_resource(self, resource):
        return Resource(resource.name, resource.kind, copy.deepcopy(resource.payload))

    def register(self, resource):
        if not isinstance(resource, Resource):
            raise ValueError("resource required")
        self._name(resource.name)
        self._kind(resource.kind)
        self._payload(resource.kind, resource.payload)
        if resource.name in self._resources:
            raise ValueError("duplicate resource")
        payload = list(resource.payload) if resource.kind == "labels" else copy.deepcopy(resource.payload)
        self._resources[resource.name] = Resource(resource.name, resource.kind, payload)

    def get(self, name, expected_kind=None):
        self._name(name)
        if expected_kind is not None:
            self._kind(expected_kind)
        if name not in self._resources:
            raise KeyError(name)
        resource = self._resources[name]
        if expected_kind is not None and resource.kind != expected_kind:
            raise TypeError("unexpected kind")
        return self._copy_resource(resource)

    def names(self, kind=None):
        if kind is not None:
            self._kind(kind)
        return sorted(name for name, resource in self._resources.items() if kind is None or resource.kind == kind)

    def remove(self, name):
        self._name(name)
        if name not in self._resources:
            return False
        del self._resources[name]
        return True


def _dimensions(m, n, k, element_bytes):
    if not all(_is_positive_int(value) for value in (m, n, k, element_bytes)):
        raise ValueError("invalid dimensions")


def _tile(m, n, k, tile):
    if not isinstance(tile, (tuple, list)) or len(tile) != 3:
        raise ValueError("invalid tile")
    tm, tn, tk = tile
    if not all(_is_positive_int(value) for value in (tm, tn, tk)):
        raise ValueError("invalid tile")
    if m % tm != 0 or n % tn != 0 or k % tk != 0:
        raise ValueError("tile does not divide dimensions")
    return (tm, tn, tk)


def estimate_tiled_matmul_cost(m, n, k, tile, element_bytes=4):
    _dimensions(m, n, k, element_bytes)
    tm, tn, tk = _tile(m, n, k, tile)
    workspace_bytes = element_bytes * (tm * tk + tk * tn + tm * tn)
    output_tiles = (m // tm) * (n // tn)
    inner_blocks = k // tk
    estimated_bytes = element_bytes * (output_tiles * inner_blocks * (tm * tk + tk * tn) + m * n)
    flops = 2 * m * n * k
    return {
        "tile": (tm, tn, tk),
        "workspace_bytes": workspace_bytes,
        "estimated_bytes": estimated_bytes,
        "arithmetic_intensity": float(flops) / estimated_bytes,
    }


def choose_matrix_tiling(m, n, k, tile_candidates, max_workspace_bytes, element_bytes=4):
    _dimensions(m, n, k, element_bytes)
    if not _is_positive_int(max_workspace_bytes):
        raise ValueError("invalid workspace budget")
    if not isinstance(tile_candidates, (list, tuple)) or not tile_candidates:
        raise ValueError("invalid candidates")
    feasible = []
    for tile in tile_candidates:
        cost = estimate_tiled_matmul_cost(m, n, k, tile, element_bytes)
        if cost["workspace_bytes"] <= max_workspace_bytes:
            feasible.append(cost)
    if not feasible:
        raise ValueError("no feasible tile")
    return min(feasible, key=lambda cost: (cost["estimated_bytes"], cost["tile"]))


class VersionedGetWhenDatabase:
    def __init__(self):
        self._records = {}

    def _record_id(self, record_id):
        if not _is_nonempty_string(record_id):
            raise ValueError("invalid record id")

    def _version(self, version):
        if not _is_nonnegative_int(version):
            raise ValueError("invalid version")

    def _fields(self, fields):
        if not isinstance(fields, dict) or not fields:
            raise ValueError("invalid fields")
        if any(not _is_nonempty_string(key) or not _is_scalar(value) for key, value in fields.items()):
            raise ValueError("invalid fields")

    def _existing(self, record_id):
        self._record_id(record_id)
        if record_id not in self._records:
            raise KeyError(record_id)
        return self._records[record_id]

    def _view(self, record_id, snapshot):
        return {"id": record_id, "version": snapshot["version"], "fields": dict(snapshot["fields"])}

    def write(self, record_id, version, fields):
        self._record_id(record_id)
        self._version(version)
        self._fields(fields)
        snapshots = self._records.setdefault(record_id, [])
        if snapshots and version <= snapshots[-1]["version"]:
            raise ValueError("versions must advance")
        snapshots.append({"version": version, "fields": dict(fields)})

    def get_at(self, record_id, version):
        snapshots = self._existing(record_id)
        self._version(version)
        versions = [snapshot["version"] for snapshot in snapshots]
        index = bisect_right(versions, version) - 1
        return None if index < 0 else self._view(record_id, snapshots[index])

    def get_when(self, record_id, field, expected, min_version=0):
        snapshots = self._existing(record_id)
        if not _is_nonempty_string(field) or not _is_scalar(expected):
            raise ValueError("invalid condition")
        self._version(min_version)
        for snapshot in snapshots:
            if snapshot["version"] >= min_version and snapshot["fields"].get(field) == expected and field in snapshot["fields"]:
                return self._view(record_id, snapshot)
        return None

    def history(self, record_id, start_version=0, end_version=None):
        snapshots = self._existing(record_id)
        self._version(start_version)
        if end_version is not None:
            self._version(end_version)
            if end_version < start_version:
                raise ValueError("reversed range")
        return [
            self._view(record_id, snapshot)
            for snapshot in snapshots
            if snapshot["version"] >= start_version and (end_version is None or snapshot["version"] <= end_version)
        ]
