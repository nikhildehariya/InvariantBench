"""Buggy LLM Baseline Implementation for Task 08.

Representative of typical frontier LLM outputs:
1. Treats ** as LEFT-associative (built via a while loop like * and +), making
   '2 ** 3 ** 2' evaluate as (2**3)**2 = 64 instead of the correct 512.
2. Uses naive recursive-descent structure that doesn't properly handle the
   interaction between unary minus and exponentiation.
"""


def evaluate(expression: str) -> float:
    pos = [0]

    def peek_char():
        while pos[0] < len(expression) and expression[pos[0]].isspace():
            pos[0] += 1
        if pos[0] >= len(expression):
            return None
        return expression[pos[0]]

    def consume_char():
        ch = expression[pos[0]]
        pos[0] += 1
        return ch

    def parse_number():
        start = pos[0]
        while pos[0] < len(expression) and (expression[pos[0]].isdigit() or expression[pos[0]] == "."):
            pos[0] += 1
        return float(expression[start:pos[0]])

    def parse_primary():
        ch = peek_char()
        if ch == "(":
            consume_char()
            val = parse_additive()
            if peek_char() == ")":
                consume_char()
            return val
        elif ch == "-":
            consume_char()
            return -parse_primary()
        else:
            return parse_number()

    # LLM TRAP: Uses a WHILE LOOP for **, making it left-associative!
    # 2**3**2 -> evaluates as (2**3)**2 = 8**2 = 64 instead of 2**(3**2) = 512
    def parse_exponent():
        left = parse_primary()
        while peek_char() == "*" and pos[0] + 1 < len(expression) and expression[pos[0] + 1] == "*":
            pos[0] += 2
            right = parse_primary()
            left = left ** right
        return left

    def parse_multiplicative():
        left = parse_exponent()
        while peek_char() in ("*", "/"):
            ch = peek_char()
            # Check it's not ** to avoid consuming first star of **
            if ch == "*" and pos[0] + 1 < len(expression) and expression[pos[0] + 1] == "*":
                break
            consume_char()
            right = parse_exponent()
            left = left * right if ch == "*" else left / right
        return left

    def parse_additive():
        left = parse_multiplicative()
        while peek_char() in ("+", "-"):
            ch = consume_char()
            right = parse_multiplicative()
            left = left + right if ch == "+" else left - right
        return left

    result = parse_additive()
    return result
