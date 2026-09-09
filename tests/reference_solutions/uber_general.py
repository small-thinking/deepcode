import math
from bisect import bisect_left
from collections import deque


def minimize_convex(f, a, b, tol=1e-6):
    if b-a <= tol:
        return (a+b)/2
    ratio = (math.sqrt(5)-1)/2
    x, y = b-ratio*(b-a), a+ratio*(b-a)
    fx, fy = f(x), f(y)
    while b-a > tol:
        if fx <= fy:
            b, y, fy = y, x, fx
            if b-a <= tol:
                break
            x = b-ratio*(b-a)
            fx = f(x)
        else:
            a, x, fx = x, y, fy
            if b-a <= tol:
                break
            y = a+ratio*(b-a)
            fy = f(y)
    return (a+b)/2


def longest_bounded_subarray(nums, limit):
    low, high = deque(), deque()
    left = best = 0
    for right, value in enumerate(nums):
        while low and nums[low[-1]] > value:
            low.pop()
        while high and nums[high[-1]] < value:
            high.pop()
        low.append(right)
        high.append(right)
        while nums[high[0]]-nums[low[0]] > limit:
            if low[0] == left:
                low.popleft()
            if high[0] == left:
                high.popleft()
            left += 1
        best = max(best, right-left+1)
    return best


def find_robots(grid, query):
    if not grid or not grid[0]:
        return []
    rows, cols = len(grid), len(grid[0])
    distances = [[[0]*4 for _ in range(cols)] for _ in range(rows)]
    for r in range(rows):
        blocker = -1
        for c in range(cols):
            if grid[r][c] == 'X':
                blocker = c
            distances[r][c][0] = c-blocker
        blocker = cols
        for c in range(cols-1,-1,-1):
            if grid[r][c] == 'X':
                blocker = c
            distances[r][c][3] = blocker-c
    for c in range(cols):
        blocker = -1
        for r in range(rows):
            if grid[r][c] == 'X':
                blocker = r
            distances[r][c][1] = r-blocker
        blocker = rows
        for r in range(rows-1,-1,-1):
            if grid[r][c] == 'X':
                blocker = r
            distances[r][c][2] = blocker-r
    return [[r,c] for r in range(rows) for c in range(cols)
            if grid[r][c] == 'O' and distances[r][c] == list(query)]


def sorted_squares(nums):
    out = [0]*len(nums)
    left, right = 0, len(nums)-1
    for i in range(len(nums)-1,-1,-1):
        if abs(nums[left]) > abs(nums[right]):
            out[i] = nums[left]**2
            left += 1
        else:
            out[i] = nums[right]**2
            right -= 1
    return out


def kth_smallest_square(nums, k):
    right = bisect_left(nums, 0)
    left = right-1
    for _ in range(k):
        if right == len(nums) or (left >= 0 and abs(nums[left]) <= abs(nums[right])):
            value = nums[left]**2
            left -= 1
        else:
            value = nums[right]**2
            right += 1
    return value


def count_keypad_combinations(digits):
    if not digits:
        return 0
    count = 1
    for digit in digits:
        if digit not in '23456789':
            raise ValueError('invalid keypad digit')
        count *= 4 if digit in '79' else 3
    return count


def count_islands(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    seen = set()
    count = 0
    for r in range(rows):
        for c in range(cols):
            if not grid[r][c] or (r,c) in seen:
                continue
            count += 1
            seen.add((r,c))
            stack = [(r,c)]
            while stack:
                x,y = stack.pop()
                for a,b in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                    if 0 <= a < rows and 0 <= b < cols and grid[a][b] and (a,b) not in seen:
                        seen.add((a,b))
                        stack.append((a,b))
    return count


def streaming_islands(rows, cols, positions):
    parent, size = {}, {}
    count = 0
    result = []
    def find(x):
        while x != parent[x]:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for r,c in positions:
        cell = (r,c)
        if cell not in parent:
            parent[cell], size[cell] = cell, 1
            count += 1
            for other in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if other not in parent:
                    continue
                a,b = find(cell), find(other)
                if a == b:
                    continue
                if size[a] < size[b]:
                    a,b = b,a
                parent[b] = a
                size[a] += size[b]
                count -= 1
        result.append(count)
    return result
