# Interpreter for Small-C.

import math
import random

from parser import (
    ArrayAccess,
    Assign,
    BinOp,
    Break,
    Compound,
    Continue,
    Declaration,
    DoWhile,
    For,
    FunctionCall,
    FunctionDef,
    If,
    Num,
    Return,
    String,
    UnaryOp,
    Var,
    While,
)
from symtable import SymbolTable
from memory import Memory


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class Interpreter:
    BUILTINS = {
        "printf", "scanf", "abs", "sqrt", "pow", "max", "min", "strlen",
        "strcpy", "strcat", "strcmp", "atoi", "itoa", "rand",
    }

    def __init__(self, trace=False):
        self.symbol_table = SymbolTable()
        self.memory = Memory()
        self.functions = {}
        self.trace = trace

    def trace_line(self, node):
        if self.trace and hasattr(node, "line"):
            print(f"[line {node.line}] {type(node).__name__}")

    def visit(self, node):
        self.trace_line(node)
        if isinstance(node, Num):
            return node.value
        if isinstance(node, String):
            return node.value
        if isinstance(node, Var):
            return self.load_var(node.value)
        if isinstance(node, ArrayAccess):
            return self.load_array(node.name, self.visit(node.index))
        if isinstance(node, UnaryOp):
            return self.eval_unary(node)
        if isinstance(node, BinOp):
            return self.eval_binary(node)
        if isinstance(node, Declaration):
            return self.declare(node)
        if isinstance(node, Assign):
            return self.assign(node)
        if isinstance(node, Compound):
            result = None
            for statement in node.statements:
                result = self.visit(statement)
            return result
        if isinstance(node, If):
            if self.visit(node.condition):
                return self.visit(node.then_branch)
            if node.else_branch:
                return self.visit(node.else_branch)
            return None
        if isinstance(node, While):
            return self.exec_while(node)
        if isinstance(node, For):
            return self.exec_for(node)
        if isinstance(node, DoWhile):
            return self.exec_do_while(node)
        if isinstance(node, Break):
            raise BreakSignal()
        if isinstance(node, Continue):
            raise ContinueSignal()
        if isinstance(node, FunctionDef):
            self.functions[node.name] = node
            return None
        if isinstance(node, FunctionCall):
            return self.call_function(node.name, node.args)
        if isinstance(node, Return):
            raise ReturnSignal(self.visit(node.expr) if node.expr else 0)
        raise ValueError(f"Unknown node type: {type(node)}")

    def load_var(self, name):
        symbol = self.symbol_table.lookup(name)
        if not symbol:
            raise ValueError(f"Undefined variable: {name}")
        if symbol.dimensions:
            return symbol.address
        return self.memory.load(symbol.address)

    def load_array(self, name, index):
        symbol = self.symbol_table.lookup(name)
        if not symbol:
            raise ValueError(f"Undefined array: {name}")
        if not symbol.dimensions:
            raise ValueError(f"{name} is not an array")
        self.memory.check_bounds(index, symbol.dimensions[0])
        return self.memory.array_load(symbol.address, index, symbol.type)

    def array_address(self, name, index):
        symbol = self.symbol_table.lookup(name)
        if not symbol or not symbol.dimensions:
            raise ValueError(f"Undefined array: {name}")
        self.memory.check_bounds(index, symbol.dimensions[0])
        width = 1 if symbol.type == "char" else 4
        return symbol.address + index * width

    def eval_unary(self, node):
        if node.op.type == "PLUS":
            return self.visit(node.expr)
        if node.op.type == "MINUS":
            return -self.visit(node.expr)
        if node.op.type == "NOT":
            return 0 if self.visit(node.expr) else 1
        if node.op.type == "BITNOT":
            return ~self.visit(node.expr)
        if node.op.type == "BITAND":
            return self.address_of(node.expr)
        if node.op.type == "MUL":
            address = self.visit(node.expr)
            return self.memory.load(address)
        raise ValueError(f"Unknown unary operator: {node.op.value}")

    def eval_binary(self, node):
        if node.op.type == "AND":
            left = self.visit(node.left)
            return 1 if left and self.visit(node.right) else 0
        if node.op.type == "OR":
            left = self.visit(node.left)
            return 1 if left or self.visit(node.right) else 0
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.op.type == "PLUS":
            return left + right
        if node.op.type == "MINUS":
            return left - right
        if node.op.type == "MUL":
            return left * right
        if node.op.type == "DIV":
            if right == 0:
                raise ValueError("division by zero")
            return int(left / right)
        if node.op.type == "MOD":
            if right == 0:
                raise ValueError("division by zero")
            return left % right
        if node.op.type == "BITAND":
            return left & right
        if node.op.type == "BITOR":
            return left | right
        if node.op.type == "BITXOR":
            return left ^ right
        if node.op.type == "LSHIFT":
            return left << right
        if node.op.type == "RSHIFT":
            return left >> right
        if node.op.type == "LT":
            return 1 if left < right else 0
        if node.op.type == "LE":
            return 1 if left <= right else 0
        if node.op.type == "GT":
            return 1 if left > right else 0
        if node.op.type == "GE":
            return 1 if left >= right else 0
        if node.op.type == "EQ":
            return 1 if left == right else 0
        if node.op.type == "NE":
            return 1 if left != right else 0
        raise ValueError(f"Unknown operator: {node.op.value}")

    def declare(self, node):
        size = self.visit(node.array_size) if node.array_size else None
        symbol = self.symbol_table.define(
            node.name,
            node.type,
            [size] if size else None,
            pointer=node.pointer,
        )
        if node.array_size:
            for i in range(size):
                self.memory.array_store(symbol.address, i, 0, node.type)
        else:
            value = self.visit(node.initializer) if node.initializer else 0
            self.memory.store(symbol.address, value, node.type)
        return None

    def assign(self, node):
        current = self.read_lvalue(node.left)
        value = self.visit(node.right)
        if node.op.type == "PLUS_ASSIGN":
            value = current + value
        elif node.op.type == "MINUS_ASSIGN":
            value = current - value
        elif node.op.type == "MUL_ASSIGN":
            value = current * value
        elif node.op.type == "DIV_ASSIGN":
            if value == 0:
                raise ValueError("division by zero")
            value = int(current / value)
        elif node.op.type == "MOD_ASSIGN":
            if value == 0:
                raise ValueError("division by zero")
            value = current % value
        self.write_lvalue(node.left, value)
        return value

    def read_lvalue(self, node):
        if isinstance(node, Var):
            symbol = self.symbol_table.lookup(node.value)
            return self.memory.load(symbol.address) if symbol else 0
        if isinstance(node, ArrayAccess):
            return self.load_array(node.name, self.visit(node.index))
        if isinstance(node, UnaryOp) and node.op.type == "MUL":
            return self.memory.load(self.visit(node.expr))
        raise ValueError("Invalid assignment target")

    def write_lvalue(self, node, value):
        if isinstance(node, Var):
            symbol = self.symbol_table.lookup(node.value)
            if not symbol:
                symbol = self.symbol_table.define(node.value, "int")
            self.memory.store(symbol.address, value, symbol.type)
            return
        if isinstance(node, ArrayAccess):
            symbol = self.symbol_table.lookup(node.name)
            index = self.visit(node.index)
            self.memory.check_bounds(index, symbol.dimensions[0])
            self.memory.array_store(symbol.address, index, value, symbol.type)
            return
        if isinstance(node, UnaryOp) and node.op.type == "MUL":
            self.memory.store(self.visit(node.expr), value, "int")
            return
        raise ValueError("Invalid assignment target")

    def address_of(self, node):
        if isinstance(node, Var):
            symbol = self.symbol_table.lookup(node.value)
            if not symbol:
                raise ValueError(f"Undefined variable: {node.value}")
            return symbol.address
        if isinstance(node, ArrayAccess):
            return self.array_address(node.name, self.visit(node.index))
        raise ValueError("Can only take address of a variable or array element")

    def exec_while(self, node):
        while self.visit(node.condition):
            try:
                self.visit(node.body)
            except ContinueSignal:
                continue
            except BreakSignal:
                break
        return None

    def exec_for(self, node):
        if node.init:
            self.visit(node.init)
        while True:
            if node.condition and not self.visit(node.condition):
                break
            try:
                self.visit(node.body)
            except ContinueSignal:
                pass
            except BreakSignal:
                break
            if node.update:
                self.visit(node.update)
        return None

    def exec_do_while(self, node):
        while True:
            try:
                self.visit(node.body)
            except ContinueSignal:
                pass
            except BreakSignal:
                break
            if not self.visit(node.condition):
                break
        return None

    def call_function(self, name, args):
        if name in self.functions:
            return self.call_user_function(name, args)
        if name in self.BUILTINS:
            return self.call_builtin(name, args)
        raise ValueError(f"Undefined function: {name}")

    def call_user_function(self, name, args):
        func = self.functions[name]
        self.symbol_table.enter_scope()
        try:
            for i, (type_, param_name, pointer) in enumerate(func.params):
                value = self.visit(args[i]) if i < len(args) else 0
                if pointer and isinstance(args[i], Var):
                    source = self.symbol_table.lookup(args[i].value)
                    self.symbol_table.define_alias(param_name, type_, source.address, source.dimensions, pointer=True)
                else:
                    symbol = self.symbol_table.define(param_name, type_, pointer=pointer)
                    self.memory.store(symbol.address, value, type_)
            try:
                self.visit(func.body)
            except ReturnSignal as signal:
                return signal.value
            return 0
        finally:
            self.symbol_table.exit_scope()

    def call_builtin(self, name, args):
        if name == "printf":
            return self.builtin_printf(args)
        if name == "scanf":
            return 0
        if name == "abs":
            return abs(self.visit(args[0]))
        if name == "sqrt":
            value = self.visit(args[0])
            if value < 0:
                raise ValueError("sqrt argument cannot be negative")
            return int(math.sqrt(value))
        if name == "pow":
            return int(math.pow(self.visit(args[0]), self.visit(args[1])))
        if name == "max":
            return max(self.visit(args[0]), self.visit(args[1]))
        if name == "min":
            return min(self.visit(args[0]), self.visit(args[1]))
        if name == "strlen":
            return len(self.read_string_arg(args[0]))
        if name == "strcpy":
            text = self.read_string_arg(args[1])
            self.write_string_arg(args[0], text)
            return self.visit(args[0])
        if name == "strcat":
            text = self.read_string_arg(args[0]) + self.read_string_arg(args[1])
            self.write_string_arg(args[0], text)
            return self.visit(args[0])
        if name == "strcmp":
            left = self.read_string_arg(args[0])
            right = self.read_string_arg(args[1])
            return 0 if left == right else (-1 if left < right else 1)
        if name == "atoi":
            return int(self.read_string_arg(args[0]))
        if name == "itoa":
            self.write_string_arg(args[1], str(self.visit(args[0])))
            return self.visit(args[1])
        if name == "rand":
            return random.randint(0, 32767)
        raise ValueError(f"Undefined function: {name}")

    def builtin_printf(self, args):
        if not args:
            return 0
        if isinstance(args[0], String):
            fmt = self.visit(args[0])
            values = [self.visit(arg) for arg in args[1:]]
            output = self.format_printf(fmt, values)
        else:
            output = str(self.visit(args[0]))
        print(output, end="")
        return len(output)

    def format_printf(self, fmt, values):
        result = ""
        i = 0
        arg_index = 0
        while i < len(fmt):
            if fmt[i] != "%":
                result += fmt[i]
                i += 1
                continue
            if i + 1 < len(fmt) and fmt[i + 1] == "%":
                result += "%"
                i += 2
                continue
            spec = fmt[i + 1] if i + 1 < len(fmt) else ""
            value = values[arg_index] if arg_index < len(values) else 0
            arg_index += 1
            if spec == "d":
                result += str(value)
            elif spec == "c":
                result += chr(value)
            elif spec == "s":
                result += self.read_string_value(value)
            elif spec == "x":
                result += format(value, "x")
            else:
                result += "%" + spec
            i += 2
        return result

    def read_string_arg(self, arg):
        if isinstance(arg, String):
            return arg.value
        return self.read_string_value(self.visit(arg))

    def read_string_value(self, value):
        if isinstance(value, str):
            return value
        chars = []
        address = value
        while True:
            ch = self.memory.load(address)
            if ch == 0:
                break
            chars.append(chr(ch))
            address += 1
        return "".join(chars)

    def write_string_arg(self, target, text):
        address = self.visit(target)
        for offset, ch in enumerate(text):
            self.memory.store(address + offset, ord(ch), "char")
        self.memory.store(address + len(text), 0, "char")

    def interpret(self, tree):
        return self.visit(tree)
