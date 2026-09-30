from lexer import lexer


code = """
int calculate(int x) {
    int y = x * 2;

    if (y >= 10)
        return y + 5;

    return y - 5;
}
"""


lexer.input(code)

while True:
    token = lexer.token()

    if not token:
        break

    print(
        f"{token.type:<12} "
        f"{str(token.value):<12} "
        f"line={token.lineno}"
    )