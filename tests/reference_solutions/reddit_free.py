import heapq


def process_queries(stage, logs, queries):
    rosters = {}

    for line in logs.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if not parts or not parts[0]:
            continue

        if stage == 1:
            target, action, _actor, timestamp = parts
            community = ""
        else:
            community, target, action, _actor, timestamp = parts

        roster = rosters.setdefault(community, {})
        if action == "remove":
            roster.pop(target, None)
        else:
            roster[target] = int(timestamp)

    answers = []
    for query in queries:
        if query[0] == "can":
            if stage == 1:
                actor, target = query[1:]
                roster = rosters.get("", {})
            else:
                community, actor, target = query[1:]
                roster = rosters.get(community, {})
            answers.append(
                actor != target
                and actor in roster
                and target in roster
                and roster[actor] < roster[target]
            )
        else:
            community = "" if stage == 1 else query[1]
            roster = rosters.get(community, {})
            answers.append([name for name, _time in sorted(roster.items(), key=lambda item: item[1])])

    return answers


def build_children(relations):
    children = {}
    parent = {}
    appearance_order = []

    for row in relations:
        manager, *reports = row
        if manager not in children:
            children[manager] = []
            appearance_order.append(manager)
        for report in reports:
            if report not in children:
                children[report] = []
                appearance_order.append(report)
            children[manager].append(report)
            parent[report] = manager

    root = next(name for name in appearance_order if name not in parent)
    return children, root


def render_full_chain(relations):
    children, root = build_children(relations)
    lines = []

    def visit(name, depth):
        lines.append("...." * depth + name)
        for report in children[name]:
            visit(report, depth + 1)

    visit(root, 0)
    return "\n".join(lines)


def all_skip_level_pairs(relations):
    children, root = build_children(relations)
    pairs = []

    def visit(name):
        for report in children[name]:
            for grandchild in children[report]:
                pairs.append((name, grandchild))
            visit(report)

    visit(root)
    return pairs


def render_chain_for(relations, target):
    children, root = build_children(relations)
    parent = {report: manager for manager, reports in children.items() for report in reports}
    path = [target]
    while path[-1] != root:
        path.append(parent[path[-1]])
    path.reverse()

    lines = ["...." * depth + name for depth, name in enumerate(path)]

    def visit(name, depth):
        lines.append("...." * depth + name)
        for report in children[name]:
            visit(report, depth + 1)

    for report in children[target]:
        visit(report, len(path))
    return "\n".join(lines)


def lowest_common_manager(relations, employee1, employee2):
    children, _root = build_children(relations)
    parent = {report: manager for manager, reports in children.items() for report in reports}
    ancestors = {employee1}
    while employee1 in parent:
        employee1 = parent[employee1]
        ancestors.add(employee1)
    while employee2 not in ancestors:
        employee2 = parent[employee2]
    return employee2


class TrieNode:
    def __init__(self):
        self.children = {}
        self.word = None


class Solution:
    def findWords(self, board, words):
        root = TrieNode()
        for word in words:
            node = root
            for letter in word:
                node = node.children.setdefault(letter, TrieNode())
            node.word = word

        found = []
        rows, cols = len(board), len(board[0])

        def search(row, col, parent):
            letter = board[row][col]
            node = parent.children[letter]
            if node.word is not None:
                found.append(node.word)
                node.word = None

            board[row][col] = "#"
            for row_delta, col_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_row, next_col = row + row_delta, col + col_delta
                if (
                    0 <= next_row < rows
                    and 0 <= next_col < cols
                    and board[next_row][next_col] in node.children
                ):
                    search(next_row, next_col, node)
            board[row][col] = letter

            if not node.children and node.word is None:
                parent.children.pop(letter)

        for row in range(rows):
            for col in range(cols):
                if board[row][col] in root.children:
                    search(row, col, root)
        return found


class Message:
    def __init__(self, id, content=""):
        self.id = id
        self.content = content

    def __repr__(self):
        return f"Message(id={self.id})"


def get_chat_messages(message_id):
    return []


def merge_windows(ids):
    windows = [get_chat_messages(message_id) for message_id in ids]
    heap = []
    for window_index, window in enumerate(windows):
        if window:
            message = window[0]
            heapq.heappush(heap, (message.id, window_index, 0, message))

    merged = []
    previous_id = None
    while heap:
        message_id, window_index, item_index, message = heapq.heappop(heap)
        if message_id != previous_id:
            merged.append(message)
            previous_id = message_id

        next_index = item_index + 1
        window = windows[window_index]
        if next_index < len(window):
            next_message = window[next_index]
            heapq.heappush(heap, (next_message.id, window_index, next_index, next_message))

    return merged
