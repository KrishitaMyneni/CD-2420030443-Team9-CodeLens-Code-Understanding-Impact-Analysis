import ply.lex as lex


# --------------------------------------------------
# Reserved Words
# --------------------------------------------------

reserved = {
    "int": "INT",
    "float": "FLOAT",
    "char": "CHAR",
    "void": "VOID",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "return": "RETURN",
}


# --------------------------------------------------
# Token List
# --------------------------------------------------

tokens = [
    "ID",
    "NUMBER",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "ASSIGN",
    "EQ",
    "NE",
    "LT",
    "LE",
    "GT",
    "GE",
    "LPAREN",
    "RPAREN",
    "LBRACE",
    "RBRACE",
    "LBRACKET",
    "RBRACKET",
    "SEMICOLON",
    "COMMA",
] + list(reserved.values())


# --------------------------------------------------
# Simple Tokens
# --------------------------------------------------

t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_ASSIGN = r"="
t_EQ = r"=="
t_NE = r"!="
t_LT = r"<"
t_LE = r"<="
t_GT = r">"
t_GE = r">="
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"
t_SEMICOLON = r";"
t_COMMA = r","


# --------------------------------------------------
# Ignored Characters
# --------------------------------------------------

t_ignore = " \t"


# --------------------------------------------------
# Numbers
# --------------------------------------------------

def t_NUMBER(t):
    r"\d+(\.\d+)?"
    if "." in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)

    return t


# --------------------------------------------------
# Identifiers and Reserved Words
# --------------------------------------------------

def t_ID(t):
    r"[a-zA-Z_][a-zA-Z_0-9]*"
    t.type = reserved.get(t.value, "ID")
    return t


# --------------------------------------------------
# Comments
# --------------------------------------------------

def t_COMMENT(t):
    r"//.*"
    pass


# --------------------------------------------------
# New Lines
# --------------------------------------------------

def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


# --------------------------------------------------
# Error Handling
# --------------------------------------------------

def t_error(t):
    print(
        f"Illegal character '{t.value[0]}' "
        f"at line {t.lineno}"
    )
    t.lexer.skip(1)


# --------------------------------------------------
# Build Lexer
# --------------------------------------------------

lexer = lex.lex()