# Lexer for the Small-C interpreter.

class Token:
    def __init__(self, type_, value, line=1):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value})"


class Lexer:
    KEYWORDS = {
        "int", "char", "void", "while", "if", "else", "for", "do",
        "break", "continue", "return",
    }

    TWO_CHAR_TOKENS = {
        "==": "EQ",
        "!=": "NE",
        "<=": "LE",
        ">=": "GE",
        "&&": "AND",
        "||": "OR",
        "<<": "LSHIFT",
        ">>": "RSHIFT",
        "+=": "PLUS_ASSIGN",
        "-=": "MINUS_ASSIGN",
        "*=": "MUL_ASSIGN",
        "/=": "DIV_ASSIGN",
        "%=": "MOD_ASSIGN",
    }

    ONE_CHAR_TOKENS = {
        "+": "PLUS",
        "-": "MINUS",
        "*": "MUL",
        "/": "DIV",
        "%": "MOD",
        "=": "ASSIGN",
        "!": "NOT",
        "<": "LT",
        ">": "GT",
        "&": "BITAND",
        "|": "BITOR",
        "^": "BITXOR",
        "~": "BITNOT",
        "(": "LPAREN",
        ")": "RPAREN",
        "{": "LBRACE",
        "}": "RBRACE",
        "[": "LBRACKET",
        "]": "RBRACKET",
        ";": "SEMICOLON",
        ",": "COMMA",
    }

    ESCAPES = {
        "n": "\n",
        "t": "\t",
        "r": "\r",
        "0": "\0",
        "\\": "\\",
        '"': '"',
        "'": "'",
    }

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.current_char = self.text[0] if self.text else None

    def advance(self):
        if self.current_char == "\n":
            self.line += 1
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        peek_pos = self.pos + 1
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        if self.current_char == "/" and self.peek() == "/":
            while self.current_char is not None and self.current_char != "\n":
                self.advance()
        elif self.current_char == "/" and self.peek() == "*":
            self.advance()
            self.advance()
            while self.current_char is not None:
                if self.current_char == "*" and self.peek() == "/":
                    self.advance()
                    self.advance()
                    return
                self.advance()
            raise ValueError("Unterminated block comment")

    def read_number(self):
        start_line = self.line
        result = ""
        if self.current_char == "0" and self.peek() in ("x", "X"):
            result += self.current_char
            self.advance()
            result += self.current_char
            self.advance()
            while self.current_char is not None and self.current_char.lower() in "0123456789abcdef":
                result += self.current_char
                self.advance()
            return Token("NUMBER", int(result, 16), start_line)
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return Token("NUMBER", int(result), start_line)

    def read_identifier(self):
        start_line = self.line
        result = ""
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == "_"):
            result += self.current_char
            self.advance()
        return Token("KEYWORD" if result in self.KEYWORDS else "IDENTIFIER", result, start_line)

    def read_escaped_char(self):
        if self.current_char != "\\":
            ch = self.current_char
            self.advance()
            return ch
        self.advance()
        if self.current_char is None:
            raise ValueError("Invalid escape sequence")
        ch = self.ESCAPES.get(self.current_char, self.current_char)
        self.advance()
        return ch

    def read_string(self):
        start_line = self.line
        result = ""
        self.advance()
        while self.current_char is not None and self.current_char != '"':
            result += self.read_escaped_char()
        if self.current_char != '"':
            raise ValueError("Unterminated string literal")
        self.advance()
        return Token("STRING", result, start_line)

    def read_char(self):
        start_line = self.line
        self.advance()
        ch = self.read_escaped_char()
        if self.current_char != "'":
            raise ValueError("Invalid character literal")
        self.advance()
        return Token("NUMBER", ord(ch), start_line)

    def tokenize(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            if self.current_char == "/" and self.peek() in ("/", "*"):
                self.skip_comment()
                continue
            if self.current_char.isdigit():
                tokens.append(self.read_number())
                continue
            if self.current_char == '"':
                tokens.append(self.read_string())
                continue
            if self.current_char == "'":
                tokens.append(self.read_char())
                continue
            if self.current_char.isalpha() or self.current_char == "_":
                tokens.append(self.read_identifier())
                continue

            pair = self.current_char + (self.peek() or "")
            if pair in self.TWO_CHAR_TOKENS:
                tokens.append(Token(self.TWO_CHAR_TOKENS[pair], pair, self.line))
                self.advance()
                self.advance()
                continue
            if self.current_char in self.ONE_CHAR_TOKENS:
                tokens.append(Token(self.ONE_CHAR_TOKENS[self.current_char], self.current_char, self.line))
                self.advance()
                continue
            raise ValueError(f"Invalid character on line {self.line}: {self.current_char}")
        tokens.append(Token("EOF", None, self.line))
        return tokens
