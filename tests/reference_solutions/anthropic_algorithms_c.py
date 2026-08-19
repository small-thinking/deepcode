import heapq
from collections import defaultdict, deque
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def schedule_pending_tasks(tasks, completed=()):
    task_ids = set(tasks)
    completed_ids = set(completed)
    if not completed_ids <= task_ids:
        raise ValueError("completed contains an unknown task")

    priorities = {}
    remaining = {}
    dependents = defaultdict(set)
    for task_id, specification in tasks.items():
        dependencies = set(specification["depends_on"])
        priority = specification["priority"]
        if type(priority) is not int:
            raise ValueError("priority must be an integer")
        if not dependencies <= task_ids:
            raise ValueError("dependency is unknown")
        priorities[task_id] = priority
        outstanding = dependencies - completed_ids
        remaining[task_id] = len(outstanding)
        for dependency in outstanding:
            dependents[dependency].add(task_id)

    ready = [(-priorities[task_id], task_id) for task_id in task_ids - completed_ids if remaining[task_id] == 0]
    heapq.heapify(ready)
    result = []

    while ready:
        _negative_priority, task_id = heapq.heappop(ready)
        result.append(task_id)
        for dependent in dependents[task_id]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(ready, (-priorities[dependent], dependent))

    if len(result) != len(task_ids - completed_ids):
        raise ValueError("dependency graph contains a cycle")
    return result


def plan_crawl_frontier(candidates, per_host_limit, global_limit):
    if type(per_host_limit) is not int or type(global_limit) is not int:
        raise ValueError("limits must be ordinary integers")
    if per_host_limit < 0 or global_limit < 0:
        raise ValueError("limits must be nonnegative")

    unique = []
    seen = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict) or set(candidate) != {"url", "priority"}:
            raise ValueError("candidate must have url and priority")
        url = candidate["url"]
        priority = candidate["priority"]
        if not isinstance(url, str) or type(priority) is not int:
            raise ValueError("candidate has invalid fields")
        parsed = urlsplit(url)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            raise ValueError("candidate URL must be absolute HTTP(S)")
        if url in seen:
            continue
        seen.add(url)
        unique.append((priority, index, url, parsed.hostname.lower()))

    unique.sort(key=lambda item: (-item[0], item[1]))
    selected = []
    selected_per_host = defaultdict(int)
    for _priority, _index, url, host in unique:
        if len(selected) >= global_limit:
            break
        if selected_per_host[host] >= per_host_limit:
            continue
        selected.append(url)
        selected_per_host[host] += 1
    return selected


def _file_extension(path):
    basename = path.rsplit("/", 1)[-1]
    dot = basename.rfind(".")
    return "" if dot <= 0 else basename[dot:].lower()


def profile_file_inventory(records):
    counts = defaultdict(int)
    byte_totals = defaultdict(int)
    total_bytes = 0
    largest_size = None
    largest_paths = []

    for record in records:
        path = record["path"]
        size = record["size_bytes"]
        extension = _file_extension(path)
        counts[extension] += 1
        byte_totals[extension] += size
        total_bytes += size
        if largest_size is None or size > largest_size:
            largest_size = size
            largest_paths = [path]
        elif size == largest_size:
            largest_paths.append(path)

    extension_totals = sorted(
        ((extension, counts[extension], byte_totals[extension]) for extension in counts),
        key=lambda item: (-item[2], item[0]),
    )
    return {
        "file_count": sum(counts.values()),
        "total_bytes": total_bytes,
        "extension_totals": extension_totals,
        "largest_paths": sorted(largest_paths),
    }


def label_threshold_components(image, threshold):
    rows = len(image)
    columns = len(image[0])
    labels = [[0] * columns for _ in range(rows)]
    components = []
    next_label = 1

    for start_row in range(rows):
        for start_column in range(columns):
            if image[start_row][start_column] < threshold or labels[start_row][start_column] != 0:
                continue
            queue = deque([(start_row, start_column)])
            labels[start_row][start_column] = next_label
            area = 0
            min_row = max_row = start_row
            min_column = max_column = start_column

            while queue:
                row, column = queue.popleft()
                area += 1
                min_row = min(min_row, row)
                max_row = max(max_row, row)
                min_column = min(min_column, column)
                max_column = max(max_column, column)
                for row_delta, column_delta in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = row + row_delta
                    next_column = column + column_delta
                    if (
                        0 <= next_row < rows
                        and 0 <= next_column < columns
                        and labels[next_row][next_column] == 0
                        and image[next_row][next_column] >= threshold
                    ):
                        labels[next_row][next_column] = next_label
                        queue.append((next_row, next_column))

            components.append(
                {
                    "label": next_label,
                    "area": area,
                    "bbox": (min_row, min_column, max_row, max_column),
                }
            )
            next_label += 1

    return {"labels": labels, "components": components}


def _canonical_http_url(raw_url):
    if not isinstance(raw_url, str):
        return None
    parsed = urlsplit(raw_url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    port = parsed.port
    if port is not None and not (scheme == "http" and port == 80) and not (scheme == "https" and port == 443):
        host = f"{host}:{port}"

    segments = []
    for segment in parsed.path.split("/"):
        if not segment or segment == ".":
            continue
        if segment == "..":
            if segments:
                segments.pop()
            continue
        segments.append(segment)
    path = "/" + "/".join(segments)
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)), doseq=True)
    return urlunsplit((scheme, host, path, query, ""))


def discover_canonical_urls(seed_url, pages):
    seed = _canonical_http_url(seed_url)
    if seed is None:
        raise ValueError("seed_url must be absolute HTTP(S)")

    canonical_pages = defaultdict(list)
    for page_url, links in pages.items():
        canonical_page = _canonical_http_url(page_url)
        if canonical_page is None:
            continue
        canonical_pages[canonical_page].extend(links)

    queue = deque([seed])
    visited = {seed}
    discovery_order = []
    while queue:
        url = queue.popleft()
        discovery_order.append(url)
        for raw_link in canonical_pages[url]:
            canonical_link = _canonical_http_url(raw_link)
            if canonical_link is None or canonical_link in visited:
                continue
            visited.add(canonical_link)
            queue.append(canonical_link)
    return discovery_order
