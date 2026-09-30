from dataclasses import dataclass, field
from typing import Dict, List, Set
from .basic_blocks import BasicBlock


@dataclass
class CFGNode:
    block: BasicBlock
    successors: Set[int] = field(default_factory=set)
    predecessors: Set[int] = field(default_factory=set)


class ControlFlowGraph:
    def __init__(self, blocks: List[BasicBlock]):
        self.nodes: Dict[int, CFGNode] = {
            block.id: CFGNode(block=block)
            for block in blocks
        }

    def add_edge(self, from_block: int, to_block: int):
        if from_block not in self.nodes or to_block not in self.nodes:
            return

        self.nodes[from_block].successors.add(to_block)
        self.nodes[to_block].predecessors.add(from_block)

    def get_node(self, block_id: int):
        return self.nodes.get(block_id)

    def get_edges(self):
        edges = []

        for block_id, node in self.nodes.items():
            for successor in sorted(node.successors):
                edges.append((block_id, successor))

        return edges


class CFGBuilder:
    def build(self, blocks: List[BasicBlock]) -> ControlFlowGraph:
        cfg = ControlFlowGraph(blocks)

        if not blocks:
            return cfg

        label_to_block = self.build_label_map(blocks)

        for index, block in enumerate(blocks):
            if not block.instructions:
                continue

            last_instruction = block.instructions[-1]

            if last_instruction.operator == "goto":
                target_block = label_to_block.get(last_instruction.result)

                if target_block is not None:
                    cfg.add_edge(block.id, target_block)

            elif last_instruction.operator == "if":
                target_block = label_to_block.get(last_instruction.result)

                if target_block is not None:
                    cfg.add_edge(block.id, target_block)

                if index + 1 < len(blocks):
                    next_block = blocks[index + 1]
                    cfg.add_edge(block.id, next_block.id)

            elif last_instruction.operator == "return":
                continue

            else:
                if index + 1 < len(blocks):
                    next_block = blocks[index + 1]
                    cfg.add_edge(block.id, next_block.id)

        return cfg

    def build_label_map(self, blocks: List[BasicBlock]):
        label_to_block = {}

        for block in blocks:
            for instruction in block.instructions:
                if instruction.operator == "label":
                    label_to_block[instruction.result] = block.id

        return label_to_block