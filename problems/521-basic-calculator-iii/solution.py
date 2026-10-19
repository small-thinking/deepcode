def _parse_expression(s, decimal):
    position = 0

    def peek():
        nonlocal position
        while position < len(s) and s[position] == " ":
            position += 1
        return s[position] if position < len(s) else None

    def factor():
        nonlocal position
        char = peek()
        if char in ("+", "-"):
            position += 1
            value = factor()
            return value if char == "+" else -value
        if char == "(":
            position += 1
            value = expression()
            if peek() != ")":
                raise ValueError("Missing closing parenthesis")
            position += 1
            return value

        start = position
        while position < len(s) and "0" <= s[position] <= "9":
            position += 1
        if start == position:
            raise ValueError("Expected a number or parenthesized expression")
        if decimal and position < len(s) and s[position] == ".":
            position += 1
            fraction_start = position
            while position < len(s) and "0" <= s[position] <= "9":
                position += 1
            if position == fraction_start:
                raise ValueError("Expected digits after decimal point")
        token = s[start:position]
        return float(token) if decimal else int(token)

    def term():
        nonlocal position
        value = factor()
        while peek() in ("*", "/"):
            operation = s[position]
            position += 1
            right = factor()
            if operation == "*":
                value *= right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                if decimal:
                    value /= right
                else:
                    quotient = abs(value) // abs(right)
                    value = -quotient if (value < 0) != (right < 0) else quotient
        return value

    def expression():
        nonlocal position
        value = term()
        while peek() in ("+", "-"):
            operation = s[position]
            position += 1
            right = term()
            value = value + right if operation == "+" else value - right
        return value

    result = expression()
    if peek() is not None:
        raise ValueError("Unexpected trailing token")
    return result


def calculate_iii(s):
    return _parse_expression(s, decimal=False)


def calculate_decimal(s):
    return _parse_expression(s, decimal=True)
