def calculate_ii(s):
    total = 0
    term = 0
    number = 0
    operation = "+"

    for char in s + "+":
        if char == " ":
            continue
        if char.isdigit():
            number = number * 10 + int(char)
            continue

        if operation == "+":
            total += term
            term = number
        elif operation == "-":
            total += term
            term = -number
        elif operation == "*":
            term *= number
        else:
            # Python // rounds down; the task requires truncation toward zero.
            quotient = abs(term) // number
            term = -quotient if term < 0 else quotient
        operation = char
        number = 0

    return total + term
