from dataclasses import dataclass
from typing import List

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


@dataclass
class TACInstruction:
    result: str
    operator: str
    arg1: str = ""
    arg2: str = ""

    def __str__(self):
        if self.operator == "label":
            return f"{self.result}:"

        if self.operator == "goto":
            return f"goto {self.result}"

        if self.operator == "if":
            return f"if {self.arg1} goto {self.result}"

        if self.operator == "return":
            if self.arg1:
                return f"return {self.arg1}"
            return "return"

        if self.operator == "=":
            return f"{self.result} = {self.arg1}"

        if self.operator == "neg":
            return f"{self.result} = -{self.arg1}"

        return f"{self.result} = {self.arg1} {self.operator} {self.arg2}"


class TACGenerator:
    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def generate(self, ast):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

        self.visit(ast)

        return self.instructions

    def visit(self, node):
        if node is None:
            return None

        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)

        return method(node)

    def generic_visit(self, node):
        return None

    def visit_Program(self, node: Program):
        for declaration in node.declarations:
            self.visit(declaration)

    def visit_Function(self, node: Function):
        self.instructions.append(
            TACInstruction(
                result=node.name,
                operator="label",
            )
        )

        self.visit(node.body)

    def visit_Parameter(self, node: Parameter):
        return node.name

    def visit_Block(self, node: Block):
        for statement in node.statements:
            self.visit(statement)

    def visit_VariableDeclaration(self, node: VariableDeclaration):
        if node.initializer is not None:
            value = self.visit(node.initializer)

            self.instructions.append(
                TACInstruction(
                    result=node.name,
                    operator="=",
                    arg1=value,
                )
            )

    def visit_Assignment(self, node: Assignment):
        value = self.visit(node.value)

        self.instructions.append(
            TACInstruction(
                result=node.name,
                operator="=",
                arg1=value,
            )
        )

    def visit_IfStatement(self, node: IfStatement):
        condition = self.visit(node.condition)

        then_label = self.new_label()
        end_label = self.new_label()

        if node.else_branch is not None:
            else_label = self.new_label()

            self.instructions.append(
                TACInstruction(
                    result=then_label,
                    operator="if",
                    arg1=condition,
                )
            )

            self.instructions.append(
                TACInstruction(
                    result=else_label,
                    operator="goto",
                )
            )

            self.instructions.append(
                TACInstruction(
                    result=then_label,
                    operator="label",
                )
            )

            self.visit(node.then_branch)

            self.instructions.append(
                TACInstruction(
                    result=end_label,
                    operator="goto",
                )
            )

            self.instructions.append(
                TACInstruction(
                    result=else_label,
                    operator="label",
                )
            )

            self.visit(node.else_branch)

            self.instructions.append(
                TACInstruction(
                    result=end_label,
                    operator="label",
                )
            )

        else:
            self.instructions.append(
                TACInstruction(
                    result=then_label,
                    operator="if",
                    arg1=condition,
                )
            )

            self.instructions.append(
                TACInstruction(
                    result=end_label,
                    operator="goto",
                )
            )

            self.instructions.append(
                TACInstruction(
                    result=then_label,
                    operator="label",
                )
            )

            self.visit(node.then_branch)

            self.instructions.append(
                TACInstruction(
                    result=end_label,
                    operator="label",
                )
            )

    def visit_WhileStatement(self, node: WhileStatement):
        start_label = self.new_label()
        body_label = self.new_label()
        end_label = self.new_label()

        self.instructions.append(
            TACInstruction(
                result=start_label,
                operator="label",
            )
        )

        condition = self.visit(node.condition)

        self.instructions.append(
            TACInstruction(
                result=body_label,
                operator="if",
                arg1=condition,
            )
        )

        self.instructions.append(
            TACInstruction(
                result=end_label,
                operator="goto",
            )
        )

        self.instructions.append(
            TACInstruction(
                result=body_label,
                operator="label",
            )
        )

        self.visit(node.body)

        self.instructions.append(
            TACInstruction(
                result=start_label,
                operator="goto",
            )
        )

        self.instructions.append(
            TACInstruction(
                result=end_label,
                operator="label",
            )
        )

    def visit_ReturnStatement(self, node: ReturnStatement):
        if node.value is None:
            self.instructions.append(
                TACInstruction(
                    result="",
                    operator="return",
                )
            )
        else:
            value = self.visit(node.value)

            self.instructions.append(
                TACInstruction(
                    result="",
                    operator="return",
                    arg1=value,
                )
            )

    def visit_BinaryOperation(self, node: BinaryOperation):
        left = self.visit(node.left)
        right = self.visit(node.right)

        temp = self.new_temp()

        self.instructions.append(
            TACInstruction(
                result=temp,
                operator=node.operator,
                arg1=left,
                arg2=right,
            )
        )

        return temp

    def visit_UnaryOperation(self, node: UnaryOperation):
        operand = self.visit(node.operand)

        temp = self.new_temp()

        self.instructions.append(
            TACInstruction(
                result=temp,
                operator="neg",
                arg1=operand,
            )
        )

        return temp

    def visit_Identifier(self, node: Identifier):
        return node.name

    def visit_Literal(self, node: Literal):
        return str(node.value)