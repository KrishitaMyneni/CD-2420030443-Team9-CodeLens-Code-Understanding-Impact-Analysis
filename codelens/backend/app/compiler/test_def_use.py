from lexer import lexer
from parser import parser
from tac import TACGenerator
from basic_blocks import BasicBlockBuilder
from cfg import CFGBuilder
from data_flow import ReachingDefinitions
from def_use import DefUseChain


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
reaching_definitions = ReachingDefinitions(
    blocks,
    cfg,
)

reaching_definitions.analyze()

# Build Def-Use Chains
def_use = DefUseChain(
    blocks,
    reaching_definitions,
)

chains = def_use.analyze()


# Display Def-Use Chains
print("\nDef-Use Chains")
print("-" * 60)

for definition, uses in chains.items():
    print(f"\nDefinition: {definition}")

    if uses:
        print("  Uses:")

        for use in sorted(
            uses,
            key=lambda item: (item.block_id, item.instruction_index),
        ):
            print(f"    {use}")
    else:
        print("  Uses: None")