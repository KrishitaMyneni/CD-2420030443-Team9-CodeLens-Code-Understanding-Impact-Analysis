"""
Deterministic evaluator for the CodeLens C subset.

Used by change-impact analysis to derive concrete boundary cases: it
executes the BEFORE and AFTER programs on the same inputs and records how a
watched condition evaluated (operand values, result, branch taken) and what
the function returned. No heuristics, randomness or ML are involved.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

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


COMPARISON_OPERATORS = {"<", "<=", ">", ">=", "==", "!="}

PRECEDENCE = {
    "==": 1,
    "!=": 1,
    "<": 2,
    "<=": 2,
    ">": 2,
    ">=": 2,
    "+": 3,
    "-": 3,
    "*": 4,
    "/": 4,
}


class EvaluationError(Exception):
    pass


class _ReturnSignal(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value


@dataclass
class ConditionEvaluation:
    key: str
    left: object
    right: object
    operator: Optional[str]
    result: bool
    values: Dict[str, object]
    branch: str


@dataclass
class ExecutionResult:
    function: Optional[str]
    arguments: Dict[str, object]
    return_value: object = None
    returned: bool = False
    error: Optional[str] = None
    steps: int = 0
    trace: List[ConditionEvaluation] = field(default_factory=list)

    def first_evaluation(self, key):
        for evaluation in self.trace:
            if evaluation.key == key:
                return evaluation

        return None


def expression_to_source(expression, env=None):
    """Render an expression as C-like source text with minimal parens.

    When `env` is given, identifiers are replaced by their values, which
    produces text such as `10 > 10` for `y > 10`.
    """
    if isinstance(expression, Identifier):
        if env is not None and expression.name in env:
            return format_number(env[expression.name])

        return expression.name

    if isinstance(expression, Literal):
        return format_number(expression.value)

    if isinstance(expression, UnaryOperation):
        operand = expression_to_source(expression.operand, env)

        if isinstance(expression.operand, BinaryOperation):
            operand = f"({operand})"

        return f"{expression.operator}{operand}"

    if isinstance(expression, BinaryOperation):
        own = PRECEDENCE.get(expression.operator, 0)

        left = expression_to_source(expression.left, env)
        right = expression_to_source(expression.right, env)

        if (
            isinstance(expression.left, BinaryOperation)
            and PRECEDENCE.get(expression.left.operator, 0) < own
        ):
            left = f"({left})"

        if (
            isinstance(expression.right, BinaryOperation)
            and PRECEDENCE.get(expression.right.operator, 0) <= own
        ):
            right = f"({right})"

        return f"{left} {expression.operator} {right}"

    if expression is None:
        return ""

    return str(expression)


def format_number(value):
    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, float) and value.is_integer():
        return str(value)

    return str(value)


def collect_identifiers(expression, names=None):
    if names is None:
        names = []

    if isinstance(expression, Identifier):
        if expression.name not in names:
            names.append(expression.name)

    elif isinstance(expression, BinaryOperation):
        collect_identifiers(expression.left, names)
        collect_identifiers(expression.right, names)

    elif isinstance(expression, UnaryOperation):
        collect_identifiers(expression.operand, names)

    return names


def collect_numeric_literals(node, values=None):
    """Collect every numeric literal inside an AST subtree."""
    if values is None:
        values = []

    if isinstance(node, Literal):
        if isinstance(node.value, (int, float)) and node.value not in values:
            values.append(node.value)

        return values

    if isinstance(node, list):
        for item in node:
            collect_numeric_literals(item, values)

        return values

    if hasattr(node, "__dataclass_fields__"):
        for field_name in node.__dataclass_fields__:
            collect_numeric_literals(getattr(node, field_name), values)

    return values


def apply_binary(operator, left, right):
    if operator == "+":
        return left + right

    if operator == "-":
        return left - right

    if operator == "*":
        return left * right

    if operator == "/":
        if right == 0:
            raise EvaluationError("Division by zero.")

        if isinstance(left, int) and isinstance(right, int):
            # C integer division truncates toward zero.
            quotient = abs(left) // abs(right)

            return quotient if (left >= 0) == (right >= 0) else -quotient

        return left / right

    if operator == "<":
        return 1 if left < right else 0

    if operator == "<=":
        return 1 if left <= right else 0

    if operator == ">":
        return 1 if left > right else 0

    if operator == ">=":
        return 1 if left >= right else 0

    if operator == "==":
        return 1 if left == right else 0

    if operator == "!=":
        return 1 if left != right else 0

    raise EvaluationError(f"Unsupported operator '{operator}'.")


class ProgramEvaluator:
    def __init__(self, ast, max_steps: int = 10000):
        self.ast = ast
        self.max_steps = max_steps

        self.env: Dict[str, object] = {}
        self.types: Dict[str, str] = {}
        self.watch: Dict[int, str] = {}
        self.trace: List[ConditionEvaluation] = []
        self.steps = 0

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def entry_function(self):
        if not isinstance(self.ast, Program):
            return None

        functions = [
            declaration
            for declaration in self.ast.declarations
            if isinstance(declaration, Function)
        ]

        for function in functions:
            if function.name == "main":
                return function

        return functions[0] if functions else None

    def parameter_names(self):
        function = self.entry_function()

        if function is None:
            return []

        return [parameter.name for parameter in function.parameters]

    def run(self, arguments=None, watch=None) -> ExecutionResult:
        arguments = dict(arguments or {})
        function = self.entry_function()

        result = ExecutionResult(
            function=function.name if function else None,
            arguments=arguments,
        )

        if function is None:
            result.error = "No function to execute."
            return result

        self.env = {}
        self.types = {}
        self.trace = []
        self.steps = 0
        self.watch = {
            id(node): key
            for key, node in (watch or {}).items()
            if node is not None
        }

        for parameter in function.parameters:
            self.types[parameter.name] = parameter.type
            self.env[parameter.name] = self.coerce(
                parameter.name,
                arguments.get(parameter.name, 0),
            )

        try:
            self.execute(function.body)
        except _ReturnSignal as signal:
            result.return_value = signal.value
            result.returned = True
        except EvaluationError as error:
            result.error = str(error)
        except RecursionError:
            result.error = "Program is too deeply nested to evaluate."

        result.steps = self.steps
        result.trace = list(self.trace)

        return result

    # --------------------------------------------------
    # Statements
    # --------------------------------------------------

    def tick(self):
        self.steps += 1

        if self.steps > self.max_steps:
            raise EvaluationError(
                f"Execution exceeded {self.max_steps} steps "
                f"(possible infinite loop)."
            )

    def execute(self, node):
        if node is None:
            return

        self.tick()

        if isinstance(node, Block):
            for statement in node.statements:
                self.execute(statement)

        elif isinstance(node, VariableDeclaration):
            self.types[node.name] = node.type
            value = (
                self.evaluate(node.initializer)
                if node.initializer is not None
                else 0
            )
            self.env[node.name] = self.coerce(node.name, value)

        elif isinstance(node, Assignment):
            value = self.evaluate(node.value)
            self.env[node.name] = self.coerce(node.name, value)

        elif isinstance(node, IfStatement):
            truth = self.evaluate_condition(
                node.condition,
                "then",
                "else" if node.else_branch is not None else "skip",
            )

            if truth:
                self.execute(node.then_branch)
            elif node.else_branch is not None:
                self.execute(node.else_branch)

        elif isinstance(node, WhileStatement):
            while self.evaluate_condition(
                node.condition,
                "enter loop",
                "exit loop",
            ):
                self.execute(node.body)

        elif isinstance(node, ReturnStatement):
            value = (
                self.evaluate(node.value)
                if node.value is not None
                else None
            )
            raise _ReturnSignal(value)

        else:
            # Expression statement.
            self.evaluate(node)

    def evaluate_condition(self, condition, true_branch, false_branch):
        value = self.evaluate(condition)
        truth = bool(value)

        key = self.watch.get(id(condition))

        if key is not None:
            names = collect_identifiers(condition)

            left = right = None
            operator = None

            if isinstance(condition, BinaryOperation):
                operator = condition.operator
                left = self.evaluate(condition.left)
                right = self.evaluate(condition.right)

            self.trace.append(
                ConditionEvaluation(
                    key=key,
                    left=left,
                    right=right,
                    operator=operator,
                    result=truth,
                    values={
                        name: self.env.get(name)
                        for name in names
                        if name in self.env
                    },
                    branch=true_branch if truth else false_branch,
                )
            )

        return truth

    # --------------------------------------------------
    # Expressions
    # --------------------------------------------------

    def evaluate(self, node):
        if isinstance(node, Literal):
            return node.value

        if isinstance(node, Identifier):
            if node.name not in self.env:
                raise EvaluationError(
                    f"Variable '{node.name}' is used before it has a value."
                )

            return self.env[node.name]

        if isinstance(node, UnaryOperation):
            value = self.evaluate(node.operand)

            if node.operator == "-":
                return -value

            raise EvaluationError(
                f"Unsupported unary operator '{node.operator}'."
            )

        if isinstance(node, BinaryOperation):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)

            return apply_binary(node.operator, left, right)

        raise EvaluationError(
            f"Cannot evaluate {type(node).__name__}."
        )

    def coerce(self, name, value):
        declared = self.types.get(name)

        if value is None:
            return 0

        if declared in ("int", "char") and isinstance(value, float):
            return int(value)

        if declared == "float" and isinstance(value, int):
            return float(value)

        return value


def evaluate_expression(expression, env):
    """Evaluate a standalone expression with the given variable values."""
    evaluator = ProgramEvaluator(None)
    evaluator.env = dict(env)

    return evaluator.evaluate(expression)
