from lexer import lexer
from parser import parser


code = """
int calculate(int x) {
    int y = x * 2;

    if (y >= 10)
        return y + 5;

    return y - 5;
}
"""


lexer.input(code)

ast = parser.parse(code, lexer=lexer)

print(ast)