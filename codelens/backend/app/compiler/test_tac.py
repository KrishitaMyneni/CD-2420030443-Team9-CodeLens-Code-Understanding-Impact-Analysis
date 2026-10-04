from backend.app.compiler.lexer import lexer
from backend.app.compiler.parser import parser
from backend.app.compiler.tac import TACGenerator


code = """
int calculate(int x) {
    int y = x * 2;

    if (y >= 10)
        return y + 5;

    return y - 5;
}
"""


# Parse source code into AST
ast = parser.parse(code, lexer=lexer)

# Generate TAC
generator = TACGenerator()
instructions = generator.generate(ast)


# Display TAC
print("\nThree-Address Code")
print("-" * 60)

for index, instruction in enumerate(instructions):
    print(f"{index:<4} {instruction}")