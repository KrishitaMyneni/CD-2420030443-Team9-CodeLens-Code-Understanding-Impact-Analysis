from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Program:
    declarations: List[object]


@dataclass
class Function:
    return_type: str
    name: str
    parameters: List[object]
    body: object


@dataclass
class Parameter:
    type: str
    name: str


@dataclass
class Block:
    statements: List[object]


@dataclass
class VariableDeclaration:
    type: str
    name: str
    initializer: Optional[object] = None


@dataclass
class Assignment:
    name: str
    value: object


@dataclass
class IfStatement:
    condition: object
    then_branch: object
    else_branch: Optional[object] = None


@dataclass
class WhileStatement:
    condition: object
    body: object


@dataclass
class ReturnStatement:
    value: Optional[object] = None


@dataclass
class BinaryOperation:
    operator: str
    left: object
    right: object


@dataclass
class UnaryOperation:
    operator: str
    operand: object


@dataclass
class Identifier:
    name: str


@dataclass
class Literal:
    value: object