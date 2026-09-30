from dataclasses import dataclass
from typing import Dict, List, Set

from .basic_blocks import BasicBlock
from .tac import TACInstruction
from .cfg import ControlFlowGraph


@dataclass(frozen=True)
class Definition:
    variable: str
    block_id: int
    instruction_index: int
    value: str

    def __str__(self):
        return (
            f"{self.variable} "
            f"(B{self.block_id}, instruction {self.instruction_index})"
        )


class ReachingDefinitions:
    def __init__(
        self,
        blocks: List[BasicBlock],
        cfg: ControlFlowGraph,
    ):
        self.blocks = blocks
        self.cfg = cfg

        self.gen: Dict[int, Set[Definition]] = {}
        self.kill: Dict[int, Set[Definition]] = {}

        self.in_sets: Dict[int, Set[Definition]] = {}
        self.out_sets: Dict[int, Set[Definition]] = {}

        self.all_definitions: Set[Definition] = set()

    def analyze(self):
        self.collect_definitions()
        self.compute_gen_kill()
        self.compute_reaching_definitions()

        return {
            "gen": self.gen,
            "kill": self.kill,
            "in": self.in_sets,
            "out": self.out_sets,
        }

    def collect_definitions(self):
        for block in self.blocks:
            for index, instruction in enumerate(block.instructions):
                if self.is_definition(instruction):
                    definition = Definition(
                        variable=instruction.result,
                        block_id=block.id,
                        instruction_index=index,
                        value=self.get_definition_value(instruction),
                    )

                    self.all_definitions.add(definition)

    def compute_gen_kill(self):
        for block in self.blocks:
            block_definitions = set()

            for index, instruction in enumerate(block.instructions):
                if self.is_definition(instruction):
                    definition = self.find_definition(
                        block.id,
                        index,
                    )

                    if definition:
                        block_definitions.add(definition)

            self.gen[block.id] = block_definitions

            defined_variables = {
                definition.variable
                for definition in block_definitions
            }

            self.kill[block.id] = {
                definition
                for definition in self.all_definitions
                if definition.variable in defined_variables
                and definition.block_id != block.id
            }

    def compute_reaching_definitions(self):
        for block in self.blocks:
            self.in_sets[block.id] = set()
            self.out_sets[block.id] = set(self.gen[block.id])

        changed = True

        while changed:
            changed = False

            for block in self.blocks:
                predecessors = self.cfg.get_node(block.id).predecessors

                new_in = set()

                for predecessor in predecessors:
                    new_in.update(self.out_sets[predecessor])

                new_out = self.gen[block.id] | (
                    new_in - self.kill[block.id]
                )

                if new_in != self.in_sets[block.id]:
                    self.in_sets[block.id] = new_in
                    changed = True

                if new_out != self.out_sets[block.id]:
                    self.out_sets[block.id] = new_out
                    changed = True

    def is_definition(self, instruction: TACInstruction):
        return (
            instruction.operator == "="
            and instruction.result != ""
        )

    def get_definition_value(self, instruction: TACInstruction):
        return instruction.arg1

    def find_definition(
        self,
        block_id: int,
        instruction_index: int,
    ):
        for definition in self.all_definitions:
            if (
                definition.block_id == block_id
                and definition.instruction_index == instruction_index
            ):
                return definition

        return None