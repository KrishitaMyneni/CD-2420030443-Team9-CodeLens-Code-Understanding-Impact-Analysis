from backend.app.compiler.lexer import lexer
from backend.app.compiler.parser import parser
from backend.app.compiler.change_analyzer import ChangeAnalyzer


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


old_ast = parser.parse(old_code, lexer=lexer)
new_ast = parser.parse(new_code, lexer=lexer)


analyzer = ChangeAnalyzer()

changes = analyzer.compare(
    old_ast,
    new_ast,
)


print("\nChanges Detected")
print("-" * 60)

for change in changes:
    print(f"Type: {change.change_type}")
    print(f"Description: {change.description}")
    print(f"Path: {change.path}")
    print()