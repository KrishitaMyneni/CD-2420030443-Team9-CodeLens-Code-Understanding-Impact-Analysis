from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Change:
    change_type: str
    description: str
    path: str


class ChangeAnalyzer:
    def compare(self, old_ast, new_ast):
        changes = []

        self.compare_nodes(
            old_ast,
            new_ast,
            "program",
            changes,
        )

        return changes

    def compare_nodes(
        self,
        old_node,
        new_node,
        path: str,
        changes: List[Change],
    ):
        if old_node is None and new_node is None:
            return

        if old_node is None:
            changes.append(
                Change(
                    change_type="added",
                    description=(
                        f"Added {type(new_node).__name__}."
                    ),
                    path=path,
                )
            )
            return

        if new_node is None:
            changes.append(
                Change(
                    change_type="removed",
                    description=(
                        f"Removed {type(old_node).__name__}."
                    ),
                    path=path,
                )
            )
            return

        old_type = type(old_node).__name__
        new_type = type(new_node).__name__

        if old_type != new_type:
            changes.append(
                Change(
                    change_type="modified",
                    description=(
                        f"Changed {old_type} to {new_type}."
                    ),
                    path=path,
                )
            )
            return

        if hasattr(old_node, "__dataclass_fields__"):
            self.compare_dataclass_fields(
                old_node,
                new_node,
                path,
                changes,
            )

    def compare_dataclass_fields(
        self,
        old_node,
        new_node,
        path: str,
        changes: List[Change],
    ):
        for field_name in old_node.__dataclass_fields__:
            old_value = getattr(old_node, field_name)
            new_value = getattr(new_node, field_name)

            field_path = f"{path}.{field_name}"

            if self.is_ast_node(old_value) or self.is_ast_node(new_value):
                self.compare_nodes(
                    old_value,
                    new_value,
                    field_path,
                    changes,
                )

            elif isinstance(old_value, list) or isinstance(new_value, list):
                self.compare_lists(
                    old_value or [],
                    new_value or [],
                    field_path,
                    changes,
                )

            elif old_value != new_value:
                changes.append(
                    Change(
                        change_type="modified",
                        description=(
                            f"Changed {field_name} "
                            f"from '{old_value}' "
                            f"to '{new_value}'."
                        ),
                        path=field_path,
                    )
                )

    def compare_lists(
        self,
        old_list,
        new_list,
        path: str,
        changes: List[Change],
    ):
        common_length = min(
            len(old_list),
            len(new_list),
        )

        for index in range(common_length):
            self.compare_nodes(
                old_list[index],
                new_list[index],
                f"{path}[{index}]",
                changes,
            )

        for index in range(common_length, len(old_list)):
            changes.append(
                Change(
                    change_type="removed",
                    description=(
                        f"Removed {type(old_list[index]).__name__}."
                    ),
                    path=f"{path}[{index}]",
                )
            )

        for index in range(common_length, len(new_list)):
            changes.append(
                Change(
                    change_type="added",
                    description=(
                        f"Added {type(new_list[index]).__name__}."
                    ),
                    path=f"{path}[{index}]",
                )
            )

    def is_ast_node(self, value) -> bool:
        return hasattr(value, "__dataclass_fields__")