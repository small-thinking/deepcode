from dataclasses import dataclass


class InMemoryUnixFileSystem:
    def __init__(self):
        self.root = {"kind": "dir", "children": {}}

    def _parts(self, path):
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("path must be absolute")
        return [part for part in path.split("/") if part]

    def _locate(self, path):
        node = self.root
        for part in self._parts(path):
            node = node["children"].get(part)
            if node is None:
                raise ValueError("path does not exist")
        return node

    def _parent(self, path):
        parts = self._parts(path)
        if not parts:
            return None, None
        node = self.root
        for part in parts[:-1]:
            node = node["children"].get(part)
            if node is None or node["kind"] != "dir":
                return None, None
        return node, parts[-1]

    def touch(self, path):
        parent, name = self._parent(path)
        if parent is None:
            raise ValueError("parent must exist")
        existing = parent["children"].get(name)
        if existing is None:
            parent["children"][name] = {"kind": "file"}
        elif existing["kind"] != "file":
            raise ValueError("a directory already uses this name")

    def mkdir(self, path):
        node = self.root
        for part in self._parts(path):
            child = node["children"].get(part)
            if child is None:
                child = {"kind": "dir", "children": {}}
                node["children"][part] = child
            if child["kind"] != "dir":
                raise ValueError("a file already uses this path component")
            node = child

    def ls(self, path):
        node = self._locate(path)
        if node["kind"] == "file":
            return [self._parts(path)[-1]]
        return sorted(node["children"])

    def rm(self, path):
        parent, name = self._parent(path)
        if parent is None:
            return False
        node = parent["children"].get(name)
        if node is None or node["kind"] != "file":
            return False
        del parent["children"][name]
        return True

    def rmdir(self, path):
        parent, name = self._parent(path)
        if parent is None:
            return False
        node = parent["children"].get(name)
        if node is None or node["kind"] != "dir" or node["children"]:
            return False
        del parent["children"][name]
        return True


class TextEditor:
    def __init__(self):
        self.left = ""
        self.right = ""

    def addText(self, text):
        self.left += text

    def deleteText(self, k):
        removed = min(k, len(self.left))
        self.left = self.left[:-removed] if removed else self.left
        return removed

    def cursorLeft(self, k):
        moved = min(k, len(self.left))
        if moved:
            self.right = self.left[-moved:] + self.right
            self.left = self.left[:-moved]
        return self.left[-10:]

    def cursorRight(self, k):
        moved = min(k, len(self.right))
        self.left += self.right[:moved]
        self.right = self.right[moved:]
        return self.left[-10:]


@dataclass
class CitationResult:
    tagged_document: str
    counts: dict[int, int]
    citations: list[list[int]]


def highlight_with_citations(document, sources):
    def is_word_char(char):
        return char.isalnum() or char == "_"

    matches = []
    counts = {index: 0 for index in range(len(sources))}
    for source_id, source in enumerate(sources):
        start = document.find(source)
        while start != -1:
            end = start + len(source)
            left_ok = start == 0 or not is_word_char(document[start - 1])
            right_ok = end == len(document) or not is_word_char(document[end])
            if left_ok and right_ok:
                matches.append((start, end, source_id))
                counts[source_id] += 1
            start = document.find(source, start + 1)

    intervals = []
    for start, end, source_id in sorted(matches):
        if not intervals:
            intervals.append([start, end, {source_id}])
            continue
        current = intervals[-1]
        whitespace_adjacent = document[current[1]:start].isspace()
        if start <= current[1] or whitespace_adjacent:
            current[1] = max(current[1], end)
            current[2].add(source_id)
        else:
            intervals.append([start, end, {source_id}])

    parts = []
    cursor = 0
    citations = []
    for start, end, source_ids in intervals:
        ordered = sorted(source_ids, key=lambda source_id: (-counts[source_id], source_id))
        parts.extend((document[cursor:start], "<yellow>", document[start:end], "</yellow>"))
        parts.extend(f"[{source_id}]" for source_id in ordered)
        citations.append(ordered)
        cursor = end
    parts.append(document[cursor:])
    return CitationResult("".join(parts), counts, citations)
