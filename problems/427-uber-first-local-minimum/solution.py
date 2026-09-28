def solution(nums):
    for i, value in enumerate(nums):
        if i > 0 and value >= nums[i - 1]:
            continue
        if i + 1 < len(nums) and value >= nums[i + 1]:
            continue
        return i
    return -1
