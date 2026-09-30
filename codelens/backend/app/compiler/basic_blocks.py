from dataclasses import dataclass
from typing import List

from .tac import TACInstruction


@dataclass
class BasicBlock:
    id: int
    instructions: List[TACInstruction]

    def __str__(self):
        lines = [f"B{self.id}"]

        for instruction in self.instructions:
            lines.append(f"    {instruction}")

        return "\n".join(lines)


class BasicBlockBuilder:
    def build(self, instructions: List[TACInstruction]) -> List[BasicBlock]:
        if not instructions:
            return []

        leaders = self.find_leaders(instructions)

        blocks = []

        for index, start in enumerate(leaders):
            if index + 1 < len(leaders):
                end = leaders[index + 1]
            else:
                end = len(instructions)

            block_instructions = instructions[start:end]

            blocks.append(
                BasicBlock(
                    id=index + 1,
                    instructions=block_instructions,
                )
            )

        return blocks

    def find_leaders(self, instructions: List[TACInstruction]) -> List[int]:
        leaders = {0}

        label_positions = {}

        for index, instruction in enumerate(instructions):
            if instruction.operator == "label":
                label_positions[instruction.result] = index

        for index, instruction in enumerate(instructions):
            if instruction.operator == "goto":
                if instruction.result in label_positions:
                    leaders.add(label_positions[instruction.result])

                if index + 1 < len(instructions):
                    leaders.add(index + 1)

            elif instruction.operator == "if":
                if instruction.result in label_positions:
                    leaders.add(label_positions[instruction.result])

                if index + 1 < len(instructions):
                    leaders.add(index + 1)

            elif instruction.operator == "return":
                if index + 1 < len(instructions):
                    leaders.add(index + 1)

        return sorted(leaders)