from backend.app.compiler.lexer import lexer
from backend.app.compiler.parser import parser
from backend.app.compiler.explanation import ExplanationEngine


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

# Generate explanation
engine = ExplanationEngine()
explanations = engine.explain(ast)


# Display explanation
print("\nCode Explanation")
print("-" * 60)

for explanation in explanations:
    print(f"- {explanation}")