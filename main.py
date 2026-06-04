# Small-C Interactive Interpreter

import os
import re

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


VERSION = "1.0"
AUTHOR = "Small-C Project Team"
SEMESTER = "Spring 2026"


def preprocess(source):
    defines = {}
    output = []
    for line in source.splitlines():
        match = re.match(r"\s*#define\s+([A-Za-z_]\w*)\s+(.+?)\s*$", line)
        if match:
            defines[match.group(1)] = match.group(2)#regular expression 的第一個括號匹配到的內容是 match.group(1)，第二個括號匹配到的內容是 match.group(2)，以此類推
            output.append("")
            continue
        output.append(line)
    source = "\n".join(output) #讓output 透過換行符號\n連接成一個字符串
    for name, value in defines.items(): #從defines字典中取出每個鍵值對，name是鍵，value是值
        source = re.sub(rf"\b{name}\b", value, source)
    return source


def parse_source(source):
    lexer = Lexer(preprocess(source))
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def run_source(source, trace=False):
    interp = Interpreter(trace=trace)#建立一台解釋器可執行AST的機器
    tree = parse_source(source)#將原始程式碼轉換成抽象語法樹（AST）的過程，parse_source函數會先預處理（preprocess）->詞法分析器（Lexer）->分解成一系列的標記（tokens）->語法分析器（Parser）將這些標記組織成一棵抽象語法樹（AST）。
    interp.interpret(tree)
    result = 0
    if "main" in interp.functions:
        result = interp.call_function("main", [])
        print(f"Program exited with return value {result}.")
    return interp


def print_about():
    print("Small-C Interactive Interpreter")
    print(f"Version: {VERSION}")
    print(f"Author: {AUTHOR}")
    print(f"Semester: {SEMESTER}")


def print_help():
    print("Commands:")
    print("  ABOUT                 Show interpreter information")
    print("  HELP                  Show this help")
    print("  APPEND                Append program lines until a single '.' line")
    print("  LIST [n|n1-n2]        List all lines, one line, or a range")
    print("  EDIT n                Replace line n")
    print("  DELETE n             Delete line n")
    print("  INSERT n             Insert lines before n until a single '.' line")
    print("  CHECK                 Parse the current program")
    print("  RUN                   Run the current program buffer")
    print("  SAVE <file>           Save the current program buffer")
    print("  LOAD <file>           Load a program file")
    print("  NEW                   Clear program buffer and interpreter state")
    print("  TRACE ON/OFF          Enable or disable execution trace")
    print("  VARS                  Show current interactive variables")
    print("  FUNCS                 Show current interactive functions and built-ins")
    print("  CLEAR                 Clear the screen")
    print("  QUIT / EXIT           Leave the interpreter")


def list_lines(code_lines, arg=""):
    if not code_lines:
        print("(no program lines)")
        return
    start = 1
    end = len(code_lines)
    if arg:
        if "-" in arg:
            left, right = arg.split("-", 1)
            start = int(left)
            end = int(right)
        else:
            start = end = int(arg)
    for line_no in range(max(1, start), min(len(code_lines), end) + 1):
        print(f"{line_no:4}: {code_lines[line_no - 1]}")


def read_block(first_line):
    lines = [first_line]
    brace_balance = first_line.count("{") - first_line.count("}")
    needs_more = brace_balance > 0
    if first_line.strip().startswith("do"):
        needs_more = True
    while needs_more:
        line = input("  > ")
        lines.append(line)
        brace_balance += line.count("{") - line.count("}")
        text = "\n".join(lines).strip()
        needs_more = brace_balance > 0 or (text.startswith("do") and not re.search(r"\bwhile\s*\(.*\)\s*;\s*$", text, re.S))
    return "\n".join(lines)


def execute_interactive(interp, source):
    tree = parse_source(source)
    return interp.interpret(tree)


