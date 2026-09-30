from typing import List

from .ast_nodes import (
    Program,
    Function,
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


class ExplanationEngine:
    def explain(self, ast):
        explanations = []

        if isinstance(ast, Program):
            for declaration in ast.declarations:
                explanations.extend(self.explain(declaration))

        elif isinstance(ast, Function):
            explanations.append(
                f"Function '{ast.name}' returns {ast.return_type}."
            )

            if ast.parameters:
                parameters = ", ".join(
                    f"{parameter.type} {parameter.name}"
                    for parameter in ast.parameters
                )

                explanations.append(
                    f"It accepts the following parameter(s): {parameters}."
                )
            else:
                explanations.append(
                    "It does not accept any parameters."
                )

            explanations.extend(
                self.explain_block(ast.body)
            )

        return explanations

    def explain_block(self, block: Block):
        explanations = []

        for statement in block.statements:
            explanations.extend(
                self.explain_statement(statement)
            )

        return explanations

    def explain_statement(self, statement):
        explanations = []

        if isinstance(statement, VariableDeclaration):
            if statement.initializer is not None:
                value = self.expression_to_text(
                    statement.initializer
                )

                explanations.append(
                    f"Variable '{statement.name}' of type "
                    f"{statement.type} is initialized with {value}."
                )
            else:
                explanations.append(
                    f"Variable '{statement.name}' of type "
                    f"{statement.type} is declared."
                )

        elif isinstance(statement, Assignment):
            value = self.expression_to_text(
                statement.value
            )

            explanations.append(
                f"Variable '{statement.name}' is assigned {value}."
            )

        elif isinstance(statement, IfStatement):
            condition = self.expression_to_text(
                statement.condition
            )

            explanations.append(
                f"The program checks the condition {condition}."
            )

            explanations.append(
                "If the condition is true, the then branch is executed."
            )

            explanations.extend(
                self.explain_statement(
                    statement.then_branch
                )
            )

            if statement.else_branch is not None:
                explanations.append(
                    "If the condition is false, the else branch is executed."
                )

                explanations.extend(
                    self.explain_statement(
                        statement.else_branch
                    )
                )

        elif isinstance(statement, WhileStatement):
            condition = self.expression_to_text(
                statement.condition
            )

            explanations.append(
                f"The program repeatedly checks the condition {condition}."
            )

            explanations.extend(
                self.explain_statement(
                    statement.body
                )
            )

        elif isinstance(statement, ReturnStatement):
            if statement.value is not None:
                value = self.expression_to_text(
                    statement.value
                )

                explanations.append(
                    f"The function returns {value}."
                )
            else:
                explanations.append(
                    "The function returns without a value."
                )

        elif isinstance(statement, Block):
            explanations.extend(
                self.explain_block(statement)
            )

        return explanations

    def expression_to_text(self, expression):
        if isinstance(expression, Identifier):
            return expression.name

        if isinstance(expression, Literal):
            return str(expression.value)

        if isinstance(expression, BinaryOperation):
            left = self.expression_to_text(
                expression.left
            )

            right = self.expression_to_text(
                expression.right
            )

            return f"({left} {expression.operator} {right})"

        if isinstance(expression, UnaryOperation):
            operand = self.expression_to_text(
                expression.operand
            )

            return f"({expression.operator}{operand})"

        return str(expression)