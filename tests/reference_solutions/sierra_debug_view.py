"""Reference answer for the explicit Debug View practice contract.

Part 1 combines intervals within a role, then merges the three timelines.
Parts 2-4 annotate that result without changing their inputs.
"""

from bisect import bisect_right


def merge_chunks(agent_chunks, user_chunks, tool_chunks):
    result = []
    for role, chunks in (
        ("user", user_chunks),
        ("agent", agent_chunks),
        ("tool", tool_chunks),
    ):
        merged = []
        # Stable sorting preserves input order when both endpoints tie.
        for start, end, text in sorted(chunks, key=lambda chunk: (chunk[0], chunk[1])):
            if merged and start <= merged[-1]["end"]:
                merged[-1]["end"] = max(merged[-1]["end"], end)
                merged[-1]["text"].append(text)
            else:
                merged.append({"role": role, "start": start, "end": end, "text": [text]})
        # Join once per merged interval, avoiding quadratic string copying.
        for chunk in merged:
            chunk["text"] = " ".join(chunk["text"])
        result.extend(merged)

    priority = {"user": 0, "agent": 1, "tool": 2}
    return sorted(result, key=lambda chunk: (chunk["start"], priority[chunk["role"]]))


def mark_interruptions(chunks):
    # A user already speaking, or starting at the same time, is not a new
    # interruption under this exercise's convention.
    user_starts = [chunk["start"] for chunk in chunks if chunk["role"] == "user"]
    result = []
    for chunk in chunks:
        item = dict(chunk)
        item["interrupted"] = False
        if item["role"] == "agent":
            index = bisect_right(user_starts, item["start"])
            if index < len(user_starts) and user_starts[index] < item["end"]:
                item["end"] = user_starts[index]
                item["text"] += " ... [INTERRUPTED]"
                item["interrupted"] = True
        result.append(item)
    return result


def insert_gaps(chunks):
    result = []
    for index, chunk in enumerate(chunks):
        result.append(dict(chunk))
        if index + 1 == len(chunks):
            continue
        following = chunks[index + 1]
        if chunk["role"] == "user" and following["role"] == "agent":
            duration = following["start"] - chunk["end"]
            if duration > 0:
                result.append({
                    "role": "gap",
                    "start": chunk["end"],
                    "end": following["start"],
                    "text": f"[{duration} ms gap]",
                    "interrupted": False,
                })
    return result


def thinking_time_p50(chunks):
    durations = sorted(
        chunk["end"] - chunk["start"]
        for chunk in chunks
        if chunk["role"] == "gap"
    )
    count = len(durations)
    if count == 0:
        return 0
    middle = count // 2
    if count % 2:
        return durations[middle]
    return (durations[middle - 1] + durations[middle]) / 2
