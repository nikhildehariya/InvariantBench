"""Ground Truth Reference Implementation for Task 08: Recursive Descent Parser."""

from typing import List, Tuple, Optional


class TokenType:
    NUMBER = "NUMBER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    STARSTAR = "STARSTAR"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


class Token:
    def __init__(self, kind: str, value):
        self.kind = kind
        self.value = value


def tokenize(expr: str) -> List[Token]:
    tokens = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isspace():
            i += 1
        elif ch.isdigit() or ch == ".":
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == "."):
                j += 1
            tokens.append(Token(TokenType.NUMBER, float(expr[i:j])))
            i = j
        elif ch == "+" :
            tokens.append(Token(TokenType.PLUS, "+"))
            i += 1
        elif ch == "-":
            tokens.append(Token(TokenType.MINUS, "-"))
            i += 1
        elif ch == "*":
            if i + 1 < len(expr) and expr[i + 1] == "*":
                tokens.append(Token(TokenType.STARSTAR, "**"))
                i += 2
            else:
                tokens.append(Token(TokenType.STAR, "*"))
                i += 1
        elif ch == "/":
            tokens.append(Token(TokenType.SLASH, "/"))
            i += 1
        elif ch == "(":
            tokens.append(Token(TokenType.LPAREN, "("))
            i += 1
        elif ch == ")":
            tokens.append(Token(TokenType.RPAREN, ")"))
            i += 1
        else:
            raise ValueError(f"Unexpected character: {ch!r}")
    tokens.append(Token(TokenType.EOF, None))
    return tokens


class Parser:
    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _consume(self, kind: Optional[str] = None) -> Token:
        tok = self._tokens[self._pos]
        if kind and tok.kind != kind:
            raise ValueError(f"Expected {kind}, got {tok.kind}")
        self._pos += 1
        return tok

    def parse_expression(self) -> float:
        result = self._parse_additive()
        if self._peek().kind != TokenType.EOF:
            raise ValueError(f"Unexpected token: {self._peek().kind}")
        return result

    def _parse_additive(self) -> float:
        left = self._parse_multiplicative()
        while self._peek().kind in (TokenType.PLUS, TokenType.MINUS):
            op = self._consume().kind
            right = self._parse_multiplicative()
            left = left + right if op == TokenType.PLUS else left - right
        return left

    def _parse_multiplicative(self) -> float:
        left = self._parse_unary()
        while self._peek().kind in (TokenType.STAR, TokenType.SLASH):
            op = self._consume().kind
            right = self._parse_unary()
            left = left * right if op == TokenType.STAR else left / right
        return left

    def _parse_unary(self) -> float:
        if self._peek().kind == TokenType.MINUS:
            self._consume()
            return -self._parse_unary()
        return self._parse_exponent()

    def _parse_exponent(self) -> float:
        """Right-associative: 2**3**2 = 2**(3**2) = 512, NOT (2**3)**2 = 64."""
        base = self._parse_primary()
        if self._peek().kind == TokenType.STARSTAR:
            self._consume()
            # Right-associativity: recurse into _parse_exponent (NOT _parse_primary)
            exponent = self._parse_unary()
            return base ** exponent
        return base

    def _parse_primary(self) -> float:
        tok = self._peek()
        if tok.kind == TokenType.NUMBER:
            self._consume()
            return tok.value
        elif tok.kind == TokenType.LPAREN:
            self._consume()
            val = self._parse_additive()
            self._consume(TokenType.RPAREN)
            return val
        else:
            raise ValueError(f"Unexpected token in primary: {tok.kind!r}")


def evaluate(expression: str) -> float:
    tokens = tokenize(expression)
    parser = Parser(tokens)
    return parser.parse_expression()
