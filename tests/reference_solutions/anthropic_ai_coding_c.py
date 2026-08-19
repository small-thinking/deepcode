import copy

import numpy as np


def _validate_layout_state(state, breakpoint):
    if not isinstance(state, dict):
        raise ValueError("state must be a mapping")
    required = {"width", "sidebar_open", "query", "selected_id", "items"}
    if not required <= set(state):
        raise ValueError("state is missing required fields")
    if type(breakpoint) is not int or breakpoint <= 0:
        raise ValueError("breakpoint must be a positive integer")
    if type(state["width"]) is not int or state["width"] <= 0:
        raise ValueError("width must be a positive integer")
    if type(state["sidebar_open"]) is not bool or not isinstance(state["query"], str):
        raise ValueError("invalid sidebar or query state")
    if state["selected_id"] is not None and (not isinstance(state["selected_id"], str) or not state["selected_id"]):
        raise ValueError("selected_id must be None or a nonempty string")
    if not isinstance(state["items"], list):
        raise ValueError("items must be a list")
    items = []
    item_ids = set()
    for item in state["items"]:
        if not isinstance(item, dict) or set(item) != {"id", "label"}:
            raise ValueError("items require id and label")
        item_id, label = item["id"], item["label"]
        if not isinstance(item_id, str) or not item_id or not isinstance(label, str) or not label:
            raise ValueError("item IDs and labels must be nonempty strings")
        if item_id in item_ids:
            raise ValueError("item IDs must be unique")
        item_ids.add(item_id)
        items.append({"id": item_id, "label": label})
    if state["selected_id"] is not None and state["selected_id"] not in item_ids:
        raise ValueError("selected item must exist")
    return {
        "width": state["width"],
        "sidebar_open": state["sidebar_open"],
        "query": state["query"],
        "selected_id": state["selected_id"],
        "items": items,
    }


def _visible_ids(items, query):
    normalized_query = query.casefold()
    return [item["id"] for item in items if normalized_query in item["label"].casefold()]


def reduce_layout_state(state, action, breakpoint=720):
    next_state = _validate_layout_state(state, breakpoint)
    if not isinstance(action, dict) or not isinstance(action.get("type"), str):
        raise ValueError("action must have a type")
    action_type = action["type"]
    if action_type == "resize":
        width = action.get("width")
        if type(width) is not int or width <= 0:
            raise ValueError("resize width must be a positive integer")
        next_state["width"] = width
    elif action_type == "toggle_sidebar":
        next_state["sidebar_open"] = not next_state["sidebar_open"]
    elif action_type == "set_query":
        query = action.get("query")
        if not isinstance(query, str):
            raise ValueError("query must be a string")
        next_state["query"] = query
        if next_state["selected_id"] not in _visible_ids(next_state["items"], query):
            next_state["selected_id"] = None
    elif action_type == "select":
        item_id = action.get("id")
        if not isinstance(item_id, str) or item_id not in _visible_ids(next_state["items"], next_state["query"]):
            raise ValueError("selected item must be visible")
        next_state["selected_id"] = item_id
    elif action_type == "clear_selection":
        next_state["selected_id"] = None
    else:
        raise ValueError("unknown action")
    next_state["layout"] = "wide" if next_state["width"] >= breakpoint else "compact"
    next_state["visible_ids"] = _visible_ids(next_state["items"], next_state["query"])
    return next_state


