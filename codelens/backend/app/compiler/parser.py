import ply.yacc as yacc

from .lexer import tokens
from .ast_nodes import (
    Program,
    Function,
    Parameter,
    Block,
    VariableDeclaration,
    Assignment,
    IfStatement,
    WhileStatement,
    ReturnStatement,
    BinaryOperation,
    UnaryOperation,
    Identifier,
    Literal,
)

precedence = (
    ("nonassoc", "IFX"),
    ("left", "ELSE"),
    ("left", "EQ", "NE"),
    ("left", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE"),
    ("right", "UMINUS"),
)


# --------------------------------------------------
# Program
# --------------------------------------------------

def p_program(p):
    """program : external_declarations"""
    p[0] = Program(p[1])


def p_external_declarations_multiple(p):
    """external_declarations : external_declarations external_declaration"""
    p[0] = p[1] + [p[2]]


def p_external_declarations_single(p):
    """external_declarations : external_declaration"""
    p[0] = [p[1]]


def p_external_declaration(p):
    """external_declaration : function_definition"""
    p[0] = p[1]


# --------------------------------------------------
# Function
# --------------------------------------------------

def p_function_definition(p):
    """function_definition : type_specifier ID LPAREN parameter_list RPAREN compound_statement"""
    p[0] = Function(
        return_type=p[1],
        name=p[2],
        parameters=p[4],
        body=p[6],
    )


# --------------------------------------------------
# Parameters
# --------------------------------------------------

def p_parameter_list_multiple(p):
    """parameter_list : parameter_list COMMA parameter"""
    p[0] = p[1] + [p[3]]


def p_parameter_list_single(p):
    """parameter_list : parameter"""
    p[0] = [p[1]]


def p_parameter_list_empty(p):
    """parameter_list : empty"""
    p[0] = []


def p_parameter(p):
    """parameter : type_specifier ID"""
    p[0] = Parameter(
        type=p[1],
        name=p[2],
    )


# --------------------------------------------------
# Types
# --------------------------------------------------

def p_type_specifier(p):
    """
    type_specifier : INT
                   | FLOAT
                   | CHAR
                   | VOID
    """
    p[0] = p[1]


# --------------------------------------------------
# Compound Statement
# --------------------------------------------------

def p_compound_statement(p):
    """compound_statement : LBRACE statement_list RBRACE"""
    p[0] = Block(p[2])


def p_statement_list_multiple(p):
    """statement_list : statement_list statement"""
    p[0] = p[1] + [p[2]]


def p_statement_list_single(p):
    """statement_list : statement"""
    p[0] = [p[1]]


def p_statement_list_empty(p):
    """statement_list : empty"""
    p[0] = []


# --------------------------------------------------
# Statements
# --------------------------------------------------

def p_statement(p):
    """
    statement : variable_declaration
              | assignment
              | if_statement
              | while_statement
              | return_statement
              | compound_statement
              | expression_statement
    """
    p[0] = p[1]


# --------------------------------------------------
# Variable Declaration
# --------------------------------------------------

def p_variable_declaration(p):
    """variable_declaration : type_specifier ID optional_initializer SEMICOLON"""
    p[0] = VariableDeclaration(
        type=p[1],
        name=p[2],
        initializer=p[3],
    )


def p_optional_initializer(p):
    """optional_initializer : ASSIGN expression"""
    p[0] = p[2]


def p_optional_initializer_empty(p):
    """optional_initializer : empty"""
    p[0] = None


# --------------------------------------------------
# Assignment
# --------------------------------------------------

def p_assignment(p):
    """assignment : ID ASSIGN expression SEMICOLON"""
    p[0] = Assignment(
        name=p[1],
        value=p[3],
    )


# --------------------------------------------------
# If Statement
# --------------------------------------------------

def p_if_statement(p):
    """if_statement : IF LPAREN expression RPAREN statement %prec IFX
                    | IF LPAREN expression RPAREN statement ELSE statement"""
    if len(p) == 6:
        p[0] = IfStatement(
            condition=p[3],
            then_branch=p[5],
            else_branch=None,
        )
    else:
        p[0] = IfStatement(
            condition=p[3],
            then_branch=p[5],
            else_branch=p[7],
        )


# --------------------------------------------------
# While Statement
# --------------------------------------------------

def p_while_statement(p):
    """while_statement : WHILE LPAREN expression RPAREN statement"""
    p[0] = WhileStatement(
        condition=p[3],
        body=p[5],
    )


# --------------------------------------------------
# Return
# --------------------------------------------------

def p_return_statement(p):
    """return_statement : RETURN optional_return_value SEMICOLON"""
    p[0] = ReturnStatement(p[2])


def p_optional_return_value(p):
    """optional_return_value : expression"""
    p[0] = p[1]


def p_optional_return_value_empty(p):
    """optional_return_value : empty"""
    p[0] = None


# --------------------------------------------------
# Expression Statement
# --------------------------------------------------

def p_expression_statement(p):
    """expression_statement : expression SEMICOLON"""
    p[0] = p[1]


# --------------------------------------------------
# Expressions
# --------------------------------------------------

def p_expression_binary(p):
    """
    expression : expression PLUS expression
               | expression MINUS expression
               | expression TIMES expression
               | expression DIVIDE expression
               | expression EQ expression
               | expression NE expression
               | expression LT expression
               | expression LE expression
               | expression GT expression
               | expression GE expression
    """
    p[0] = BinaryOperation(
        operator=p[2],
        left=p[1],
        right=p[3],
    )


def p_expression_unary(p):
    """expression : MINUS expression %prec UMINUS"""
    p[0] = UnaryOperation(operator=p[1], operand=p[2])


def p_expression_grouped(p):
    """expression : LPAREN expression RPAREN"""
    p[0] = p[2]


def p_expression_identifier(p):
    """expression : ID"""
    p[0] = Identifier(p[1])


def p_expression_number(p):
    """expression : NUMBER"""
    p[0] = Literal(p[1])


# --------------------------------------------------
# Empty
# --------------------------------------------------

def p_empty(p):
    """empty :"""
    pass


# --------------------------------------------------
# Error Handling
# --------------------------------------------------

def p_error(p):
    if p:
        print(
            f"Syntax error at '{p.value}' "
            f"(token: {p.type}, line: {p.lineno})"
        )
    else:
        print("Syntax error at end of input")


# --------------------------------------------------
# Build Parser
# --------------------------------------------------

parser = yacc.yacc(debug=True, debugfile="parser.out")