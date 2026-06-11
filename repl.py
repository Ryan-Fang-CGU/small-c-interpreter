# repl.py

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


def repl():
    print("Small-C REPL (type 'exit' to quit)")
    interpreter = Interpreter()

    while True:
        try:
            text = input(">>> ")

            if text.strip() == "exit":
                break

            if not text.strip():
                continue

            # 自動補分號
            if not text.strip().endswith(";"):
                text += ";"

            lexer = Lexer(text)
            parser = Parser(lexer)
            tree = parser.parse()

            result = interpreter.interpret(tree)

            if result is not None:
                print(result)

        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    repl()
