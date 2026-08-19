from collections import defaultdict, deque
from threading import Lock


def find_feasible_recipes(recipes, supplies):
    available = set(supplies)
    remaining = {}
    dependents = defaultdict(set)

    for recipe, requirements in recipes.items():
        unresolved = set(requirements) - available
        remaining[recipe] = unresolved
        for requirement in unresolved:
            dependents[requirement].add(recipe)

    ready = deque(recipe for recipe, unresolved in remaining.items() if not unresolved)
    feasible = set()

    while ready:
        recipe = ready.popleft()
        if recipe in feasible:
            continue
        feasible.add(recipe)
        for dependent in dependents[recipe]:
            remaining[dependent].discard(recipe)
            if not remaining[dependent]:
                ready.append(dependent)

    return [recipe for recipe in recipes if recipe in feasible]


def summarize_token_usage(events):
    final_events = {}
    for event in events:
        final_events[event["request_id"]] = event

    totals = defaultdict(lambda: [0, 0, 0, 0, 0])
    for event in final_events.values():
        if event["status"] != "completed":
            continue
        model_totals = totals[event["model"]]
        model_totals[0] += 1
        model_totals[1] += event["prompt_tokens"]
        model_totals[2] += event["cached_prompt_tokens"]
        model_totals[3] += event["completion_tokens"]
        model_totals[4] += (
            event["prompt_tokens"]
            - event["cached_prompt_tokens"]
            + event["completion_tokens"]
        )

    return [
        (model, *totals[model])
        for model in sorted(totals)
    ]


def _fnv1a_64(text):
    value = 14695981039346656037
    prime = 1099511628211
    mask = (1 << 64) - 1
    for byte in text.encode("utf-8"):
        value ^= byte
        value = (value * prime) & mask
    return value


def route_prompt_by_affinity(prompt, servers):
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")

    try:
        server_ids = list(servers)
    except TypeError as error:
        raise TypeError("servers must be iterable") from error
    if not server_ids:
        raise ValueError("at least one server is required")

    seen = set()
    best_server = None
    best_score = None
    for server in server_ids:
        if not isinstance(server, str):
            raise TypeError("server IDs must be strings")
        if not server:
            raise ValueError("server IDs must not be empty")
        if server in seen:
            raise ValueError("server IDs must be unique")
        seen.add(server)

        score = _fnv1a_64(server + "\0" + prompt)
        if best_score is None or score > best_score or (score == best_score and server < best_server):
            best_server = server
            best_score = score
    return best_server


def _canonical_template(template):
    if not isinstance(template, str):
        raise TypeError("template must be a string")

    text = template.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        stripped = line.strip(" \t")
        collapsed = []
        in_spacing = False
        for character in stripped:
            if character in " \t":
                if not in_spacing:
                    collapsed.append(" ")
                    in_spacing = True
            else:
                collapsed.append(character)
                in_spacing = False
        lines.append("".join(collapsed))

    start = 0
    end = len(lines)
    while start < end and not lines[start]:
        start += 1
    while end > start and not lines[end - 1]:
        end -= 1
    canonical = "\n".join(lines[start:end])
    if not canonical:
        raise ValueError("template must contain non-whitespace text")
    return canonical


class TemplateRegistry:
    def __init__(self):
        self._templates = []
        self._template_ids = {}
        self._lock = Lock()

    def register(self, template):
        canonical = _canonical_template(template)
        with self._lock:
            existing = self._template_ids.get(canonical)
            if existing is not None:
                return existing
            template_id = len(self._templates)
            self._templates.append(canonical)
            self._template_ids[canonical] = template_id
            return template_id

    def get(self, template_id):
        if type(template_id) is not int:
            raise TypeError("template_id must be an integer")
        with self._lock:
            if template_id < 0 or template_id >= len(self._templates):
                raise IndexError(template_id)
            return self._templates[template_id]

    def snapshot(self):
        with self._lock:
            return list(self._templates)
