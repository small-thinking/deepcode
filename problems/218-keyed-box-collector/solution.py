from collections import deque


class Solution:
    def maxCandies(self, status, candies, keys, containedBoxes, initialBoxes):
        n = len(status)
        can_open = list(status)
        possessed = [False] * n
        scheduled = [False] * n
        pending = deque()

        def enqueue(box):
            if possessed[box] and can_open[box] and not scheduled[box]:
                scheduled[box] = True
                pending.append(box)

        for box in initialBoxes:
            possessed[box] = True
            enqueue(box)

        total = 0
        while pending:
            box = pending.popleft()
            total += candies[box]
            for target in keys[box]:
                can_open[target] = True
                enqueue(target)
            for child in containedBoxes[box]:
                possessed[child] = True
                enqueue(child)
        return total
