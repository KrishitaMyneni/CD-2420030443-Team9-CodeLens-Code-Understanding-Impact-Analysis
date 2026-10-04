from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Change:
    change_type: str
    description: str
    path: str
    # Optional extra detail (backward compatible: older callers only use
    # change_type / description / path).
    old_path: Optional[str] = None
    new_path: Optional[str] = None
    old_value: Optional[object] = None
    new_value: Optional[object] = None


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
        old_path: Optional[str] = None,
    ):
        # `path` is the location in the NEW program. `old_path` is the
        # location in the OLD program (they differ when statements were
        # inserted/removed before this node).
        if old_path is None:
            old_path = path

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
                    new_path=path,
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
                    path=old_path,
                    old_path=old_path,
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
                    old_path=old_path,
                    new_path=path,
                )
            )
            return

        if hasattr(old_node, "__dataclass_fields__"):
            self.compare_dataclass_fields(
                old_node,
                new_node,
                path,
                changes,
                old_path,
            )

    def compare_dataclass_fields(
        self,
        old_node,
        new_node,
        path: str,
        changes: List[Change],
        old_path: Optional[str] = None,
    ):
        if old_path is None:
            old_path = path

        for field_name in old_node.__dataclass_fields__:
            old_value = getattr(old_node, field_name)
            new_value = getattr(new_node, field_name)

            field_path = f"{path}.{field_name}"
            old_field_path = f"{old_path}.{field_name}"

            if self.is_ast_node(old_value) or self.is_ast_node(new_value):
                self.compare_nodes(
                    old_value,
                    new_value,
                    field_path,
                    changes,
                    old_field_path,
                )

            elif isinstance(old_value, list) or isinstance(new_value, list):
                self.compare_lists(
                    old_value or [],
                    new_value or [],
                    field_path,
                    changes,
                    old_field_path,
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
                        old_path=old_field_path,
                        new_path=field_path,
                        old_value=old_value,
                        new_value=new_value,
                    )
                )

    def compare_lists(
        self,
        old_list,
        new_list,
        path: str,
        changes: List[Change],
        old_path: Optional[str] = None,
    ):
        """
        Align the two lists with a longest-common-subsequence over
        structurally equal AST nodes, so that inserting or deleting one
        statement does not mark every following statement as modified.
        Unmatched items in each gap are paired by node type (modified);
        anything left over is reported as added / removed.
        """
        if old_path is None:
            old_path = path

        matches = self.longest_common_subsequence(
            old_list,
            new_list,
        )

        previous_old = -1
        previous_new = -1

        for old_index, new_index in matches + [
            (len(old_list), len(new_list))
        ]:
            old_gap = list(range(previous_old + 1, old_index))
            new_gap = list(range(previous_new + 1, new_index))

            self.compare_gap(
                old_list,
                new_list,
                old_gap,
                new_gap,
                path,
                old_path,
                changes,
            )

            previous_old = old_index
            previous_new = new_index

    def compare_gap(
        self,
        old_list,
        new_list,
        old_gap,
        new_gap,
        path,
        old_path,
        changes,
    ):
        pairs = []
        used_new = set()
        search_start = 0

        # Pair items of the same node type, preserving order.
        for old_index in old_gap:
            old_type = type(old_list[old_index]).__name__

            for position in range(search_start, len(new_gap)):
                new_index = new_gap[position]

                if (
                    new_index not in used_new
                    and type(new_list[new_index]).__name__ == old_type
                ):
                    pairs.append((old_index, new_index))
                    used_new.add(new_index)
                    search_start = position + 1
                    break

        paired_old = {old_index for old_index, _ in pairs}

        # When nothing could be paired by type but both gaps have exactly
        # one element, treat it as an in-place replacement.
        if not pairs and len(old_gap) == 1 and len(new_gap) == 1:
            pairs.append((old_gap[0], new_gap[0]))
            paired_old.add(old_gap[0])
            used_new.add(new_gap[0])

        for old_index, new_index in pairs:
            self.compare_nodes(
                old_list[old_index],
                new_list[new_index],
                f"{path}[{new_index}]",
                changes,
                f"{old_path}[{old_index}]",
            )

        for old_index in old_gap:
            if old_index in paired_old:
                continue

            changes.append(
                Change(
                    change_type="removed",
                    description=(
                        f"Removed {type(old_list[old_index]).__name__}."
                    ),
                    path=f"{old_path}[{old_index}]",
                    old_path=f"{old_path}[{old_index}]",
                )
            )

        for new_index in new_gap:
            if new_index in used_new:
                continue

            changes.append(
                Change(
                    change_type="added",
                    description=(
                        f"Added {type(new_list[new_index]).__name__}."
                    ),
                    path=f"{path}[{new_index}]",
                    new_path=f"{path}[{new_index}]",
                )
            )

    def longest_common_subsequence(self, old_list, new_list):
        rows = len(old_list)
        columns = len(new_list)

        lengths = [[0] * (columns + 1) for _ in range(rows + 1)]

        for i in range(rows - 1, -1, -1):
            for j in range(columns - 1, -1, -1):
                if old_list[i] == new_list[j]:
                    lengths[i][j] = lengths[i + 1][j + 1] + 1
                else:
                    lengths[i][j] = max(
                        lengths[i + 1][j],
                        lengths[i][j + 1],
                    )

        matches = []
        i = 0
        j = 0

        while i < rows and j < columns:
            if old_list[i] == new_list[j]:
                matches.append((i, j))
                i += 1
                j += 1
            elif lengths[i + 1][j] >= lengths[i][j + 1]:
                i += 1
            else:
                j += 1

        return matches

    def is_ast_node(self, value) -> bool:
        return hasattr(value, "__dataclass_fields__")