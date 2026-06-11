# Small-C Interpreter

## Overview
This project implements a Small-C interpreter in Python. It supports basic C-like syntax and executes programs using an Abstract Syntax Tree (AST) with a visitor pattern.

## Architecture
The interpreter follows this process:
Source Code → Lexer → Parser (AST) → Interpreter → Memory / Symbol Table

## Project Structure
- lexer.py: Tokenizes source code into tokens
- parser.py: Builds AST from tokens
- interpreter.py: Executes AST (core logic)
- memory.py: Stores variable values
- symtable.py: Manages variable types and scope
- main.py: Entry point

## Features
- Arithmetic operations: +, -, *, /, %
- Control flow: if, while, for, do-while
- Functions (user-defined and built-in)
- Arrays and pointers
- Built-in functions: printf, sqrt, pow, strlen, rand, etc.

## Error Handling
The interpreter prevents runtime errors by checking:
- Division by zero
- Undefined variables (using symbol table)
- Array index out of bounds
- Invalid operations (e.g., sqrt of negative numbers)

Errors are handled using exceptions to avoid program crashes.

## How to Run
python main.py program.c

## Example
```c
int main() {
    int a = 5;
    int b = 3;
    printf("%d\n", a + b);
    return 0;
}
