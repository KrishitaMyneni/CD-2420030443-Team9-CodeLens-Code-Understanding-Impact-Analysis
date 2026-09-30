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

from .symbol_table import SymbolTable


class SymbolTableBuilder:
    def __init__(self):
        self.symbol_table = SymbolTable()

    def build(self, ast):
        self.visit(ast)
        return self.symbol_table

    def visit(self, node):
        if node is None:
            return

        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)

        return method(node)

    def generic_visit(self, node):
        return

    def visit_Program(self, node: Program):
        self.symbol_table.enter_scope("global")

        for declaration in node.declarations:
            self.visit(declaration)

        self.symbol_table.exit_scope()

    def visit_Function(self, node: Function):
        self.symbol_table.declare(
            name=node.name,
            symbol_type=node.return_type,
            kind="function",
        )

        self.symbol_table.enter_scope(node.name)

        for parameter in node.parameters:
            self.visit(parameter)

        self.visit(node.body)

        self.symbol_table.exit_scope()

    def visit_Parameter(self, node: Parameter):
        self.symbol_table.declare(
            name=node.name,
            symbol_type=node.type,
            kind="parameter",
        )

    def visit_Block(self, node: Block):
        for statement in node.statements:
            self.visit(statement)

    def visit_VariableDeclaration(self, node: VariableDeclaration):
        self.symbol_table.declare(
            name=node.name,
            symbol_type=node.type,
            kind="variable",
        )

        self.visit(node.initializer)

    def visit_Assignment(self, node: Assignment):
        self.visit(node.value)

    def visit_IfStatement(self, node: IfStatement):
        self.visit(node.condition)
        self.visit(node.then_branch)
        self.visit(node.else_branch)

    def visit_WhileStatement(self, node: WhileStatement):
        self.visit(node.condition)
        self.visit(node.body)

    def visit_ReturnStatement(self, node: ReturnStatement):
        self.visit(node.value)

    def visit_BinaryOperation(self, node: BinaryOperation):
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOperation(self, node: UnaryOperation):
        self.visit(node.operand)

    def visit_Identifier(self, node: Identifier):
        return self.symbol_table.lookup(node.name)

    def visit_Literal(self, node: Literal):
        return