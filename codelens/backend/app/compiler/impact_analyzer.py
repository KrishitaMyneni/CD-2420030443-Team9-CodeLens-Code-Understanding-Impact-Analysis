from dataclasses import dataclass
from typing import List, Optional

from .ast_nodes import (
    BinaryOperation,
    UnaryOperation,
    Identifier,
)


@dataclass
class Impact:
    impact_type: str
    description: str
    path: str


class ImpactAnalyzer:
    def analyze(
        self,
        ast,
        changes,
        cfg=None,
        def_use=None,
    ):
        impacts = []

        for change in changes:
            self.analyze_change(
                ast,
                change,
                impacts,
            )

        if cfg is not None:
            self.analyze_cfg_impact(
                cfg,
                impacts,
            )

        if def_use is not None:
            self.analyze_data_dependency(
                def_use,
                impacts,
                cfg,
            )

        return impacts

    def analyze_change(
        self,
        ast,
        change,
        impacts: List[Impact],
    ):
        path_parts = self.get_path_parts(
            change.path
        )

        node = self.find_node(
            ast,
            path_parts,
        )

        if node is None:
            return

        if change.path.endswith(".operator"):
            self.analyze_operator_change(
                ast,
                path_parts,
                impacts,
            )

        elif change.path.endswith(".name"):
            impacts.append(
                Impact(
                    impact_type="variable",
                    description=(
                        f"Variable name changed at "
                        f"{change.path}."
                    ),
                    path=change.path,
                )
            )

        elif change.path.endswith(".condition"):
            impacts.append(
                Impact(
                    impact_type="condition",
                    description=(
                        "A control-flow condition "
                        "was changed."
                    ),
                    path=change.path,
                )
            )

    def analyze_operator_change(
        self,
        ast,
        path_parts,
        impacts: List[Impact],
    ):
        parent_path = path_parts[:-1]

        node = self.find_node(
            ast,
            parent_path,
        )

        if not isinstance(
            node,
            BinaryOperation,
        ):
            return

        impacts.append(
            Impact(
                impact_type="condition",
                description=(
                    f"Condition operator "
                    f"'{node.operator}' controls "
                    f"a program branch."
                ),
                path=".".join(parent_path),
            )
        )

        variables = self.extract_identifiers(
            node,
        )

        for variable in variables:
            impacts.append(
                Impact(
                    impact_type="variable",
                    description=(
                        f"Variable '{variable}' "
                        f"is used by the changed "
                        f"condition."
                    ),
                    path=".".join(parent_path),
                )
            )

        statement_path = (
            self.find_containing_statement(
                ast,
                parent_path,
            )
        )

        if statement_path:
            impacts.append(
                Impact(
                    impact_type="control_flow",
                    description=(
                        "The changed condition "
                        "can alter which branch "
                        "of the program executes."
                    ),
                    path=statement_path,
                )
            )

    def analyze_cfg_impact(
        self,
        cfg,
        impacts: List[Impact],
    ):
        control_flow_impacts = [
            impact
            for impact in impacts
            if impact.impact_type
            == "control_flow"
        ]

        if not control_flow_impacts:
            return

        for impact in control_flow_impacts:
            block_id = self.find_block_for_statement(
                cfg,
                impact.path,
            )

            if block_id is None:
                continue

            node = cfg.get_node(block_id)

            if node is None:
                continue

            successors = sorted(
                node.successors
            )

            if len(successors) <= 1:
                continue

            successor_text = ", ".join(
                f"B{successor}"
                for successor in successors
            )

            impacts.append(
                Impact(
                    impact_type="basic_block",
                    description=(
                        f"Changed condition affects "
                        f"branching from B{block_id} "
                        f"to {successor_text}."
                    ),
                    path=f"B{block_id}",
                )
            )

            for successor in successors:
                self.trace_affected_path(
                    cfg,
                    block_id,
                    successor,
                    impacts,
                    visited=set(),
                )

    def find_block_for_statement(
        self,
        cfg,
        statement_path: str,
    ) -> Optional[int]:
        branching_blocks = []

        for block_id, node in cfg.nodes.items():
            if len(node.successors) > 1:
                branching_blocks.append(
                    block_id
                )

        if not branching_blocks:
            return None

        return branching_blocks[0]

    def trace_affected_path(
        self,
        cfg,
        from_block,
        current_block,
        impacts,
        visited,
        path=None,
    ):
        if path is None:
            path = [from_block]

        if current_block in visited:
            return

        visited = visited.copy()
        visited.add(current_block)

        path = path + [current_block]

        node = cfg.get_node(current_block)

        if node is None:
            return

        # If this block contains a return,
        # this is a complete affected path.
        for instruction in node.block.instructions:
            if instruction.operator == "return":
                path_text = " -> ".join(
                    f"B{block_id}"
                    for block_id in path
                )

                impacts.append(
                    Impact(
                        impact_type="affected_path",
                        description=(
                            f"Affected execution path "
                            f"reaches B{current_block}."
                        ),
                        path=path_text,
                    )
                )

                return_value = instruction.arg1

                if return_value:
                    description = (
                        f"Affected path reaches "
                        f"B{current_block}, which "
                        f"returns {return_value}."
                    )
                else:
                    description = (
                        f"Affected path reaches "
                        f"B{current_block}, which "
                        f"returns."
                    )

                impacts.append(
                    Impact(
                        impact_type="return",
                        description=description,
                        path=path_text,
                    )
                )

                return

        # Continue tracing through the CFG.
        for successor in sorted(
            node.successors
        ):
            self.trace_affected_path(
                cfg,
                current_block,
                successor,
                impacts,
                visited,
                path,
            )

    def analyze_data_dependency(
        self,
        def_use,
        impacts: List[Impact],
        cfg=None,
    ):
        changed_variables = (
            self.get_changed_variables(
                impacts
            )
        )

        if not changed_variables:
            return

        affected_blocks = set()

        for impact in impacts:
            if impact.impact_type != "affected_path":
                continue

            parts = impact.path.split("->")

            for part in parts:
                block_text = part.strip()

                if block_text.startswith("B"):
                    try:
                        affected_blocks.add(
                            int(
                                block_text[1:]
                            )
                        )
                    except ValueError:
                        pass

        for definition, uses in def_use.items():
            if definition.variable not in changed_variables:
                continue

            for use in sorted(
                uses,
                key=lambda item: (
                    item.block_id,
                    item.instruction_index,
                ),
            ):
                if (
                    use.block_id
                    not in affected_blocks
                ):
                    continue

                impacts.append(
                    Impact(
                        impact_type="data_dependency",
                        description=(
                            f"Variable "
                            f"'{definition.variable}' "
                            f"is defined at B"
                            f"{definition.block_id} "
                            f"and used at B"
                            f"{use.block_id} "
                            f"on an affected path."
                        ),
                        path=(
                            f"B{definition.block_id}"
                            f" -> "
                            f"B{use.block_id}"
                        ),
                    )
                )

    def get_changed_variables(
        self,
        impacts,
    ):
        variables = set()

        for impact in impacts:
            if impact.impact_type != "variable":
                continue

            description = impact.description

            prefix = "Variable '"

            if prefix not in description:
                continue

            start = description.find(
                prefix
            )

            start += len(prefix)

            end = description.find(
                "'",
                start,
            )

            if end == -1:
                continue

            variable = description[
                start:end
            ]

            variables.add(variable)

        return variables

    def find_node(
        self,
        root,
        path_parts,
    ):
        node = root

        for part in path_parts:
            if not part:
                continue

            if "[" in part and part.endswith("]"):
                field_name = part[
                    :part.index("[")
                ]

                index_text = part[
                    part.index("[") + 1:-1
                ]

                try:
                    index = int(index_text)
                except ValueError:
                    return None

                if not hasattr(
                    node,
                    field_name,
                ):
                    return None

                collection = getattr(
                    node,
                    field_name,
                )

                if index >= len(collection):
                    return None

                node = collection[index]

            else:
                if not hasattr(
                    node,
                    part,
                ):
                    return None

                node = getattr(
                    node,
                    part,
                )

        return node

    def get_path_parts(
        self,
        path: str,
    ):
        parts = path.split(".")

        result = []

        for part in parts:
            if "[" in part:
                field_name = part[
                    :part.index("[")
                ]

                index = part[
                    part.index("["):
                ]

                if field_name:
                    result.append(
                        field_name
                    )

                result.append(index)

            else:
                result.append(part)

        return self.normalize_path_parts(
            result,
        )

    def normalize_path_parts(
        self,
        parts,
    ):
        normalized = []

        for part in parts:
            if part.startswith("["):
                if not normalized:
                    return []

                previous = normalized.pop()

                normalized.append(
                    previous + part
                )

            else:
                normalized.append(part)

        if (
            normalized
            and normalized[0] == "program"
        ):
            normalized = normalized[1:]

        return normalized

    def extract_identifiers(
        self,
        node,
    ):
        variables = []

        self.collect_identifiers(
            node,
            variables,
        )

        return variables

    def collect_identifiers(
        self,
        node,
        variables,
    ):
        if node is None:
            return

        if isinstance(
            node,
            Identifier,
        ):
            if node.name not in variables:
                variables.append(
                    node.name
                )

            return

        if isinstance(
            node,
            BinaryOperation,
        ):
            self.collect_identifiers(
                node.left,
                variables,
            )

            self.collect_identifiers(
                node.right,
                variables,
            )

            return

        if isinstance(
            node,
            UnaryOperation,
        ):
            self.collect_identifiers(
                node.operand,
                variables,
            )

    def find_containing_statement(
        self,
        root,
        target_path,
        current_path="",
    ):
        if root is None:
            return None

        if hasattr(
            root,
            "__dataclass_fields__",
        ):
            for field_name in (
                root.__dataclass_fields__
            ):
                value = getattr(
                    root,
                    field_name,
                )

                field_path = (
                    f"{current_path}."
                    f"{field_name}"
                    if current_path
                    else field_name
                )

                if isinstance(
                    value,
                    list,
                ):
                    for index, item in enumerate(
                        value
                    ):
                        item_path = (
                            f"{field_path}"
                            f"[{index}]"
                        )

                        result = (
                            self.find_containing_statement(
                                item,
                                target_path,
                                item_path,
                            )
                        )

                        if result:
                            return result

                elif hasattr(
                    value,
                    "__dataclass_fields__",
                ):
                    result = (
                        self.find_containing_statement(
                            value,
                            target_path,
                            field_path,
                        )
                    )

                    if result:
                        return result

                if (
                    field_name == "condition"
                    and target_path
                    == self.get_path_parts(
                        field_path
                    )
                ):
                    return current_path

        return None