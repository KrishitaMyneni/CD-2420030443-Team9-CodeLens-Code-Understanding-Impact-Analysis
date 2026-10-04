import itertools
from dataclasses import dataclass
from typing import Dict, List, Optional

from .ast_nodes import (
    Assignment,
    BinaryOperation,
    Block,
    Function,
    Identifier,
    IfStatement,
    Literal,
    Program,
    ReturnStatement,
    UnaryOperation,
    VariableDeclaration,
    WhileStatement,
)
from .program_evaluator import (
    COMPARISON_OPERATORS,
    EvaluationError,
    ProgramEvaluator,
    collect_numeric_literals,
    evaluate_expression,
    expression_to_source,
)


@dataclass
class Impact:
    impact_type: str
    description: str
    path: str


STATEMENT_TYPES = (
    VariableDeclaration,
    Assignment,
    IfStatement,
    WhileStatement,
    ReturnStatement,
)

CONTROL_TYPES = (IfStatement, WhileStatement)

# Impact types grouped into the categories shown in the impact report.
IMPACT_GROUPS = {
    "variables": ("variable",),
    "conditions": ("condition", "boundary_condition"),
    "control_flow": ("control_flow",),
    "basic_blocks": ("basic_block",),
    "paths": ("affected_path",),
    "returns": ("return",),
    "data_dependencies": ("data_dependency",),
    "statements": (
        "added_statement",
        "removed_statement",
        "modified_statement",
    ),
}

MAX_BOUNDARY_CASES = 3
MAX_CANDIDATE_INPUTS = 2000


