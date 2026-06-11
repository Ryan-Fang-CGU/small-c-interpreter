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
from builtins import call_builtin   # ⭐ 新增


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

    def eval_unary(self, node):
        if node.op.type == "PLUS":
            return self.visit(node.expr)
        if node.op.type == "MINUS":
            return -self.visit(node.expr)
        if node.op.type == "NOT":
            return 0 if self.visit(node.expr) else 1
        if node.op.type == "BITNOT":
            return ~self.visit(node.expr)
        raise ValueError(f"Unknown unary operator: {node.op.value}")

    def eval_binary(self, node):
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
        if node.op.type == "LT":
            return 1 if left < right else 0
        if node.op.type == "GT":
            return 1 if left > right else 0
        if node.op.type == "EQ":
            return 1 if left == right else 0
        if node.op.type == "NE":
            return 1 if left != right else 0

        raise ValueError(f"Unknown operator: {node.op.value}")

    def declare(self, node):
        symbol = self.symbol_table.define(node.name, node.type)
        value = self.visit(node.initializer) if node.initializer else 0
        self.memory.store(symbol.address, value, node.type)

    def assign(self, node):
        value = self.visit(node.right)
        symbol = self.symbol_table.lookup(node.left.value)

        if not symbol:
            symbol = self.symbol_table.define(node.left.value, "int")

        self.memory.store(symbol.address, value, symbol.type)
        return value

    def exec_while(self, node):
        while self.visit(node.condition):
            try:
                self.visit(node.body)
            except ContinueSignal:
                continue
            except BreakSignal:
                break

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

    def call_function(self, name, args):
        if name in self.functions:
            return self.call_user_function(name, args)
        if name in self.BUILTINS:
            return call_builtin(self, name, args)   # ⭐ 改這裡
        raise ValueError(f"Undefined function: {name}")

    def call_user_function(self, name, args):
        func = self.functions[name]
        self.symbol_table.enter_scope()

        try:
            for i, (type_, param_name, pointer) in enumerate(func.params):
                value = self.visit(args[i]) if i < len(args) else 0
                symbol = self.symbol_table.define(param_name, type_)
                self.memory.store(symbol.address, value, type_)

            try:
                self.visit(func.body)
            except ReturnSignal as signal:
                return signal.value

            return 0

        finally:
            self.symbol_table.exit_scope()

    def interpret(self, tree):
        return self.visit(tree)
