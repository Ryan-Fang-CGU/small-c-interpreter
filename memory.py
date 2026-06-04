# Memory Simulation for Small-C

class Memory:
    def __init__(self):
        self.memory = {}  # address -> value

    def store(self, address, value, type_='int'):
        if type_ == 'char':
            value = value & 0xFF  # 8-bit
        self.memory[address] = value

    def load(self, address):
        return self.memory.get(address, 0)

    def array_store(self, base_address, index, value, type_='int'):
        address = base_address + index * (1 if type_ == 'char' else 4)
        self.store(address, value, type_)

    def array_load(self, base_address, index, type_='int'):
        address = base_address + index * (1 if type_ == 'char' else 4)
        return self.load(address)

    def check_bounds(self, index, size):
        if index < 0 or index >= size:
            raise ValueError(f"Array index out of bounds: {index}")
