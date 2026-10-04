from backend.app.compiler.lexer import lexer
from backend.app.compiler.parser import parser
from backend.app.compiler.symbol_table_builder import SymbolTableBuilder


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

# Build symbol table from AST
builder = SymbolTableBuilder()
symbol_table = builder.build(ast)


# Display symbols
print("\nSymbol Table")
print("-" * 60)

for scope_data in symbol_table.all_scopes:
    print(f"\nScope: {scope_data['name']}")

    for symbol in scope_data["symbols"].values():
        print(
            f"Name: {symbol.name:<12} "
            f"Type: {symbol.symbol_type:<8} "
            f"Kind: {symbol.kind:<10} "
            f"Scope: {symbol.scope}"
        )