def repl():
    print(f"Small-C Interpreter v{VERSION}")
    print("Type 'HELP' for commands, 'EXIT' to quit.")
    code_lines = []
    interp = Interpreter()
    trace_enabled = False

    while True:
        try:
            raw = input("sc> ")
            line = raw.strip()
            if not line:
                continue
            upper = line.upper()

            if upper in ("EXIT", "QUIT"):
                print("Goodbye!")
                break
            if upper == "ABOUT":
                print_about()
                continue
            if upper == "HELP":
                print_help()
                continue
            if upper == "CLEAR":
                os.system("cls" if os.name == "nt" else "clear")
                continue
            if upper == "NEW":
                code_lines = []
                interp = Interpreter(trace=trace_enabled)
                print("All cleared.")
                continue
            if upper == "APPEND":
                while True:
                    entry = input(f"{len(code_lines) + 1:4}> ")
                    if entry.strip() == ".":
                        break
                    code_lines.append(entry)
                print(f"Appended. Total lines: {len(code_lines)}")
                continue
            if upper.startswith("INSERT "):
                index = int(line[7:].strip())
                insert_at = max(0, min(index - 1, len(code_lines)))
                new_lines = []
                current = index
                while True:
                    entry = input(f"{current:4}> ")
                    if entry.strip() == ".":
                        break
                    new_lines.append(entry)
                    current += 1
                code_lines[insert_at:insert_at] = new_lines
                print(f"Inserted {len(new_lines)} line(s).")
                continue
            if upper.startswith("EDIT "):
                index = int(line[5:].strip())
                if index < 1 or index > len(code_lines):
                    print("Line number out of range.")
                    continue
                print(f"{index:4}: {code_lines[index - 1]}")
                code_lines[index - 1] = input("new> ")
                print("Line updated.")
                continue
            if upper.startswith("DELETE "):
                index = int(line[7:].strip())
                if index < 1 or index > len(code_lines):
                    print("Line number out of range.")
                    continue
                del code_lines[index - 1]
                print("Line deleted.")
                continue
            if upper.startswith("LIST"):
                list_lines(code_lines, line[4:].strip())
                continue
            if upper.startswith("LOAD "):
                filename = line[5:].strip()
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        code_lines = f.read().splitlines()
                    print(f"Loaded {len(code_lines)} line(s) from {filename}.")
                except FileNotFoundError:
                    print(f"File not found: {filename}")
                continue
            if upper.startswith("SAVE "):
                filename = line[5:].strip()
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(code_lines))
                print(f"Saved {len(code_lines)} line(s) to {filename}.")
                continue
            if upper == "CHECK":
                try:
                    parse_source("\n".join(code_lines))
                    print("No errors found.")
                except Exception as exc:
                    print(f"Error: {exc}")
                continue
            if upper == "RUN":
                if not code_lines:
                    print("No code to run.")
                    continue
                try:
                    interp = run_source("\n".join(code_lines), trace=trace_enabled)
                except Exception as exc:
                    print(f"Error: {exc}")
                continue
            if upper == "TRACE ON":
                trace_enabled = True
                interp.trace = True
                print("Trace ON")
                continue
            if upper == "TRACE OFF":
                trace_enabled = False
                interp.trace = False
                print("Trace OFF")
                continue
            if upper == "VARS":
                printed = False
                for symbol in interp.symbol_table.all_symbols():
                    if symbol.dimensions:
                        print(f"{symbol.type} {symbol.name}[{symbol.dimensions[0]}] @ {symbol.address}")
                    else:
                        value = interp.memory.load(symbol.address)
                        if symbol.type == "char":
                            print(f"char {symbol.name} = {value} ('{chr(value)}')")
                        else:
                            print(f"{symbol.type} {symbol.name} = {value}")
                    printed = True
                if not printed:
                    print("(no variables)")
                continue
            if upper == "FUNCS":
                for name, func in interp.functions.items():
                    params = ", ".join(param[1] for param in func.params)
                    print(f"{func.return_type} {name}({params}) [line {func.line}]")
                for name in sorted(Interpreter.BUILTINS):
                    print(f"{name} [built-in]")
                continue

            source = read_block(raw)
            execute_interactive(interp, source)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    repl()