class ImpactAnalyzer:

    def __init__(self):
        self.reset()

    def reset(self):
        # Branch points whose behaviour may change. Each entry is a dict
        # with "side" ("new" / "old") and either "parts" (AST statement
        # path) or "block_id".
        self.control_points = []
        # Pairs of (old statement parts, new statement parts) for
        # conditionals whose condition expression changed.
        self.condition_changes = []
        # Variables whose definition (declaration / assignment) changed.
        self.modified_variables = set()
        # Blocks of the NEW program that lie on an affected path.
        self.affected_blocks = set()
        # Conditionals whose condition now depends on a changed value.
        self.dependent_conditions = []

        self.boundary_cases = []
        self.execution = None

        self._return_text = {"new": {}, "old": {}}

    # ==================================================
    # Entry point
    # ==================================================

    def analyze(
        self,
        old_ast,
        new_ast,
        changes,
        cfg=None,
        def_use=None,
        old_cfg=None,
    ):
        self.reset()

        impacts = []

        for change in changes:
            self.analyze_change(
                old_ast,
                new_ast,
                change,
                impacts,
            )

        if cfg is not None:
            self._return_text["new"] = self.build_return_text_map(
                new_ast,
                cfg,
            )

            self.analyze_value_propagation(
                new_ast,
                cfg,
                impacts,
            )

        if old_cfg is not None:
            self._return_text["old"] = self.build_return_text_map(
                old_ast,
                old_cfg,
            )

        if cfg is not None or old_cfg is not None:
            self.analyze_cfg_impact(
                new_ast,
                cfg,
                impacts,
                old_ast=old_ast,
                old_cfg=old_cfg,
            )

        if def_use is not None:
            self.analyze_data_dependency(
                def_use,
                impacts,
                cfg,
            )

        if changes:
            self.boundary_cases = self.analyze_boundary_cases(
                old_ast,
                new_ast,
            )
            self.execution = self.compare_execution(
                old_ast,
                new_ast,
            )

        return self.deduplicate_impacts(impacts)

    # ==================================================
    # Per-change analysis
    # ==================================================

    def analyze_change(
        self,
        old_ast,
        new_ast,
        change,
        impacts: List[Impact],
    ):
        new_parts = self.get_path_parts(
            getattr(change, "new_path", None) or change.path
        )
        old_parts = self.get_path_parts(
            getattr(change, "old_path", None) or change.path
        )

        old_node = self.find_node(
            old_ast,
            old_parts,
        )

        new_node = self.find_node(
            new_ast,
            new_parts,
        )

        if change.change_type == "modified":
            self.analyze_modified_change(
                old_ast,
                new_ast,
                old_node,
                new_node,
                change,
                new_parts,
                impacts,
                old_parts=old_parts,
            )

        elif change.change_type == "added":
            impacts.append(
                Impact(
                    impact_type="added_statement",
                    description=(
                        f"Added code at {change.path}."
                    ),
                    path=change.path,
                )
            )

            self.analyze_added_or_removed_node(
                new_ast,
                new_node,
                change.path,
                impacts,
                "added",
            )

            self.analyze_branch_shape_change(
                new_ast,
                new_parts,
                impacts,
                "new",
                "added",
            )

        elif change.change_type == "removed":
            impacts.append(
                Impact(
                    impact_type="removed_statement",
                    description=(
                        f"Removed code at {change.path}."
                    ),
                    path=change.path,
                )
            )

            self.analyze_added_or_removed_node(
                old_ast,
                old_node,
                change.path,
                impacts,
                "removed",
            )

            self.analyze_branch_shape_change(
                old_ast,
                old_parts,
                impacts,
                "old",
                "removed",
            )

    def analyze_modified_change(
        self,
        old_ast,
        new_ast,
        old_node,
        new_node,
        change,
        path_parts,
        impacts,
        old_parts=None,
    ):
        if old_parts is None:
            old_parts = path_parts

        condition_index = self.find_condition_index(path_parts)
        old_condition_index = self.find_condition_index(old_parts)

        if (
            condition_index is not None
            and old_condition_index is not None
        ):
            new_statement = self.find_node(
                new_ast,
                path_parts[:condition_index],
            )
            old_statement = self.find_node(
                old_ast,
                old_parts[:old_condition_index],
            )

            if isinstance(new_statement, CONTROL_TYPES) and isinstance(
                old_statement,
                CONTROL_TYPES,
            ):
                if change.path.endswith(".operator"):
                    self.analyze_operator_change(
                        old_ast,
                        new_ast,
                        old_node,
                        new_node,
                        path_parts,
                        impacts,
                        old_parts=old_parts,
                    )
                else:
                    self.analyze_condition_change(
                        old_statement,
                        new_statement,
                        old_parts[:old_condition_index],
                        path_parts[:condition_index],
                        change,
                        impacts,
                    )

                return

        if change.path.endswith(".name"):
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

            for name in (change.old_value, change.new_value):
                if isinstance(name, str) and name:
                    impacts.append(
                        Impact(
                            impact_type="variable",
                            description=(
                                f"Variable '{name}' is affected by "
                                f"the renamed reference."
                            ),
                            path=change.path,
                        )
                    )

        impacts.append(
            Impact(
                impact_type="modified_statement",
                description=(
                    f"Statement or expression modified "
                    f"at {change.path}."
                ),
                path=change.path,
            )
        )

        self.analyze_statement_change(
            old_ast,
            new_ast,
            old_parts,
            path_parts,
            change,
            impacts,
        )

    def analyze_operator_change(
        self,
        old_ast,
        new_ast,
        old_node,
        new_node,
        path_parts,
        impacts,
        old_parts=None,
    ):
        if old_parts is None:
            old_parts = path_parts

        parent_path = path_parts[:-1]
        old_parent_path = old_parts[:-1]

        old_operation = self.find_node(
            old_ast,
            old_parent_path,
        )

        new_operation = self.find_node(
            new_ast,
            parent_path,
        )

        if not isinstance(
            old_operation,
            BinaryOperation,
        ):
            return

        if not isinstance(
            new_operation,
            BinaryOperation,
        ):
            return

        impacts.append(
            Impact(
                impact_type="condition",
                description=(
                    f"Condition operator changed "
                    f"from '{old_operation.operator}' "
                    f"to '{new_operation.operator}' "
                    f"({expression_to_source(old_operation)} → "
                    f"{expression_to_source(new_operation)})."
                ),
                path=".".join(parent_path),
            )
        )

        variables = self.extract_identifiers(
            new_operation,
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

        condition_index = self.find_condition_index(parent_path)
        old_condition_index = self.find_condition_index(old_parent_path)

        if condition_index is not None:
            statement_parts = parent_path[:condition_index]
            old_statement_parts = (
                old_parent_path[:old_condition_index]
                if old_condition_index is not None
                else statement_parts
            )
            statement_path = ".".join(statement_parts)
        else:
            statement_path = self.find_containing_statement(
                new_ast,
                parent_path,
            )
            statement_parts = (
                self.get_path_parts(statement_path)
                if statement_path
                else None
            )
            old_statement_parts = statement_parts

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

            self.add_control_point("new", parts=statement_parts)
            self.add_condition_change(
                old_statement_parts,
                statement_parts,
            )

        if self.is_boundary_operator_change(
            old_operation.operator,
            new_operation.operator,
        ):
            impacts.append(
                Impact(
                    impact_type="boundary_condition",
                    description=(
                        f"Boundary behavior changed from "
                        f"'{old_operation.operator}' to "
                        f"'{new_operation.operator}'. "
                        f"The boundary value itself may "
                        f"now select a different branch."
                    ),
                    path=".".join(parent_path),
                )
            )

    def analyze_condition_change(
        self,
        old_statement,
        new_statement,
        old_statement_parts,
        new_statement_parts,
        change,
        impacts,
    ):
        statement_path = ".".join(new_statement_parts)
        condition_path = f"{statement_path}.condition"

        old_text = expression_to_source(old_statement.condition)
        new_text = expression_to_source(new_statement.condition)

        impacts.append(
            Impact(
                impact_type="condition",
                description=(
                    f"A control-flow condition was changed "
                    f"({old_text} → {new_text})."
                ),
                path=condition_path,
            )
        )

        for variable in self.extract_identifiers(
            new_statement.condition
        ):
            impacts.append(
                Impact(
                    impact_type="variable",
                    description=(
                        f"Variable '{variable}' "
                        f"is used by the changed "
                        f"condition."
                    ),
                    path=condition_path,
                )
            )

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

        if (
            isinstance(change.old_value, (int, float))
            and isinstance(change.new_value, (int, float))
            and not isinstance(change.old_value, bool)
        ):
            low = min(change.old_value, change.new_value)
            high = max(change.old_value, change.new_value)

            impacts.append(
                Impact(
                    impact_type="boundary_condition",
                    description=(
                        f"Comparison threshold changed from "
                        f"{change.old_value} to {change.new_value}. "
                        f"Values between {low} and {high} may now "
                        f"select a different branch."
                    ),
                    path=condition_path,
                )
            )

        self.add_control_point("new", parts=new_statement_parts)
        self.add_condition_change(
            old_statement_parts,
            new_statement_parts,
        )

    def analyze_statement_change(
        self,
        old_ast,
        new_ast,
        old_parts,
        new_parts,
        change,
        impacts,
    ):
        """Classify a modification that is not inside a condition."""
        new_statement, new_statement_parts = self.find_enclosing_statement(
            new_ast,
            new_parts,
        )
        old_statement, old_statement_parts = self.find_enclosing_statement(
            old_ast,
            old_parts,
        )

        if new_statement is None and old_statement is None:
            return

        # The statement itself was replaced by a different kind of node.
        if (
            new_statement is not None
            and old_statement is not None
            and type(new_statement) is not type(old_statement)
        ):
            self.analyze_added_or_removed_node(
                old_ast,
                old_statement,
                ".".join(old_statement_parts),
                impacts,
                "removed",
            )
            self.analyze_added_or_removed_node(
                new_ast,
                new_statement,
                ".".join(new_statement_parts),
                impacts,
                "added",
            )
            return

        statement = new_statement or old_statement
        statement_path = ".".join(
            new_statement_parts
            if new_statement is not None
            else old_statement_parts
        )

        if isinstance(statement, (VariableDeclaration, Assignment)):
            names = []

            for node in (old_statement, new_statement):
                name = getattr(node, "name", None)

                if name and name not in names:
                    names.append(name)

            for name in names:
                self.modified_variables.add(name)

                impacts.append(
                    Impact(
                        impact_type="variable",
                        description=(
                            f"Variable '{name}' is defined "
                            f"differently: "
                            f"{self.statement_to_source(old_statement)} → "
                            f"{self.statement_to_source(new_statement)}"
                        ),
                        path=statement_path,
                    )
                )

        elif isinstance(statement, ReturnStatement):
            old_value = expression_to_source(
                getattr(old_statement, "value", None)
            ) or "nothing"
            new_value = expression_to_source(
                getattr(new_statement, "value", None)
            ) or "nothing"

            impacts.append(
                Impact(
                    impact_type="return",
                    description=(
                        f"Return value changed from "
                        f"{old_value} to {new_value}."
                    ),
                    path=statement_path,
                )
            )

    def analyze_branch_shape_change(
        self,
        ast,
        parts,
        impacts,
        side,
        change_type,
    ):
        """An added/removed then/else branch changes the branch itself."""
        if not parts or parts[-1] not in ("then_branch", "else_branch"):
            return

        statement = self.find_node(ast, parts[:-1])

        if not isinstance(statement, CONTROL_TYPES):
            return

        branch_name = parts[-1].replace("_branch", "")
        statement_path = ".".join(parts[:-1])

        impacts.append(
            Impact(
                impact_type="control_flow",
                description=(
                    f"The {branch_name} branch was {change_type}, "
                    f"so the paths leaving this conditional change."
                ),
                path=statement_path,
            )
        )

        self.add_control_point(side, parts=parts[:-1])

    def is_boundary_operator_change(
        self,
        old_operator,
        new_operator,
    ):
        boundary_pairs = {
            (">", ">="),
            (">=", ">"),
            ("<", "<="),
            ("<=", "<"),
            ("==", "!="),
            ("!=", "=="),
        }

        return (
            old_operator,
            new_operator,
        ) in boundary_pairs

    def analyze_added_or_removed_node(
        self,
        ast,
        node,
        path,
        impacts,
        change_type,
    ):
        if node is None:
            return

        side = "new" if change_type == "added" else "old"
        base_parts = self.get_path_parts(path)

        for sub_node, sub_parts in self.iter_statements(node, base_parts):
            sub_path = ".".join(sub_parts) if sub_parts else path

            if isinstance(
                sub_node,
                (IfStatement, WhileStatement),
            ):
                impacts.append(
                    Impact(
                        impact_type="control_flow",
                        description=(
                            f"A {change_type} "
                            f"control-flow statement can "
                            f"change program execution."
                        ),
                        path=sub_path,
                    )
                )

                self.add_control_point(side, parts=sub_parts)

            if isinstance(
                sub_node,
                (
                    VariableDeclaration,
                    Assignment,
                ),
            ):
                name = getattr(
                    sub_node,
                    "name",
                    None,
                )

                if name:
                    self.modified_variables.add(name)

                    impacts.append(
                        Impact(
                            impact_type="variable",
                            description=(
                                f"Variable '{name}' is "
                                f"affected by the "
                                f"{change_type} statement."
                            ),
                            path=sub_path,
                        )
                    )

            if isinstance(
                sub_node,
                ReturnStatement,
            ):
                value = expression_to_source(sub_node.value)
                suffix = f" ({'return ' + value if value else 'return'})"

                impacts.append(
                    Impact(
                        impact_type="return",
                        description=(
                            f"A return statement was "
                            f"{change_type}{suffix}."
                        ),
                        path=sub_path,
                    )
                )

    # ==================================================
    # Data-flow based value propagation (TAC level)
    # ==================================================

    def analyze_value_propagation(
        self,
        ast,
        cfg,
        impacts: List[Impact],
    ):
        """
        Forward-propagate changed variable definitions through the TAC of
        the NEW program until a fixed point is reached. Any variable,
        branch condition or return value computed from a changed variable
        is reported as affected.
        """
        seeds = set(self.modified_variables)

        if not seeds:
            return

        instructions = []

        for block_id in sorted(cfg.nodes):
            for index, instruction in enumerate(
                cfg.nodes[block_id].block.instructions
            ):
                instructions.append((block_id, index, instruction))

        program_variables = {
            instruction.result
            for _, _, instruction in instructions
            if instruction.operator == "="
        }

        origins: Dict[str, set] = {
            variable: {variable}
            for variable in seeds
        }
        defined_at: Dict[str, int] = {}

        changed = True

        while changed:
            changed = False

            for block_id, _, instruction in instructions:
                if instruction.operator in (
                    "label",
                    "goto",
                    "if",
                    "return",
                ):
                    continue

                if not instruction.result:
                    continue

                sources = set()

                for argument in (instruction.arg1, instruction.arg2):
                    if argument in origins:
                        sources |= origins[argument]

                if not sources:
                    continue

                known = origins.setdefault(instruction.result, set())

                if not sources <= known:
                    known |= sources
                    defined_at.setdefault(instruction.result, block_id)
                    changed = True

        for variable in sorted(program_variables - seeds):
            if variable not in origins:
                continue

            source_text = ", ".join(
                f"'{name}'" for name in sorted(origins[variable])
            )

            impacts.append(
                Impact(
                    impact_type="data_dependency",
                    description=(
                        f"Variable '{variable}' depends on changed "
                        f"variable(s) {source_text}, so its value "
                        f"can change too."
                    ),
                    path=f"B{defined_at.get(variable, '?')}",
                )
            )

        for block_id, index, instruction in instructions:
            if instruction.operator == "if" and instruction.arg1 in origins:
                source_text = ", ".join(
                    f"'{name}'"
                    for name in sorted(origins[instruction.arg1])
                )

                impacts.append(
                    Impact(
                        impact_type="condition",
                        description=(
                            f"The branch condition in B{block_id} "
                            f"depends on changed variable(s) "
                            f"{source_text}."
                        ),
                        path=f"B{block_id}",
                    )
                )

                impacts.append(
                    Impact(
                        impact_type="control_flow",
                        description=(
                            f"A changed value of {source_text} can "
                            f"alter which branch executes at "
                            f"B{block_id}."
                        ),
                        path=f"B{block_id}",
                    )
                )

                self.add_control_point("new", block_id=block_id)
                self.dependent_conditions.append(block_id)

            elif (
                instruction.operator == "return"
                and instruction.arg1 in origins
            ):
                source_text = ", ".join(
                    f"'{name}'"
                    for name in sorted(origins[instruction.arg1])
                )
                value_text = self._return_text["new"].get(
                    (block_id, index),
                    instruction.arg1,
                )

                impacts.append(
                    Impact(
                        impact_type="return",
                        description=(
                            f"The value returned at B{block_id} "
                            f"({value_text}) depends on changed "
                            f"variable(s) {source_text}."
                        ),
                        path=f"B{block_id}",
                    )
                )

    # ==================================================
    # CFG / basic block / path impact
    # ==================================================

    def analyze_cfg_impact(
        self,
        ast,
        cfg,
        impacts: List[Impact],
        old_ast=None,
        old_cfg=None,
    ):
        points = list(self.control_points)

        if not points and cfg is not None:
            # Backward-compatible fallback: derive branch points from the
            # control-flow impacts themselves.
            points = [
                {"side": "new", "path": impact.path}
                for impact in impacts
                if impact.impact_type == "control_flow"
            ]

        maps = {
            "new": (
                self.conditional_block_map(ast, cfg)
                if cfg is not None
                else {}
            ),
            "old": (
                self.conditional_block_map(old_ast, old_cfg)
                if old_cfg is not None
                else {}
            ),
        }

        for point in points:
            side = point["side"]
            the_cfg = cfg if side == "new" else old_cfg

            if the_cfg is None:
                continue

            block_id = point.get("block_id")

            if block_id is None and point.get("parts") is not None:
                block_id = maps[side].get(tuple(point["parts"]))

            if block_id is None:
                block_id = self.find_block_for_statement(
                    ast if side == "new" else old_ast,
                    the_cfg,
                    point.get("path"),
                    impacts,
                )

            if block_id is None:
                continue

            node = the_cfg.get_node(block_id)

            if node is None:
                continue

            successors = sorted(
                node.successors
            )

            if len(successors) <= 1:
                continue

            prefix = "" if side == "new" else "In the BEFORE program: "

            successor_text = ", ".join(
                f"B{successor}"
                for successor in successors
            )

            impacts.append(
                Impact(
                    impact_type="basic_block",
                    description=(
                        f"{prefix}Changed condition affects "
                        f"branching from B{block_id} "
                        f"to {successor_text}."
                    ),
                    path=f"B{block_id}",
                )
            )

            true_block, false_block = self.branch_targets(
                the_cfg,
                block_id,
            )

            for successor in successors:
                if successor == true_block:
                    label = "true branch"
                    truth = "true"
                elif successor == false_block:
                    label = "false branch"
                    truth = "false"
                else:
                    label = "branch"
                    truth = "selected"

                impacts.append(
                    Impact(
                        impact_type="basic_block",
                        description=(
                            f"{prefix}B{successor} ({label}) runs when "
                            f"the condition in B{block_id} is {truth}."
                        ),
                        path=f"B{successor}",
                    )
                )

            if side == "new":
                self.affected_blocks.add(block_id)

            for successor in successors:
                self.trace_affected_path(
                    the_cfg,
                    block_id,
                    successor,
                    impacts,
                    visited={block_id},
                    side=side,
                )

    def branch_targets(self, cfg, block_id):
        node = cfg.get_node(block_id)

        if node is None or not node.block.instructions:
            return None, None

        last = node.block.instructions[-1]

        if last.operator != "if":
            return None, None

        true_block = None

        for other_id, other in cfg.nodes.items():
            for instruction in other.block.instructions:
                if (
                    instruction.operator == "label"
                    and instruction.result == last.result
                ):
                    true_block = other_id

        ordered = sorted(cfg.nodes)
        position = ordered.index(block_id)
        false_block = (
            ordered[position + 1]
            if position + 1 < len(ordered)
            else None
        )

        return true_block, false_block

    def find_block_for_statement(
        self,
        ast,
        cfg,
        statement_path,
        impacts=None,
    ) -> Optional[int]:
        # Deterministic mapping first: the k-th conditional in the AST
        # produces the k-th conditional jump in the TAC.
        if statement_path:
            mapping = self.conditional_block_map(ast, cfg)
            block_id = mapping.get(
                tuple(self.get_path_parts(statement_path))
            )

            if block_id is not None:
                return block_id

        # Heuristic fallback (kept from the original implementation).
        variables = set()

        for impact in impacts or []:
            if impact.impact_type == "variable":
                variable = self.extract_variable_name(
                    impact.description
                )

                if variable:
                    variables.add(variable)

        candidates = []

        for block_id, node in cfg.nodes.items():
            if len(node.successors) <= 1:
                continue

            score = 0

            instruction_text = " ".join(
                str(instruction)
                for instruction in node.block.instructions
            )

            for variable in variables:
                if variable in instruction_text:
                    score += 10

            if "if" in instruction_text.lower():
                score += 5

            candidates.append(
                (
                    score,
                    block_id,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        return candidates[0][1]

    def trace_affected_path(
        self,
        cfg,
        from_block,
        current_block,
        impacts,
        visited,
        path=None,
        side="new",
    ):
        if path is None:
            path = [from_block]

        if current_block in visited:
            return

        visited = visited.copy()
        visited.add(current_block)

        path = path + [current_block]

        node = cfg.get_node(
            current_block
        )

        if node is None:
            return

        if side == "new":
            self.affected_blocks.add(current_block)

        prefix = "" if side == "new" else "In the BEFORE program: "
        prefix_lower = "" if side == "new" else "in the BEFORE program "

        path_text = " -> ".join(
            f"B{block_id}"
            for block_id in path
        )

        for index, instruction in enumerate(node.block.instructions):
            if instruction.operator == "return":
                impacts.append(
                    Impact(
                        impact_type="affected_path",
                        description=(
                            f"{prefix}Affected execution path "
                            f"reaches B{current_block}."
                        ),
                        path=path_text,
                    )
                )

                return_value = self._return_text[side].get(
                    (current_block, index),
                    instruction.arg1,
                )

                if return_value:
                    description = (
                        f"{prefix}Affected path reaches "
                        f"B{current_block}, which "
                        f"returns {return_value}."
                    )
                else:
                    description = (
                        f"{prefix}Affected path reaches "
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

        if not node.successors:
            impacts.append(
                Impact(
                    impact_type="affected_path",
                    description=(
                        f"Affected execution path {prefix_lower}"
                        f"reaches the end of the function at "
                        f"B{current_block}."
                    ),
                    path=path_text,
                )
            )
            return

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
                side=side,
            )

    # ==================================================
    # Def-use based dependency impact
    # ==================================================

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

        affected_blocks = set(self.affected_blocks)

        if not affected_blocks:
            for impact in impacts:
                if impact.impact_type != "affected_path":
                    continue

                if impact.description.startswith("In the BEFORE"):
                    continue

                parts = impact.path.split("->")

                for part in parts:
                    block_text = part.strip()

                    if not block_text.startswith("B"):
                        continue

                    try:
                        affected_blocks.add(
                            int(block_text[1:])
                        )
                    except ValueError:
                        continue

        for definition, uses in sorted(
            def_use.items(),
            key=lambda item: (
                item[0].block_id,
                item[0].instruction_index,
            ),
        ):
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
                    affected_blocks
                    and use.block_id
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

            variable = self.extract_variable_name(
                impact.description
            )

            if variable:
                variables.add(variable)

        return variables

    def extract_variable_name(
        self,
        description,
    ):
        prefix = "Variable '"

        if prefix not in description:
            return None

        start = description.find(
            prefix
        )

        start += len(prefix)

        end = description.find(
            "'",
            start,
        )

        if end == -1:
            return None

        return description[
            start:end
        ]

    def deduplicate_impacts(
        self,
        impacts,
    ):
        unique = []
        seen = set()

        for impact in impacts:
            key = (
                impact.impact_type,
                impact.description,
                impact.path,
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(impact)

        return unique

    # ==================================================
    # Boundary cases (deterministic evaluation)
    # ==================================================

    def analyze_boundary_cases(self, old_ast, new_ast):
        targets = self.boundary_targets(old_ast, new_ast)

        if not targets:
            return []

        old_evaluator = ProgramEvaluator(old_ast)
        new_evaluator = ProgramEvaluator(new_ast)

        parameters = new_evaluator.parameter_names()
        candidates = self.candidate_inputs(parameters, old_ast, new_ast)

        cases = []

        for target in targets:
            found = []

            for order, arguments in enumerate(candidates):
                before = old_evaluator.run(
                    arguments,
                    watch={"target": target["old_condition"]},
                )
                after = new_evaluator.run(
                    arguments,
                    watch={"target": target["new_condition"]},
                )

                before_check = before.first_evaluation("target")
                after_check = after.first_evaluation("target")

                if before_check is None or after_check is None:
                    continue

                if before_check.result == after_check.result:
                    continue

                found.append(
                    (
                        self.boundary_distance(after_check),
                        order,
                        self.build_concrete_case(
                            target,
                            arguments,
                            before,
                            after,
                            before_check,
                            after_check,
                        ),
                    )
                )

            selected = self.select_cases(found)

            if not selected and target["explicit"]:
                selected = self.hypothetical_cases(
                    target,
                    new_evaluator,
                    parameters,
                )

            cases.extend(selected)

        return cases

    def boundary_targets(self, old_ast, new_ast):
        targets = []
        seen = set()

        def add(old_parts, new_parts, explicit):
            key = (tuple(old_parts), tuple(new_parts))

            if key in seen:
                return

            old_statement = self.find_node(old_ast, old_parts)
            new_statement = self.find_node(new_ast, new_parts)

            if not isinstance(old_statement, CONTROL_TYPES):
                return

            if not isinstance(new_statement, CONTROL_TYPES):
                return

            seen.add(key)
            targets.append(
                {
                    "old_parts": list(old_parts),
                    "new_parts": list(new_parts),
                    "old_statement": old_statement,
                    "new_statement": new_statement,
                    "old_condition": old_statement.condition,
                    "new_condition": new_statement.condition,
                    "explicit": explicit,
                }
            )

        for old_parts, new_parts in self.condition_changes:
            add(old_parts, new_parts, True)

        if self.dependent_conditions:
            reverse = {}

            for parts, block_id in self._new_conditional_map(
                new_ast
            ).items():
                reverse[block_id] = list(parts)

            for block_id in self.dependent_conditions:
                parts = reverse.get(block_id)

                if parts is not None:
                    add(parts, parts, False)

        return targets

    def _new_conditional_map(self, new_ast):
        paths = []
        self.collect_conditional_paths(new_ast, [], paths)

        # Block ids are not needed here, only the TAC order index; the
        # mapping is rebuilt against the CFG in conditional_block_map.
        return self._conditional_map_cache.get(id(new_ast), {}) if hasattr(
            self, "_conditional_map_cache"
        ) else {}

    def candidate_inputs(self, parameters, old_ast, new_ast):
        if not parameters:
            return [{}]

        literals = set()

        for value in collect_numeric_literals(
            old_ast
        ) + collect_numeric_literals(new_ast):
            if isinstance(value, bool):
                continue

            literals.add(int(value))

        literals.add(0)

        values = set()

        for literal in literals:
            for divisor in (1, 2, 3, 4):
                quotient = int(literal / divisor)
                values.update({quotient - 1, quotient, quotient + 1})

        if len(parameters) == 1:
            values.update(range(-32, 33))
        elif len(parameters) == 2:
            values.update(range(-8, 9))

        ordered = sorted(values, key=lambda value: (abs(value), value))

        per_parameter = max(
            2,
            int(MAX_CANDIDATE_INPUTS ** (1.0 / len(parameters))),
        )
        ordered = sorted(ordered[:per_parameter])

        combinations = []

        for combination in itertools.product(
            ordered,
            repeat=len(parameters),
        ):
            combinations.append(dict(zip(parameters, combination)))

            if len(combinations) >= MAX_CANDIDATE_INPUTS:
                break

        return combinations

    def boundary_distance(self, check):
        if check.left is None or check.right is None:
            return 0

        try:
            return abs(check.left - check.right)
        except TypeError:
            return 0

    def select_cases(self, found):
        found.sort(key=lambda item: (item[0], item[1]))

        selected = []
        seen = set()

        for _, _, case in found:
            key = tuple(sorted(case["variables"].items()))

            if key in seen:
                continue

            seen.add(key)
            selected.append(case)

            if len(selected) >= MAX_BOUNDARY_CASES:
                break

        return selected

    def branch_label(self, statement, truth):
        if isinstance(statement, WhileStatement):
            return "enter loop" if truth else "exit loop"

        if truth:
            return "then"

        return "else" if statement.else_branch is not None else "skip"

    def build_concrete_case(
        self,
        target,
        arguments,
        before,
        after,
        before_check,
        after_check,
    ):
        variables = dict(before_check.values)
        variables.update(after_check.values)

        before_side = self.case_side(
            target["old_condition"],
            before_check,
            before,
        )
        after_side = self.case_side(
            target["new_condition"],
            after_check,
            after,
        )

        variable_text = ", ".join(
            f"{name} = {value}" for name, value in variables.items()
        ) or "the program's own values"

        description = (
            f"When {variable_text}: BEFORE evaluates "
            f"{before_side['evaluated']} = "
            f"{str(before_side['result']).lower()} → "
            f"{before_side['branch']}"
            f"{self.return_suffix(before_side)}; AFTER evaluates "
            f"{after_side['evaluated']} = "
            f"{str(after_side['result']).lower()} → "
            f"{after_side['branch']}"
            f"{self.return_suffix(after_side)}."
        )

        return {
            "kind": "concrete",
            "inputs": dict(arguments),
            "variables": variables,
            "condition_path": ".".join(target["new_parts"]),
            "before": before_side,
            "after": after_side,
            "behavior_changed": (
                before_side["result"] != after_side["result"]
                or before_side.get("return_value")
                != after_side.get("return_value")
            ),
            "description": description,
        }

    def case_side(self, condition, check, execution):
        values = dict(check.values)

        side = {
            "condition": expression_to_source(condition),
            "evaluated": expression_to_source(condition, values),
            "result": check.result,
            "branch": check.branch,
            "return_value": execution.return_value,
        }

        if execution.error:
            side["error"] = execution.error

        return side

    def return_suffix(self, side):
        if side.get("error"):
            return f" (execution stopped: {side['error']})"

        if side.get("return_value") is None:
            return ""

        return f" → returns {side['return_value']}"

    def hypothetical_cases(self, target, new_evaluator, parameters):
        """
        When no concrete input reaches a different branch, evaluate the
        BEFORE and AFTER conditions directly on boundary values of the
        variables they read.
        """
        old_condition = target["old_condition"]
        new_condition = target["new_condition"]

        names = []

        for name in self.extract_identifiers(
            old_condition
        ) + self.extract_identifiers(new_condition):
            if name not in names:
                names.append(name)

        base = {}

        reference = new_evaluator.run(
            {name: 0 for name in parameters},
            watch={"target": new_condition},
        )
        check = reference.first_evaluation("target")

        if check is not None:
            base.update(check.values)

        for name in names:
            base.setdefault(name, 0)

        literals = set()

        for value in collect_numeric_literals(
            old_condition
        ) + collect_numeric_literals(new_condition):
            if not isinstance(value, bool):
                literals.add(value)

        found = []
        order = 0

        for name in names:
            candidates = {base[name]}

            for literal in literals:
                candidates.update({literal - 1, literal, literal + 1})

            for value in sorted(candidates):
                env = dict(base)
                env[name] = value
                order += 1

                try:
                    before_result = bool(
                        evaluate_expression(old_condition, env)
                    )
                    after_result = bool(
                        evaluate_expression(new_condition, env)
                    )
                except EvaluationError:
                    continue

                if before_result == after_result:
                    continue

                distance = 0

                if (
                    isinstance(new_condition, BinaryOperation)
                    and new_condition.operator in COMPARISON_OPERATORS
                ):
                    try:
                        distance = abs(
                            evaluate_expression(new_condition.left, env)
                            - evaluate_expression(new_condition.right, env)
                        )
                    except (EvaluationError, TypeError):
                        distance = 0

                relevant = {
                    key: env[key] for key in names if key in env
                }

                before_side = {
                    "condition": expression_to_source(old_condition),
                    "evaluated": expression_to_source(
                        old_condition,
                        relevant,
                    ),
                    "result": before_result,
                    "branch": self.branch_label(
                        target["old_statement"],
                        before_result,
                    ),
                    "return_value": None,
                }
                after_side = {
                    "condition": expression_to_source(new_condition),
                    "evaluated": expression_to_source(
                        new_condition,
                        relevant,
                    ),
                    "result": after_result,
                    "branch": self.branch_label(
                        target["new_statement"],
                        after_result,
                    ),
                    "return_value": None,
                }

                variable_text = ", ".join(
                    f"{key} = {val}" for key, val in relevant.items()
                )

                found.append(
                    (
                        distance,
                        order,
                        {
                            "kind": "hypothetical",
                            "inputs": {},
                            "variables": relevant,
                            "condition_path": ".".join(
                                target["new_parts"]
                            ),
                            "before": before_side,
                            "after": after_side,
                            "behavior_changed": True,
                            "description": (
                                f"If {variable_text} at this point "
                                f"(not reached with the program's "
                                f"current values): BEFORE "
                                f"{before_side['evaluated']} = "
                                f"{str(before_result).lower()} → "
                                f"{before_side['branch']}; AFTER "
                                f"{after_side['evaluated']} = "
                                f"{str(after_result).lower()} → "
                                f"{after_side['branch']}."
                            ),
                        },
                    )
                )

        return self.select_cases(found)

    def compare_execution(self, old_ast, new_ast):
        """Run both versions when the entry function has no inputs."""
        old_evaluator = ProgramEvaluator(old_ast)
        new_evaluator = ProgramEvaluator(new_ast)

        if old_evaluator.parameter_names() or new_evaluator.parameter_names():
            return None

        before = old_evaluator.run({})
        after = new_evaluator.run({})

        return {
            "function": after.function or before.function,
            "before": {
                "return_value": before.return_value,
                "error": before.error,
            },
            "after": {
                "return_value": after.return_value,
                "error": after.error,
            },
            "changed": (
                before.return_value != after.return_value
                or before.error != after.error
            ),
        }

    # ==================================================
    # Report
    # ==================================================

    def build_report(self, old_ast, new_ast, changes, impacts):
        grouped = {
            group: [
                self.impact_to_dict(impact)
                for impact in impacts
                if impact.impact_type in types
            ]
            for group, types in IMPACT_GROUPS.items()
        }

        change_items = [
            self.describe_change(old_ast, new_ast, change)
            for change in changes
        ]

        summary = self.build_summary(
            change_items,
            impacts,
            grouped,
        )

        explanation = self.build_explanation(
            change_items,
            grouped,
        )

        return {
            "changes": change_items,
            "impacts": [
                self.impact_to_dict(impact)
                for impact in impacts
            ],
            "affected": grouped,
            "boundary_cases": self.boundary_cases,
            "execution": self.execution,
            "summary": summary,
            "explanation": explanation,
        }

    def impact_to_dict(self, impact):
        return {
            "impact_type": impact.impact_type,
            "description": impact.description,
            "path": impact.path,
        }

    def describe_change(self, old_ast, new_ast, change):
        new_parts = self.get_path_parts(
            getattr(change, "new_path", None) or change.path
        )
        old_parts = self.get_path_parts(
            getattr(change, "old_path", None) or change.path
        )

        before_text = None
        after_text = None

        if change.change_type in ("modified", "removed"):
            before_text = self.context_text(old_ast, old_parts)

        if change.change_type in ("modified", "added"):
            after_text = self.context_text(new_ast, new_parts)

        location_ast = old_ast if change.change_type == "removed" else new_ast
        location_parts = (
            old_parts if change.change_type == "removed" else new_parts
        )

        return {
            "type": change.change_type,
            "description": change.description,
            "path": change.path,
            "location": self.describe_location(
                location_ast,
                location_parts,
            ),
            "before": before_text,
            "after": after_text,
            "old_value": self.json_value(
                getattr(change, "old_value", None)
            ),
            "new_value": self.json_value(
                getattr(change, "new_value", None)
            ),
        }

    def json_value(self, value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        return str(value)

    def context_text(self, ast, parts):
        """Source text of the condition or statement around a path."""
        condition_index = self.find_condition_index(parts)

        if condition_index is not None:
            statement = self.find_node(ast, parts[:condition_index])

            if isinstance(statement, CONTROL_TYPES):
                return expression_to_source(statement.condition)

        node = self.find_node(ast, parts)

        if isinstance(node, (Function, Program)):
            return None

        statement, _ = self.find_enclosing_statement(ast, parts)

        if statement is not None:
            return self.statement_to_source(statement)

        if node is not None and not isinstance(node, (str, int, float)):
            return self.statement_to_source(node)

        return None

    def statement_to_source(self, node):
        if node is None:
            return "(nothing)"

        if isinstance(node, VariableDeclaration):
            if node.initializer is not None:
                return (
                    f"{node.type} {node.name} = "
                    f"{expression_to_source(node.initializer)};"
                )

            return f"{node.type} {node.name};"

        if isinstance(node, Assignment):
            return f"{node.name} = {expression_to_source(node.value)};"

        if isinstance(node, ReturnStatement):
            if node.value is None:
                return "return;"

            return f"return {expression_to_source(node.value)};"

        if isinstance(node, IfStatement):
            text = f"if ({expression_to_source(node.condition)}) {{ … }}"

            if node.else_branch is not None:
                text += " else { … }"

            return text

        if isinstance(node, WhileStatement):
            return (
                f"while ({expression_to_source(node.condition)}) "
                f"{{ … }}"
            )

        if isinstance(node, Block):
            return f"{{ {len(node.statements)} statement(s) }}"

        if isinstance(node, Function):
            return f"{node.return_type} {node.name}(…)"

        return f"{expression_to_source(node)};"

    def describe_location(self, ast, parts):
        segments = []
        node = ast

        for part in parts:
            node = self.find_node(node, [part])

            field_name = part.split("[")[0]

            if isinstance(node, Function):
                segments.append(f"{node.name}()")

            elif field_name == "statements" and node is not None:
                index = int(part[part.index("[") + 1:-1]) + 1
                segments.append(
                    f"statement {index} ({self.statement_kind(node)})"
                )

            elif field_name == "then_branch":
                segments.append("then branch")

            elif field_name == "else_branch":
                segments.append("else branch")

            elif field_name == "condition":
                segments.append("condition")

            elif field_name == "initializer":
                segments.append("initial value")

            elif field_name == "parameters":
                segments.append("parameters")

            if node is None:
                break

        return " › ".join(segments) if segments else "program"

    def statement_kind(self, node):
        if isinstance(node, VariableDeclaration):
            return f"declaration of {node.name}"

        if isinstance(node, Assignment):
            return f"assignment to {node.name}"

        if isinstance(node, IfStatement):
            return "if"

        if isinstance(node, WhileStatement):
            return "while"

        if isinstance(node, ReturnStatement):
            return "return"

        if isinstance(node, Block):
            return "block"

        return "expression"

    def build_summary(self, change_items, impacts, grouped):
        counts = {}

        for impact in impacts:
            counts[impact.impact_type] = (
                counts.get(impact.impact_type, 0) + 1
            )

        affected_variables = []

        for impact in impacts:
            if impact.impact_type in ("variable", "data_dependency"):
                name = self.extract_variable_name(impact.description)

                if name and name not in affected_variables:
                    affected_variables.append(name)

        affected_blocks = []

        for impact in grouped["basic_blocks"]:
            if impact["description"].startswith("In the BEFORE"):
                continue

            if impact["path"] not in affected_blocks:
                affected_blocks.append(impact["path"])

        execution_changed = bool(
            self.execution and self.execution.get("changed")
        )

        if not change_items:
            risk = "none"
        elif (
            grouped["control_flow"]
            or self.boundary_cases
            or execution_changed
        ):
            risk = "high"
        elif grouped["data_dependencies"] or grouped["returns"]:
            risk = "medium"
        else:
            risk = "low"

        if not change_items:
            headline = (
                "No structural changes detected: both programs "
                "produce the same AST."
            )
        else:
            first = change_items[0]

            if first["before"] and first["after"]:
                headline = (
                    f"{first['before']}  →  {first['after']}"
                )
            else:
                headline = first["description"]

            if len(change_items) > 1:
                headline += f" (+{len(change_items) - 1} more change(s))"

        return {
            "changed": bool(change_items),
            "headline": headline,
            "risk_level": risk,
            "total_changes": len(change_items),
            "total_impacts": len(impacts),
            "counts": counts,
            "affected_variables": affected_variables,
            "affected_blocks": affected_blocks,
            "affected_conditions": len(grouped["conditions"]),
            "affected_paths": len(grouped["paths"]),
            "affected_returns": len(grouped["returns"]),
            "boundary_cases": len(self.boundary_cases),
            "execution_changed": execution_changed,
        }

    def build_explanation(self, change_items, grouped):
        if not change_items:
            return [
                "The BEFORE and AFTER programs have identical abstract "
                "syntax trees, so no part of the program is affected. "
                "Formatting and comment changes are ignored."
            ]

        sentences = []

        for change in change_items:
            if change["before"] and change["after"]:
                sentences.append(
                    f"At {change['location']}, "
                    f"`{change['before']}` became `{change['after']}` "
                    f"({change['description'].rstrip('.')})."
                )
            elif change["after"]:
                sentences.append(
                    f"At {change['location']}, new code was added: "
                    f"`{change['after']}`."
                )
            elif change["before"]:
                sentences.append(
                    f"At {change['location']}, code was removed: "
                    f"`{change['before']}`."
                )
            else:
                sentences.append(
                    f"At {change['location']}: {change['description']}"
                )

        condition_variables = [
            self.extract_variable_name(item["description"])
            for item in grouped["variables"]
            if "used by the changed condition" in item["description"]
        ]

        if condition_variables:
            names = ", ".join(
                f"'{name}'" for name in dict.fromkeys(condition_variables)
            )
            sentences.append(
                f"The changed condition reads {names}, so the value of "
                f"{names} now decides the branch differently."
            )

        defined = [
            item["description"]
            for item in grouped["variables"]
            if "is defined differently" in item["description"]
        ]

        for description in defined:
            sentences.append(description.rstrip(".") + ".")

        derived = [
            item["description"]
            for item in grouped["data_dependencies"]
            if "depends on changed" in item["description"]
        ]

        for description in derived:
            sentences.append(description)

        branch_impacts = [
            item
            for item in grouped["basic_blocks"]
            if "affects branching" in item["description"]
        ]

        for item in branch_impacts:
            sentences.append(
                item["description"].replace(
                    "Changed condition affects branching",
                    "The conditional jump that ends this block decides "
                    "between its successors: branching",
                )
                + " Both successor blocks are therefore affected."
            )

        returns = [
            item
            for item in grouped["returns"]
            if "Affected path reaches" in item["description"]
        ]

        if returns:
            route_text = "; ".join(
                f"{item['path']} ({item['description'].split('which ')[-1].rstrip('.')})"
                for item in returns
            )
            sentences.append(
                f"{len(returns)} affected execution path(s) end in a "
                f"return statement: {route_text}."
            )

        for case in self.boundary_cases:
            sentences.append(f"Boundary case — {case['description']}")

        if self.execution:
            before = self.execution["before"]
            after = self.execution["after"]

            def outcome(side):
                if side.get("error"):
                    return f"stops with an error ({side['error']})"

                return f"returns {side.get('return_value')}"

            if self.execution["changed"]:
                sentences.append(
                    f"Running both versions of "
                    f"{self.execution['function']}(): BEFORE "
                    f"{outcome(before)}, AFTER {outcome(after)}. The "
                    f"change alters the program's observable result."
                )
            else:
                sentences.append(
                    f"Running both versions of "
                    f"{self.execution['function']}(): both "
                    f"{outcome(after)}. With the program's current "
                    f"values the result is unchanged, but the affected "
                    f"paths above can behave differently for other "
                    f"values."
                )

        return sentences

    # ==================================================
    # AST / CFG mapping helpers
    # ==================================================

    def add_control_point(self, side, parts=None, block_id=None):
        point = {"side": side}

        if block_id is not None:
            point["block_id"] = block_id

        if parts is not None:
            point["parts"] = list(parts)
            point["path"] = ".".join(parts)

        if point not in self.control_points:
            self.control_points.append(point)

    def add_condition_change(self, old_parts, new_parts):
        if old_parts is None or new_parts is None:
            return

        pair = (list(old_parts), list(new_parts))

        if pair not in self.condition_changes:
            self.condition_changes.append(pair)

    def find_condition_index(self, parts):
        for index in range(len(parts) - 1, -1, -1):
            if parts[index] == "condition":
                return index

        return None

    def find_enclosing_statement(self, ast, parts):
        for length in range(len(parts), -1, -1):
            node = self.find_node(ast, parts[:length])

            if isinstance(node, STATEMENT_TYPES):
                return node, parts[:length]

            # Expression statements live directly in a statements list.
            if (
                length > 0
                and parts[length - 1].startswith("statements[")
                and node is not None
                and not isinstance(node, Block)
            ):
                return node, parts[:length]

        return None, []

    def iter_statements(self, node, parts):
        """Yield (statement, path parts) for a subtree in source order."""
        if node is None:
            return

        if isinstance(node, Block):
            for index, statement in enumerate(node.statements):
                yield from self.iter_statements(
                    statement,
                    parts + [f"statements[{index}]"],
                )
            return

        if isinstance(node, Function):
            yield from self.iter_statements(node.body, parts + ["body"])
            return

        yield node, parts

        if isinstance(node, IfStatement):
            yield from self.iter_statements(
                node.then_branch,
                parts + ["then_branch"],
            )
            yield from self.iter_statements(
                node.else_branch,
                parts + ["else_branch"],
            )

        elif isinstance(node, WhileStatement):
            yield from self.iter_statements(node.body, parts + ["body"])

    def collect_conditional_paths(self, node, parts, paths):
        """Collect if/while statement paths in TAC generation order."""
        if node is None:
            return

        if isinstance(node, Program):
            for index, declaration in enumerate(node.declarations):
                self.collect_conditional_paths(
                    declaration,
                    parts + [f"declarations[{index}]"],
                    paths,
                )

        elif isinstance(node, Function):
            self.collect_conditional_paths(
                node.body,
                parts + ["body"],
                paths,
            )

        elif isinstance(node, Block):
            for index, statement in enumerate(node.statements):
                self.collect_conditional_paths(
                    statement,
                    parts + [f"statements[{index}]"],
                    paths,
                )

        elif isinstance(node, IfStatement):
            paths.append(parts)
            self.collect_conditional_paths(
                node.then_branch,
                parts + ["then_branch"],
                paths,
            )
            self.collect_conditional_paths(
                node.else_branch,
                parts + ["else_branch"],
                paths,
            )

        elif isinstance(node, WhileStatement):
            paths.append(parts)
            self.collect_conditional_paths(
                node.body,
                parts + ["body"],
                paths,
            )

    def collect_return_statements(self, node, returns):
        """Collect return statements in TAC generation order."""
        if node is None:
            return

        if isinstance(node, Program):
            for declaration in node.declarations:
                self.collect_return_statements(declaration, returns)

        elif isinstance(node, Function):
            self.collect_return_statements(node.body, returns)

        elif isinstance(node, Block):
            for statement in node.statements:
                self.collect_return_statements(statement, returns)

        elif isinstance(node, IfStatement):
            self.collect_return_statements(node.then_branch, returns)
            self.collect_return_statements(node.else_branch, returns)

        elif isinstance(node, WhileStatement):
            self.collect_return_statements(node.body, returns)

        elif isinstance(node, ReturnStatement):
            returns.append(node)

    def conditional_block_map(self, ast, cfg):
        """
        Map each if/while statement path to the basic block holding its
        conditional jump. The TAC generator emits exactly one `if`
        instruction per conditional, in AST pre-order, so the k-th
        conditional corresponds to the k-th `if` instruction.
        """
        if ast is None or cfg is None:
            return {}

        paths = []
        self.collect_conditional_paths(ast, [], paths)

        jump_blocks = []

        for block_id in sorted(cfg.nodes):
            for instruction in cfg.nodes[block_id].block.instructions:
                if instruction.operator == "if":
                    jump_blocks.append(block_id)

        if len(paths) != len(jump_blocks):
            return {}

        mapping = {
            tuple(path): block_id
            for path, block_id in zip(paths, jump_blocks)
        }

        if not hasattr(self, "_conditional_map_cache"):
            self._conditional_map_cache = {}

        self._conditional_map_cache[id(ast)] = mapping

        return mapping

    def build_return_text_map(self, ast, cfg):
        """Map (block id, instruction index) of each TAC return to the
        source expression it returns."""
        if ast is None or cfg is None:
            return {}

        returns = []
        self.collect_return_statements(ast, returns)

        locations = []

        for block_id in sorted(cfg.nodes):
            for index, instruction in enumerate(
                cfg.nodes[block_id].block.instructions
            ):
                if instruction.operator == "return":
                    locations.append((block_id, index))

        if len(returns) != len(locations):
            return {}

        return {
            location: expression_to_source(statement.value)
            for location, statement in zip(locations, returns)
        }

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
        path,
    ):
        if not path:
            return []

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
            result
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
            for field_name in root.__dataclass_fields__:
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