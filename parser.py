# Recursive-descent parser for Small-C.

from lexer import Token


class AST:
    pass


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
        self.line = token.line


class String(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
        self.line = token.line


class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
        self.line = token.line


class ArrayAccess(AST):
    def __init__(self, name, index, line):
        self.name = name
        self.index = index
        self.line = line


class UnaryOp(AST):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr
        self.line = op.line


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
        self.line = op.line


class Assign(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
        self.line = op.line


class Declaration(AST):
    def __init__(self, type_, name, initializer=None, array_size=None, pointer=False, line=1):
        self.type = type_
        self.name = name
        self.initializer = initializer
        self.array_size = array_size
        self.pointer = pointer
        self.line = line


class If(AST):
    def __init__(self, condition, then_branch, else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.line = condition.line


class While(AST):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
        self.line = condition.line


class For(AST):
    def __init__(self, init, condition, update, body, line):
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body
        self.line = line


class DoWhile(AST):
    def __init__(self, body, condition, line):
        self.body = body
        self.condition = condition
        self.line = line


class Break(AST):
    def __init__(self, line):
        self.line = line


class Continue(AST):
    def __init__(self, line):
        self.line = line


class Compound(AST):
    def __init__(self, statements):
        self.statements = statements
        self.line = statements[0].line if statements else 1


class FunctionDef(AST):
    def __init__(self, return_type, name, params, body, line):
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body
        self.line = line


class FunctionCall(AST):
    def __init__(self, name, args, line):
        self.name = name
        self.args = args
        self.line = line


class Return(AST):
    def __init__(self, expr=None, line=1):
        self.expr = expr
        self.line = line


class Parser:
    ASSIGN_OPS = ("ASSIGN", "PLUS_ASSIGN", "MINUS_ASSIGN", "MUL_ASSIGN", "DIV_ASSIGN", "MOD_ASSIGN")

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else None

    def eat(self, token_type):
        if self.current_token.type != token_type:
            raise ValueError(
                f"Syntax error on line {self.current_token.line}: "
                f"expected {token_type}, got {self.current_token.type}"
            )
        token = self.current_token
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        return token

    def parse(self):
        statements = []
        while self.current_token and self.current_token.type != "EOF":
            statements.append(self.statement())
        self.eat("EOF")
        return Compound(statements)

    def statement(self):
        token = self.current_token
        if token.type == "KEYWORD" and token.value in ("int", "char", "void"):
            return self.declaration_or_function()
        if token.type == "KEYWORD" and token.value == "return":
            return self.return_statement()
        if token.type == "KEYWORD" and token.value == "if":
            return self.if_statement()
        if token.type == "KEYWORD" and token.value == "while":
            return self.while_statement()
        if token.type == "KEYWORD" and token.value == "for":
            return self.for_statement()
        if token.type == "KEYWORD" and token.value == "do":
            return self.do_while_statement()
        if token.type == "KEYWORD" and token.value == "break":
            line = self.eat("KEYWORD").line
            self.eat("SEMICOLON")
            return Break(line)
        if token.type == "KEYWORD" and token.value == "continue":
            line = self.eat("KEYWORD").line
            self.eat("SEMICOLON")
            return Continue(line)
        if token.type == "LBRACE":
            return self.compound_statement()
        node = self.assignment_or_call()
        self.eat("SEMICOLON")
        return node

    def declaration_or_function(self, consume_semicolon=True):
        type_token = self.eat("KEYWORD")
        pointer = False
        if self.current_token.type == "MUL":
            pointer = True
            self.eat("MUL")
        name_token = self.eat("IDENTIFIER")
        if self.current_token.type == "LPAREN":
            return self.function_definition(type_token.value, name_token)
        array_size = None
        if self.current_token.type == "LBRACKET":
            self.eat("LBRACKET")
            array_size = self.logic_or()
            self.eat("RBRACKET")
        initializer = None
        if self.current_token.type == "ASSIGN":
            self.eat("ASSIGN")
            initializer = self.logic_or()
        if consume_semicolon:
            self.eat("SEMICOLON")
        return Declaration(type_token.value, name_token.value, initializer, array_size, pointer, name_token.line)

    def function_definition(self, return_type, name_token):
        self.eat("LPAREN")
        params = []
        if self.current_token.type != "RPAREN":
            while True:
                type_token = self.eat("KEYWORD")
                pointer = False
                if self.current_token.type == "MUL":
                    pointer = True
                    self.eat("MUL")
                param_name = self.eat("IDENTIFIER")
                params.append((type_token.value, param_name.value, pointer))
                if self.current_token.type == "RPAREN":
                    break
                self.eat("COMMA")
        self.eat("RPAREN")
        body = self.compound_statement()
        return FunctionDef(return_type, name_token.value, params, body, name_token.line)

    def return_statement(self):
        line = self.eat("KEYWORD").line
        expr = None if self.current_token.type == "SEMICOLON" else self.logic_or()
        self.eat("SEMICOLON")
        return Return(expr, line)

    def if_statement(self):
        self.eat("KEYWORD")
        self.eat("LPAREN")
        condition = self.logic_or()
        self.eat("RPAREN")
        then_branch = self.statement()
        else_branch = None
        if self.current_token.type == "KEYWORD" and self.current_token.value == "else":
            self.eat("KEYWORD")
            else_branch = self.statement()
        return If(condition, then_branch, else_branch)

    def while_statement(self):
        self.eat("KEYWORD")
        self.eat("LPAREN")
        condition = self.logic_or()
        self.eat("RPAREN")
        return While(condition, self.statement())

    def for_statement(self):
        line = self.eat("KEYWORD").line
        self.eat("LPAREN")
        init = None
        if self.current_token.type != "SEMICOLON":
            if self.current_token.type == "KEYWORD":
                init = self.declaration_or_function(consume_semicolon=False)
            else:
                init = self.assignment_or_call()
        self.eat("SEMICOLON")
        condition = None if self.current_token.type == "SEMICOLON" else self.logic_or()
        self.eat("SEMICOLON")
        update = None if self.current_token.type == "RPAREN" else self.assignment_or_call()
        self.eat("RPAREN")
        return For(init, condition, update, self.statement(), line)

    def do_while_statement(self):
        line = self.eat("KEYWORD").line
        body = self.statement()
        if not (self.current_token.type == "KEYWORD" and self.current_token.value == "while"):
            raise ValueError(f"Syntax error on line {self.current_token.line}: expected while")
        self.eat("KEYWORD")
        self.eat("LPAREN")
        condition = self.logic_or()
        self.eat("RPAREN")
        self.eat("SEMICOLON")
        return DoWhile(body, condition, line)

    def compound_statement(self):
        self.eat("LBRACE")
        statements = []
        while self.current_token.type != "RBRACE":
            statements.append(self.statement())
        self.eat("RBRACE")
        return Compound(statements)

    def assignment_or_call(self):
        left = self.primary()
        if isinstance(left, FunctionCall):
            return left
        if self.current_token.type in self.ASSIGN_OPS:
            op = self.current_token
            self.eat(op.type)
            return Assign(left, op, self.logic_or())
        return left

    def primary(self):
        token = self.current_token
        if token.type == "NUMBER":
            return Num(self.eat("NUMBER"))
        if token.type == "STRING":
            return String(self.eat("STRING"))
        if token.type == "IDENTIFIER":
            ident = self.eat("IDENTIFIER")
            if self.current_token.type == "LPAREN":
                return self.function_call_expr(ident)
            if self.current_token.type == "LBRACKET":
                self.eat("LBRACKET")
                index = self.logic_or()
                self.eat("RBRACKET")
                return ArrayAccess(ident.value, index, ident.line)
            return Var(ident)
        if token.type == "LPAREN":
            self.eat("LPAREN")
            node = self.logic_or()
            self.eat("RPAREN")
            return node
        if token.type in ("PLUS", "MINUS", "NOT", "BITNOT", "BITAND", "MUL"):
            op = self.current_token
            self.eat(op.type)
            return UnaryOp(op, self.primary())
        raise ValueError(f"Syntax error on line {token.line}: unexpected {token.type}")

    def function_call_expr(self, ident):
        self.eat("LPAREN")
        args = []
        if self.current_token.type != "RPAREN":
            while True:
                args.append(self.logic_or())
                if self.current_token.type == "RPAREN":
                    break
                self.eat("COMMA")
        self.eat("RPAREN")
        return FunctionCall(ident.value, args, ident.line)

    def multiplicative(self):
        node = self.primary()
        while self.current_token.type in ("MUL", "DIV", "MOD"):
            op = self.current_token
            self.eat(op.type)
            node = BinOp(node, op, self.primary())
        return node

    def additive(self):
        node = self.multiplicative()
        while self.current_token.type in ("PLUS", "MINUS"):
            op = self.current_token
            self.eat(op.type)
            node = BinOp(node, op, self.multiplicative())
        return node

    def shift(self):
        node = self.additive()
        while self.current_token.type in ("LSHIFT", "RSHIFT"):
            op = self.current_token
            self.eat(op.type)
            node = BinOp(node, op, self.additive())
        return node

    def comparison(self):
        node = self.shift()
        while self.current_token.type in ("LT", "LE", "GT", "GE"):
            op = self.current_token
            self.eat(op.type)
            node = BinOp(node, op, self.shift())
        return node

    def equality(self):
        node = self.comparison()
        while self.current_token.type in ("EQ", "NE"):
            op = self.current_token
            self.eat(op.type)
            node = BinOp(node, op, self.comparison())
        return node

    def bit_and(self):
        node = self.equality()
        while self.current_token.type == "BITAND":
            op = self.eat("BITAND")
            node = BinOp(node, op, self.equality())
        return node

    def bit_xor(self):
        node = self.bit_and()
        while self.current_token.type == "BITXOR":
            op = self.eat("BITXOR")
            node = BinOp(node, op, self.bit_and())
        return node

    def bit_or(self):
        node = self.bit_xor()
        while self.current_token.type == "BITOR":
            op = self.eat("BITOR")
            node = BinOp(node, op, self.bit_xor())
        return node

    def logic_and(self):
        node = self.bit_or()
        while self.current_token.type == "AND":
            op = self.eat("AND")
            node = BinOp(node, op, self.bit_or())
        return node

    def logic_or(self):
        node = self.logic_and()
        while self.current_token.type == "OR":
            op = self.eat("OR")
            node = BinOp(node, op, self.logic_and())
        return node
