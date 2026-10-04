from backend.app.compiler.lexer import lexer
from backend.app.compiler.parser import parser
from backend.app.compiler.tac import TACGenerator
from backend.app.compiler.basic_blocks import BasicBlockBuilder

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
tac_generator = TACGenerator()
instructions = tac_generator.generate(ast)

# Build Basic Blocks
block_builder = BasicBlockBuilder()
blocks = block_builder.build(instructions)


# Display Basic Blocks
print("\nBasic Blocks")
print("-" * 60)

for block in blocks:
    print(block)
    print()