# builtins.py

import math
import random


def call_builtin(interpreter, name, args):

    def eval_arg(i):
        return interpreter.visit(args[i])

    if name == "printf":
        return interpreter.builtin_printf(args)

    if name == "scanf":
        return 0

    if name == "abs":
        return abs(eval_arg(0))

    if name == "sqrt":
        value = eval_arg(0)
        if value < 0:
            raise ValueError("sqrt argument cannot be negative")
        return int(math.sqrt(value))

    if name == "pow":
        return int(math.pow(eval_arg(0), eval_arg(1)))

    if name == "max":
        return max(eval_arg(0), eval_arg(1))

    if name == "min":
        return min(eval_arg(0), eval_arg(1))

    if name == "rand":
        return random.randint(0, 32767)

    raise ValueError(f"Undefined function: {name}")
