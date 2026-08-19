import copy

import numpy as np


def run_tool_session(initial_state, tools, actions, max_calls):
    if not isinstance(initial_state, dict) or not isinstance(tools, dict):
        raise ValueError("initial_state and tools must be mappings")
    if not isinstance(actions, (list, tuple)):
        raise ValueError("actions must be a sequence")
    if isinstance(max_calls, bool) or not isinstance(max_calls, int) or max_calls <= 0:
        raise ValueError("max_calls must be a positive integer")

    state = copy.deepcopy(initial_state)
    transcript = []
    calls = 0
    for action in actions:
        if not isinstance(action, dict) or "type" not in action:
            raise ValueError("malformed action")
        action_type = action["type"]
        if action_type == "final":
            if "answer" not in action:
                raise ValueError("final action requires an answer")
            return {
                "state": state,
                "transcript": transcript,
                "status": "complete",
                "answer": copy.deepcopy(action["answer"]),
            }
        if action_type != "tool":
            raise ValueError("unknown action type")
        name = action.get("name")
        arguments = action.get("arguments")
        if not isinstance(name, str) or not isinstance(arguments, dict) or name not in tools:
            raise ValueError("invalid tool action")
        if calls >= max_calls:
            raise RuntimeError("tool call limit exceeded")
        updates = tools[name](copy.deepcopy(state), copy.deepcopy(arguments))
        if not isinstance(updates, dict):
            raise TypeError("tools must return update mappings")
        copied_updates = copy.deepcopy(updates)
        state.update(copied_updates)
        transcript.append({
            "name": name,
            "arguments": copy.deepcopy(arguments),
            "updates": copied_updates,
        })
        calls += 1
    return {"state": state, "transcript": transcript, "status": "incomplete", "answer": None}


def _normalize_name(name):
    if not isinstance(name, str):
        raise ValueError("name must be a string")
    normalized = name.strip().rstrip(".").lower()
    if not normalized:
        raise ValueError("name must not be empty")
    return normalized


def _normalize_record_type(record_type):
    if not isinstance(record_type, str):
        raise ValueError("record type must be a string")
    normalized = record_type.strip().upper()
    if not normalized:
        raise ValueError("record type must not be empty")
    return normalized


def _read_record(record):
    if not isinstance(record, dict) or set(record) != {"value", "ttl"}:
        raise ValueError("records need value and ttl")
    value, ttl = record["value"], record["ttl"]
    if not isinstance(value, str) or not value:
        raise ValueError("record value must be a nonempty string")
    if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or ttl <= 0:
        raise ValueError("record TTL must be positive")
    return value, ttl


def _normalized_records(records):
    if not isinstance(records, dict):
        raise ValueError("records must be a mapping")
    normalized = {}
    for raw_name, record_types in records.items():
        name = _normalize_name(raw_name)
        if not isinstance(record_types, dict):
            raise ValueError("record types must be a mapping")
        normalized[name] = {}
        for raw_type, record in record_types.items():
            normalized[name][_normalize_record_type(raw_type)] = record
    return normalized


