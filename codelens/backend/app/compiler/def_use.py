from dataclasses import dataclass
from typing import Dict, List, Set

from .basic_blocks import BasicBlock
from .data_flow import Definition
from .tac import TACInstruction


@dataclass(frozen=True)
class Use:
    variable: str
    block_id: int
    instruction_index: int
    instruction: str

    def __str__(self):
        return (
            f"{self.variable} "
            f"(B{self.block_id}, instruction {self.instruction_index})"
        )


class DefUseChain:
    def __init__(
        self,
        blocks: List[BasicBlock],
        reaching_definitions,
    ):
        self.blocks = blocks
        self.reaching_definitions = reaching_definitions

        self.chains: Dict[Definition, Set[Use]] = {}

    def analyze(self):
        self.build_chains()
        return self.chains

    def build_chains(self):
        for definition in self.reaching_definitions.all_definitions:
            self.chains[definition] = set()

        for block in self.blocks:
            reaching = set(
                self.reaching_definitions.in_sets[block.id]
            )

            for index, instruction in enumerate(block.instructions):
                used_variables = self.get_used_variables(
                    instruction
                )

                for variable in used_variables:
                    use = Use(
                        variable=variable,
                        block_id=block.id,
                        instruction_index=index,
                        instruction=str(instruction),
                    )

                    for definition in reaching:
                        if definition.variable == variable:
                            self.chains[definition].add(use)

                if self.is_definition(instruction):
                    definition = self.find_definition(
                        block.id,
                        index,
                    )

                    if definition:
                        reaching = {
                            existing
                            for existing in reaching
                            if existing.variable
                            != definition.variable
                        }

                        reaching.add(definition)

    def get_used_variables(
        self,
        instruction: TACInstruction,
    ) -> List[str]:
        variables = []

        if instruction.arg1:
            if self.is_variable(instruction.arg1):
                variables.append(
                    instruction.arg1
                )

        if instruction.arg2:
            if self.is_variable(instruction.arg2):
                variables.append(
                    instruction.arg2
                )

        return variables

    def is_definition(
        self,
        instruction: TACInstruction,
    ):
        return (
            instruction.operator == "="
            and instruction.result != ""
        )

    def find_definition(
        self,
        block_id: int,
        instruction_index: int,
    ):
        for definition in (
            self.reaching_definitions.all_definitions
        ):
            if (
                definition.block_id == block_id
                and definition.instruction_index
                == instruction_index
            ):
                return definition

        return None

    def is_variable(
        self,
        value: str,
    ) -> bool:
        if not value:
            return False

        if value.startswith("t"):
            return True

        if value[0].isalpha() or value[0] == "_":
            return True

        return False