def recover_idempotent_jobs(events):
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be a non-string iterable")
    try:
        iterator = iter(events)
    except TypeError as error:
        raise ValueError("events must be iterable") from error
    states = {}
    for event in iterator:
        if not isinstance(event, dict) or set(event) != {"job_id", "phase"}:
            raise ValueError("events need job_id and phase")
        job_id, phase = event["job_id"], event["phase"]
        if not isinstance(job_id, str) or not job_id or phase not in {"claim", "effect_committed", "ack"}:
            raise ValueError("invalid job event")
        current = states.get(job_id)
        if current == "acked":
            continue
        if phase == "claim":
            if current is None:
                states[job_id] = "claimed"
        elif phase == "effect_committed":
            if current not in {"claimed", "effect_committed"}:
                raise ValueError("effect requires an earlier claim")
            states[job_id] = "effect_committed"
        else:
            if current not in {"effect_committed", "acked"}:
                raise ValueError("ack requires a committed effect")
            states[job_id] = "acked"
    return {
        "completed": sorted(job_id for job_id, state in states.items() if state == "acked"),
        "replay": sorted(job_id for job_id, state in states.items() if state == "claimed"),
        "acknowledge": sorted(job_id for job_id, state in states.items() if state == "effect_committed"),
        "effect_committed": sorted(job_id for job_id, state in states.items() if state in {"effect_committed", "acked"}),
    }


def _validate_sample_aspect_inputs(sample_counts, aspect_losses, aspect_names):
    if not isinstance(sample_counts, np.ndarray) or not isinstance(aspect_losses, np.ndarray):
        raise ValueError("sample_counts and aspect_losses must be NumPy arrays")
    if sample_counts.ndim != 1 or sample_counts.size < 3:
        raise ValueError("sample_counts must be one-dimensional with at least three entries")
    if not np.issubdtype(sample_counts.dtype, np.integer) or np.any(sample_counts <= 0) or np.any(np.diff(sample_counts) <= 0):
        raise ValueError("sample counts must be strictly increasing positive integers")
    if aspect_losses.ndim != 2 or aspect_losses.shape[0] != sample_counts.size or aspect_losses.shape[1] == 0:
        raise ValueError("aspect_losses must align sample counts and have an aspect column")
    if not np.issubdtype(aspect_losses.dtype, np.number) or not np.isfinite(aspect_losses).all() or np.any(aspect_losses < 0):
        raise ValueError("aspect losses must be finite nonnegative numbers")
    if aspect_names is None:
        return [f"aspect_{index}" for index in range(aspect_losses.shape[1])]
    if isinstance(aspect_names, (str, bytes)) or not isinstance(aspect_names, (list, tuple)):
        raise ValueError("aspect_names must be a sequence")
    if len(aspect_names) != aspect_losses.shape[1] or any(not isinstance(name, str) or not name for name in aspect_names):
        raise ValueError("aspect names must be nonempty and aligned")
    if len(set(aspect_names)) != len(aspect_names):
        raise ValueError("aspect names must be unique")
    return list(aspect_names)


def diagnose_sample_aspect_losses(sample_counts, aspect_losses, aspect_names=None):
    names = _validate_sample_aspect_inputs(sample_counts, aspect_losses, aspect_names)
    losses = aspect_losses.astype(np.float64, copy=False)
    aspects = []
    double_descent_aspects = []
    for column, name in enumerate(names):
        values = losses[:, column]
        peaks = [
            index
            for index in range(1, values.size - 1)
            if values[index] > values[index - 1] and values[index] > values[index + 1]
        ]
        if not peaks:
            aspects.append({
                "name": name,
                "peak_index": None,
                "peak_samples": None,
                "peak_loss": None,
                "double_descent": False,
            })
            continue
        peak_index = min(peaks, key=lambda index: (-values[index], index))
        peak_loss = float(values[peak_index])
        double_descent = bool(peak_loss > values[0] and peak_loss > values[-1])
        aspect = {
            "name": name,
            "peak_index": peak_index,
            "peak_samples": int(sample_counts[peak_index]),
            "peak_loss": peak_loss,
            "double_descent": double_descent,
        }
        aspects.append(aspect)
        if double_descent:
            double_descent_aspects.append(name)
    return {
        "mean_loss": losses.mean(axis=1),
        "aspects": aspects,
        "double_descent_aspects": double_descent_aspects,
    }
