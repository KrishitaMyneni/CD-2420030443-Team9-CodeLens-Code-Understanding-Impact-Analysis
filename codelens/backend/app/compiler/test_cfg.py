from backend.app.compiler.lexer import lexer
from backend.app.compiler.parser import parser
from backend.app.compiler.tac import TACGenerator
from backend.app.compiler.basic_blocks import BasicBlockBuilder
from backend.app.compiler.cfg import CFGBuilder


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

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(blocks)


# Display CFG
print("\nControl Flow Graph")
print("-" * 60)

for block_id, node in cfg.nodes.items():
    print(f"B{block_id}")
    print(f"  Successors: {sorted(node.successors)}")
    print(f"  Predecessors: {sorted(node.predecessors)}")
    print()


print("CFG Edges")
print("-" * 60)

for from_block, to_block in cfg.get_edges():
    print(f"B{from_block} -> B{to_block}")