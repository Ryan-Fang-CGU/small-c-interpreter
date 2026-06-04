# Symbol Table for Small-C

class Symbol:
    def __init__(self, name, type_, address, dimensions=None, pointer=False):
        self.name = name
        self.type = type_  # 'int' or 'char'
        self.address = address
        self.dimensions = dimensions  # list of sizes for arrays
        self.pointer = pointer

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]  # list of dicts, global is scopes[0]
        self.next_address = 1000

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def define(self, name, type_, dimensions=None, pointer=False, address=None):
        if name in self.scopes[-1]:
            return self.scopes[-1][name]
        if address is None:
            address = self.allocate_memory(type_, dimensions)
        symbol = Symbol(name, type_, address, dimensions, pointer)
        self.scopes[-1][name] = symbol
        return symbol

    def define_alias(self, name, type_, address, dimensions=None, pointer=False):
        symbol = Symbol(name, type_, address, dimensions, pointer)
        self.scopes[-1][name] = symbol
        return symbol

    def assign_symbol(self, symbol):
        self.scopes[-1][symbol.name] = symbol
        return symbol

    def all_symbols(self):
        result = []
        for scope in self.scopes:
            result.extend(scope.values())
        return result

    def allocate_memory(self, type_, dimensions):
        count = 1
        if dimensions:
            for dimension in dimensions:
                count *= dimension
        width = 1 if type_ == 'char' else 4
        address = self.next_address
        self.next_address += max(1, count) * width
        return address

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

