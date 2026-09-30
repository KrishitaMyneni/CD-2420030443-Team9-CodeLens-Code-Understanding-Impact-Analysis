from lexer import lexer
from parser import parser
from change_analyzer import ChangeAnalyzer
from impact_analyzer import ImpactAnalyzer
from tac import TACGenerator
from basic_blocks import BasicBlockBuilder
from cfg import CFGBuilder
from data_flow import ReachingDefinitions
from def_use import DefUseChain


old_code = """
int calculate(int x) {
    int y = x * 2;

    if (y > 10)
        return y + 5;

    return y - 5;
}
"""


new_code = """
int calculate(int x) {
    int y = x * 2;

    if (y >= 10)
        return y + 5;

    return y - 5;
}
"""


# --------------------------------------------------
# Build ASTs
# --------------------------------------------------

old_ast = parser.parse(
    old_code,
    lexer=lexer,
)

new_ast = parser.parse(
    new_code,
    lexer=lexer,
)


# --------------------------------------------------
# Detect Changes
# --------------------------------------------------

change_analyzer = ChangeAnalyzer()

changes = change_analyzer.compare(
    old_ast,
    new_ast,
)


# --------------------------------------------------
# Build TAC
# --------------------------------------------------

tac_generator = TACGenerator()

new_tac = tac_generator.generate(
    new_ast,
)


# --------------------------------------------------
# Build Basic Blocks
# --------------------------------------------------

block_builder = BasicBlockBuilder()

new_blocks = block_builder.build(
    new_tac,
)


# --------------------------------------------------
# Build CFG
# --------------------------------------------------

cfg_builder = CFGBuilder()

new_cfg = cfg_builder.build(
    new_blocks,
)


# --------------------------------------------------
# Reaching Definitions
# --------------------------------------------------

reaching_definitions = ReachingDefinitions(
    new_blocks,
    new_cfg,
)

reaching_definitions.analyze()


# --------------------------------------------------
# Def-Use Chains
# --------------------------------------------------

def_use_analyzer = DefUseChain(
    new_blocks,
    reaching_definitions,
)

def_use_chains = def_use_analyzer.analyze()


# --------------------------------------------------
# Analyze Impact
# --------------------------------------------------

impact_analyzer = ImpactAnalyzer()

impacts = impact_analyzer.analyze(
    new_ast,
    changes,
    new_cfg,
    def_use_chains,
)


# --------------------------------------------------
# Print Changes
# --------------------------------------------------

print("\nChanges")
print("-" * 60)

for change in changes:
    print(f"Type: {change.change_type}")
    print(f"Description: {change.description}")
    print(f"Path: {change.path}")
    print()


# --------------------------------------------------
# Print CFG
# --------------------------------------------------

print("\nControl Flow Graph")
print("-" * 60)

for block_id, node in new_cfg.nodes.items():
    print(f"B{block_id}")

    print(
        f"  Successors: "
        f"{sorted(node.successors)}"
    )

    print(
        f"  Predecessors: "
        f"{sorted(node.predecessors)}"
    )


# --------------------------------------------------
# Print Def-Use Chains
# --------------------------------------------------

print("\nDef-Use Chains")
print("-" * 60)

for definition, uses in def_use_chains.items():
    print(f"Definition: {definition}")

    for use in sorted(
        uses,
        key=lambda item: (
            item.block_id,
            item.instruction_index,
        ),
    ):
        print(f"  Use: {use}")

    print()


# --------------------------------------------------
# Print Impacts
# --------------------------------------------------

print("\nImpacts")
print("-" * 60)

for impact in impacts:
    print(
        f"Type: {impact.impact_type}"
    )

    print(
        f"Description: "
        f"{impact.description}"
    )

    print(
        f"Path: {impact.path}"
    )

    print()