def resolve_dns(records, cache, name, record_type, now):
    if not isinstance(cache, dict):
        raise ValueError("cache must be a mapping")
    query_name = _normalize_name(name)
    query_type = _normalize_record_type(record_type)
    key = (query_name, query_type)
    cached = cache.get(key)
    if cached is not None:
        if not isinstance(cached, dict) or not {"value", "chain", "expires_at"} <= set(cached):
            raise ValueError("malformed cache entry")
        if cached["expires_at"] > now:
            return {
                "status": "ok",
                "value": cached["value"],
                "chain": list(cached["chain"]),
                "ttl_remaining": cached["expires_at"] - now,
                "from_cache": True,
            }

    zones = _normalized_records(records)
    current = query_name
    chain = []
    seen = set()
    smallest_ttl = None
    while True:
        chain.append(current)
        if current in seen:
            return {
                "status": "loop",
                "value": None,
                "chain": chain,
                "ttl_remaining": None,
                "from_cache": False,
            }
        seen.add(current)
        entries = zones.get(current)
        if entries is None:
            return {
                "status": "not_found",
                "value": None,
                "chain": chain,
                "ttl_remaining": None,
                "from_cache": False,
            }
        if query_type in entries:
            value, ttl = _read_record(entries[query_type])
            smallest_ttl = ttl if smallest_ttl is None else min(smallest_ttl, ttl)
            expires_at = now + smallest_ttl
            stored = {"value": value, "chain": list(chain), "expires_at": expires_at}
            cache[key] = stored
            return {
                "status": "ok",
                "value": value,
                "chain": list(chain),
                "ttl_remaining": smallest_ttl,
                "from_cache": False,
            }
        if "CNAME" not in entries:
            return {
                "status": "not_found",
                "value": None,
                "chain": chain,
                "ttl_remaining": None,
                "from_cache": False,
            }
        target, ttl = _read_record(entries["CNAME"])
        smallest_ttl = ttl if smallest_ttl is None else min(smallest_ttl, ttl)
        current = _normalize_name(target)


def _standardize_parameter(value, image):
    parameter = np.asarray(value, dtype=np.float64)
    if parameter.ndim == 0:
        return parameter
    if image.ndim == 3 and parameter.shape == (image.shape[2],):
        return parameter.reshape(1, 1, image.shape[2])
    raise ValueError("mean and std must be scalar or per-channel vectors")


def transform_image(image, operations):
    if not isinstance(image, np.ndarray) or image.ndim not in (2, 3):
        raise ValueError("image must be a 2-D or HWC NumPy array")
    if not isinstance(operations, (list, tuple)):
        raise ValueError("operations must be a sequence")
    result = image.astype(np.float64, copy=True)
    for operation in operations:
        if not isinstance(operation, dict) or not isinstance(operation.get("op"), str):
            raise ValueError("malformed operation")
        op_name = operation["op"]
        if op_name == "clip":
            if "low" not in operation or "high" not in operation or operation["low"] > operation["high"]:
                raise ValueError("invalid clip bounds")
            result = np.clip(result, operation["low"], operation["high"])
        elif op_name == "affine":
            if "scale" not in operation or "bias" not in operation:
                raise ValueError("affine needs scale and bias")
            result = result * operation["scale"] + operation["bias"]
        elif op_name == "standardize":
            if "mean" not in operation or "std" not in operation:
                raise ValueError("standardize needs mean and std")
            mean = _standardize_parameter(operation["mean"], result)
            std = _standardize_parameter(operation["std"], result)
            if not np.all(np.isfinite(std)) or not np.all(std > 0):
                raise ValueError("standard deviations must be positive")
            result = (result - mean) / std
        elif op_name == "hflip":
            result = result[:, ::-1, ...].copy()
        elif op_name == "transpose_hw":
            result = np.swapaxes(result, 0, 1).copy()
        else:
            raise ValueError("unknown operation")
    return result


def masked_batched_gather(values, indices, fill_value=0):
    if not isinstance(values, np.ndarray) or values.ndim != 3:
        raise ValueError("values must be rank three")
    if not isinstance(indices, np.ndarray) or indices.ndim != 2:
        raise ValueError("indices must be rank two")
    if indices.shape[0] != values.shape[0]:
        raise ValueError("batch sizes must match")
    if not np.issubdtype(indices.dtype, np.integer) or np.issubdtype(indices.dtype, np.bool_):
        raise ValueError("indices must have an integer dtype")
    items = values.shape[1]
    if np.any(indices < -1) or np.any(indices >= items):
        raise ValueError("index out of range")

    output_dtype = np.result_type(values.dtype, np.asarray(fill_value).dtype)
    valid = indices >= 0
    safe_indices = np.where(valid, indices, 0)
    gathered = np.take_along_axis(values, safe_indices[..., None], axis=1).astype(output_dtype, copy=True)
    gathered = np.where(valid[..., None], gathered, np.asarray(fill_value, dtype=output_dtype))
    return gathered, valid
