from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    id: object
    candies: int
    keys: tuple
    children: tuple
    is_open: bool = False


def get_max_candies(boxes, initially_open, key_to_box):
    catalog = {box.id: box for box in boxes}
    discovered = {box_id for box_id in initially_open if box_id in catalog}
    unlocked = set(discovered)
    unlocked.update(box.id for box in boxes if box.is_open)

    pending = deque()
    queued = set()
    opened = set()
    total = 0

    def enqueue_available():
        for box_id in discovered & unlocked:
            if box_id not in opened and box_id not in queued:
                pending.append(box_id)
                queued.add(box_id)

    enqueue_available()
    while pending:
        box_id = pending.popleft()
        queued.remove(box_id)
        if box_id in opened:
            continue

        box = catalog[box_id]
        opened.add(box_id)
        total += box.candies

        for key in box.keys:
            target = key_to_box.get(key)
            if target in catalog:
                unlocked.add(target)
        for child_id in box.children:
            if child_id in catalog:
                discovered.add(child_id)

        enqueue_available()

    return total
