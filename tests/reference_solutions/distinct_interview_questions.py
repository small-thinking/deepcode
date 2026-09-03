import heapq
import re
from bisect import bisect_left


def split_indexed_message(message, limit):
    if not isinstance(message, str):
        raise ValueError("message must be a string")
    if message == "":
        return []
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer")

    chunk_count = 1
    while True:
        width = max(2, len(str(chunk_count)))
        payload_capacity = limit - 1 - width
        if payload_capacity < 1:
            raise ValueError("limit cannot hold a payload and suffix")
        required = (len(message) + payload_capacity - 1) // payload_capacity
        if required == chunk_count:
            break
        chunk_count = required

    width = max(2, len(str(chunk_count)))
    payload_capacity = limit - 1 - width
    return [
        message[start : start + payload_capacity] + f"#{index:0{width}d}"
        for index, start in enumerate(range(0, len(message), payload_capacity), start=1)
    ]


def _validate_height(height):
    if isinstance(height, bool) or not isinstance(height, int) or height < 0:
        raise ValueError("height must be a nonnegative integer")


def generate_pascal(height):
    _validate_height(height)
    rows = []
    for row_index in range(height):
        if row_index == 0:
            rows.append([1])
            continue
        previous = rows[-1]
        rows.append([1] + [previous[index] + previous[index + 1] for index in range(len(previous) - 1)] + [1])
    return rows


def render_pascal(height):
    rows = generate_pascal(height)
    if not rows:
        return []
    cell_width = max(len(str(value)) for row in rows for value in row)
    formatted_rows = [" ".join(str(value).rjust(cell_width) for value in row) for row in rows]
    final_width = len(formatted_rows[-1])
    return [
        " " * ((final_width - len(row)) // 2) + row
        for row in formatted_rows
    ]


def find_first_haiku(sentence, syllables):
    if not isinstance(sentence, str) or not isinstance(syllables, dict):
        raise ValueError("sentence and syllables must be valid")

    counts = {}
    for word, count in syllables.items():
        if (
            not isinstance(word, str)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count <= 0
        ):
            raise ValueError("syllable counts must be positive integers")
        counts[word.lower()] = count

    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", sentence.lower())
    token_counts = []
    for token in tokens:
        if token not in counts:
            raise ValueError(f"unknown word: {token}")
        token_counts.append(counts[token])

    prefix = [0]
    for count in token_counts:
        prefix.append(prefix[-1] + count)
    end_for_sum = {total: index for index, total in enumerate(prefix)}

    for start in range(len(tokens)):
        first_end = end_for_sum.get(prefix[start] + 5)
        if first_end is None:
            continue
        second_end = end_for_sum.get(prefix[first_end] + 7)
        if second_end is None:
            continue
        third_end = end_for_sum.get(prefix[second_end] + 5)
        if third_end is not None:
            return [
                tokens[start:first_end],
                tokens[first_end:second_end],
                tokens[second_end:third_end],
            ]
    return None


class PagePermissions:
    _RANKS = {"none": 0, "view": 1, "comment": 2, "edit": 3}

    def __init__(self):
        self._parents = {}
        self._groups = {}
        self._user_grants = {}
        self._group_grants = {}

    @staticmethod
    def _require_identifier(value, name):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a nonempty string")

    def _require_page(self, page):
        self._require_identifier(page, "page")
        if page not in self._parents:
            raise ValueError("unknown page")

    def _require_role(self, role):
        if role not in self._RANKS:
            raise ValueError("unknown role")

    def add_page(self, page, parent=None):
        self._require_identifier(page, "page")
        if page in self._parents:
            raise ValueError("duplicate page")
        if parent is not None:
            self._require_page(parent)
        self._parents[page] = parent
        self._user_grants[page] = {}
        self._group_grants[page] = {}

    def add_user_to_group(self, user, group):
        self._require_identifier(user, "user")
        self._require_identifier(group, "group")
        self._groups.setdefault(group, set()).add(user)

    def grant_user(self, page, user, role):
        self._require_page(page)
        self._require_identifier(user, "user")
        self._require_role(role)
        self._user_grants[page][user] = role

    def grant_group(self, page, group, role):
        self._require_page(page)
        self._require_identifier(group, "group")
        self._require_role(role)
        self._groups.setdefault(group, set())
        self._group_grants[page][group] = role

    def _ancestors(self, page):
        while page is not None:
            yield page
            page = self._parents[page]

    def getUserPermissionForPage(self, page, user):
        self._require_page(page)
        self._require_identifier(user, "user")
        rank = 0
        for current_page in self._ancestors(page):
            rank = max(rank, self._RANKS[self._user_grants[current_page].get(user, "none")])
            for group, role in self._group_grants[current_page].items():
                if user in self._groups[group]:
                    rank = max(rank, self._RANKS[role])
        return next(role for role, value in self._RANKS.items() if value == rank)

    def getAllUsersWithPermissionForPage(self, page, min_role="view"):
        self._require_page(page)
        self._require_role(min_role)
        candidates = set()
        for current_page in self._ancestors(page):
            candidates.update(self._user_grants[current_page])
            for group in self._group_grants[current_page]:
                candidates.update(self._groups[group])
        minimum_rank = self._RANKS[min_role]
        return sorted(
            user
            for user in candidates
            if self._RANKS[self.getUserPermissionForPage(page, user)] >= minimum_rank
        )


class TextDocument:
    def __init__(self, initial_text=""):
        if not isinstance(initial_text, str):
            raise ValueError("initial_text must be a string")
        self._text = initial_text
        self._undo = []
        self._redo = []

    @staticmethod
    def _require_index(index, upper_bound):
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or index > upper_bound
        ):
            raise ValueError("invalid index")

    def _apply(self, action):
        kind, index, text = action
        if kind == "insert":
            self._text = self._text[:index] + text + self._text[index:]
        else:
            if self._text[index : index + len(text)] != text:
                raise RuntimeError("history no longer applies")
            self._text = self._text[:index] + self._text[index + len(text) :]

    def insert(self, index, text):
        self._require_index(index, len(self._text))
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        if not text:
            return
        action = ("insert", index, text)
        self._apply(action)
        self._undo.append(action)
        self._redo.clear()

    def delete(self, start, end):
        self._require_index(start, len(self._text))
        self._require_index(end, len(self._text))
        if end < start:
            raise ValueError("end precedes start")
        removed = self._text[start:end]
        if not removed:
            return ""
        action = ("delete", start, removed)
        self._apply(action)
        self._undo.append(action)
        self._redo.clear()
        return removed

    def undo(self):
        if not self._undo:
            return False
        action = self._undo.pop()
        kind, index, text = action
        inverse = ("delete", index, text) if kind == "insert" else ("insert", index, text)
        self._apply(inverse)
        self._redo.append(action)
        return True

    def redo(self):
        if not self._redo:
            return False
        action = self._redo.pop()
        self._apply(action)
        self._undo.append(action)
        return True

    def get_text(self):
        return self._text


