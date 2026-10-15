from bisect import bisect_left


def k_smallest_squares(nums, k):
    right = bisect_left(nums, 0)
    left = right - 1
    result = []
    for _ in range(k):
        if left < 0:
            value = nums[right]
            right += 1
        elif right >= len(nums) or -nums[left] <= nums[right]:
            value = nums[left]
            left -= 1
        else:
            value = nums[right]
            right += 1
        result.append(value * value)
    return result
