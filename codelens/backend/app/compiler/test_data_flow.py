from lexer import lexer
from parser import parser
from tac import TACGenerator
from basic_blocks import BasicBlockBuilder
from cfg import CFGBuilder
from data_flow import ReachingDefinitions


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

# Perform Reaching Definitions analysis
analysis = ReachingDefinitions(blocks, cfg)
results = analysis.analyze()


# Display results
print("\nReaching Definitions")
print("-" * 60)

for block in blocks:
    block_id = block.id

    print(f"\nB{block_id}")

    print("  GEN:")
    for definition in results["gen"][block_id]:
        print(f"    {definition}")

    print("  KILL:")
    for definition in results["kill"][block_id]:
        print(f"    {definition}")

    print("  IN:")
    for definition in results["in"][block_id]:
        print(f"    {definition}")

    print("  OUT:")
    for definition in results["out"][block_id]:
        print(f"    {definition}")