class TableMaxIndex:
    def __init__(self):
        self._cells = {}
        self._table_heaps = {}
        self._global_heap = []

    @staticmethod
    def _require_name(value, name):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a nonempty string")

    @staticmethod
    def _require_value(value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("value must be an integer")

    def _live_table_max(self, table):
        heap = self._table_heaps[table]
        cells = self._cells[table]
        while heap:
            negative_value, cell = heap[0]
            value = -negative_value
            if cells.get(cell) == value:
                return value
            heapq.heappop(heap)
        return None

    def _record_global_candidate(self, table):
        value = self._live_table_max(table)
        if value is not None:
            heapq.heappush(self._global_heap, (-value, table))

    def set_cell(self, table, cell, value):
        self._require_name(table, "table")
        self._require_name(cell, "cell")
        self._require_value(value)
        self._cells.setdefault(table, {})[cell] = value
        self._table_heaps.setdefault(table, [])
        heapq.heappush(self._table_heaps[table], (-value, cell))
        self._record_global_candidate(table)

    def delete_cell(self, table, cell):
        self._require_name(table, "table")
        self._require_name(cell, "cell")
        if table not in self._cells or cell not in self._cells[table]:
            return False
        del self._cells[table][cell]
        self._record_global_candidate(table)
        return True

    def table_max(self, table):
        self._require_name(table, "table")
        if table not in self._cells:
            raise ValueError("unknown table")
        return self._live_table_max(table)

    def global_max(self):
        while self._global_heap:
            negative_value, table = self._global_heap[0]
            value = -negative_value
            if self._live_table_max(table) == value:
                return value
            heapq.heappop(self._global_heap)
        return None


class ResizableDeque:
    def __init__(self, initial_capacity=4):
        if (
            isinstance(initial_capacity, bool)
            or not isinstance(initial_capacity, int)
            or initial_capacity <= 0
        ):
            raise ValueError("initial_capacity must be a positive integer")
        self._data = [None] * initial_capacity
        self._head = 0
        self._size = 0

    @property
    def capacity(self):
        return len(self._data)

    def _grow(self):
        expanded = [None] * (2 * self.capacity)
        for index in range(self._size):
            expanded[index] = self._data[(self._head + index) % self.capacity]
        self._data = expanded
        self._head = 0

    def append_left(self, value):
        if self._size == self.capacity:
            self._grow()
        self._head = (self._head - 1) % self.capacity
        self._data[self._head] = value
        self._size += 1

    def append_right(self, value):
        if self._size == self.capacity:
            self._grow()
        index = (self._head + self._size) % self.capacity
        self._data[index] = value
        self._size += 1

    def pop_left(self):
        if not self._size:
            raise IndexError("pop from an empty deque")
        value = self._data[self._head]
        self._data[self._head] = None
        self._head = (self._head + 1) % self.capacity
        self._size -= 1
        return value

    def pop_right(self):
        if not self._size:
            raise IndexError("pop from an empty deque")
        index = (self._head + self._size - 1) % self.capacity
        value = self._data[index]
        self._data[index] = None
        self._size -= 1
        return value

    def to_list(self):
        return [self._data[(self._head + index) % self.capacity] for index in range(self._size)]

    def __len__(self):
        return self._size


class ConversationHistory:
    def __init__(self):
        self._messages = []
        self._prefix_tokens = [0]

    def add(self, role, content):
        if not isinstance(role, str) or not role or not isinstance(content, str):
            raise ValueError("role and content must be valid strings")
        self._messages.append((role, content))
        self._prefix_tokens.append(self._prefix_tokens[-1] + len(content.split()))

    def get_recent(self, max_tokens):
        if (
            isinstance(max_tokens, bool)
            or not isinstance(max_tokens, int)
            or max_tokens < 0
        ):
            raise ValueError("max_tokens must be a nonnegative integer")
        first_index = bisect_left(
            self._prefix_tokens,
            self._prefix_tokens[-1] - max_tokens,
        )
        return list(self._messages[first_index:])
