class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def tennis_game_score(points):
    score_a = sum(point == "A" for point in points)
    score_b = len(points) - score_a

    if max(score_a, score_b) >= 4 and abs(score_a - score_b) >= 2:
        return "Game A" if score_a > score_b else "Game B"
    if score_a >= 3 and score_b >= 3:
        if score_a == score_b:
            return "Deuce"
        return "Advantage A" if score_a > score_b else "Advantage B"

    labels = ("Love", "15", "30", "40")
    if score_a == score_b:
        return f"{labels[score_a]}-All"
    return f"{labels[score_a]}-{labels[score_b]}"


def tennis_score(points):
    return tennis_game_score(points)


def odd_even_list(head):
    if head is None or head.next is None:
        return head

    odd = head
    even = head.next
    even_head = even
    while even is not None and even.next is not None:
        odd.next = even.next
        odd = odd.next
        even.next = odd.next
        even = even.next
    odd.next = even_head
    return head


def oddEvenList(head):
    return odd_even_list(head)


def shortest_palindrome_prefix(s):
    sequence = list(s) + [object()] + list(reversed(s))
    lps = [0] * len(sequence)
    matched = 0
    for index in range(1, len(sequence)):
        while matched and sequence[index] != sequence[matched]:
            matched = lps[matched - 1]
        if sequence[index] == sequence[matched]:
            matched += 1
        lps[index] = matched

    palindrome_prefix_length = lps[-1]
    return s[palindrome_prefix_length:][::-1] + s
