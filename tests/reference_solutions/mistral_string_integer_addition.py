def add_decimal_strings(a, b):
    i = len(a) - 1
    j = len(b) - 1
    carry = 0
    reversed_digits = []

    while i >= 0 or j >= 0 or carry:
        left_digit = ord(a[i]) - ord("0") if i >= 0 else 0
        right_digit = ord(b[j]) - ord("0") if j >= 0 else 0
        carry, digit = divmod(left_digit + right_digit + carry, 10)
        reversed_digits.append(chr(ord("0") + digit))
        i -= 1
        j -= 1

    result = "".join(reversed(reversed_digits))
    return result.lstrip("0") or "0"
