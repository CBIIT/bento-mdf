"""
DiffSummary class summarizes differences between two MDFs in plain text.

Typical usage example:
    summary = DiffSummary(diff).create_summary()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bento_meta.objects import Term

if TYPE_CHECKING:
    from bento_mdf.diff import Diff


class DiffSummary:
    """
    This class provides methods to summarize the differences between two MDFs.

    The create_summary method generates the summary string.
    """

    def __init__(self, diff: Diff) -> None:
        """Initialize the DiffSummary object from a Diff."""
        self.diff = diff

    def create_overall_summary(self) -> str:
        """Create a broad overall summary of the differences between two MDFs."""
        summary_added_removed = []
        summary_changed = []
        for ent_type, diffs in self.diff.result.items():
            ents_with_attr_changes = 0
            attr_changes = 0
            for action, diff in diffs.items():
                if action in ["added", "removed"]:
                    count = self.count_items(ent_type, action)
                    if count > 0:
                        summary_added_removed.append(
                            f"{count} {ent_type[:-1]}(s) {action}",
                        )
                else:  # action == "changed"
                    ents_with_attr_changes += len(diffs[action])
                    attr_changes += sum(len(d) for d in diff.values())
            if ents_with_attr_changes != 0 and attr_changes != 0:
                summary_changed.append(
                    f"{attr_changes} attribute(s) changed for "
                    f"{ents_with_attr_changes} {ent_type[:-1]}(s)",
                )

        return "; ".join(summary_added_removed + summary_changed)

    def create_detailed_summary(self) -> str:
        """Create a detailed summary of the differences between two MDFs."""
        detailed_summary = []
        for ent_type, diffs in self.diff.result.items():
            for action in diffs:
                items = self.get_items(ent_type, action)
                if not items:
                    continue
                if action in ["added", "removed"]:
                    for item in items:
                        detail = self.format_add_rem_detail(ent_type, action, item)
                        detailed_summary.append(detail)
                else:  # action == "changed"
                    for item in items:
                        if ent_type != "terms":
                            continue
                        detail = self.format_changed_detail(ent_type, item)
                        detailed_summary.append(detail)
        return "\n".join(detailed_summary)

    def count_items(self, ent_type: str, action: str) -> int:
        """Count the number of items in the diff dictionary."""
        items = self.get_items(ent_type, action)
        if not items:
            return 0
        return len(items)

    def get_items(self, ent_type: str, action: str) -> list | None:
        """Get the items from the diff dictionary."""
        items = self.diff.result.get(ent_type, {}).get(action, {})
        if isinstance(items, dict):
            return list(items.items())
        return items

    def get_detail_by_ent_type(
        self,
        ent_type: str,
        entk: str | tuple[str, str] | tuple[str, str, str],
    ) -> str:
        """Return formatted string for detailed summary based on entity type and key."""
        props_key_len = 2
        edge_key_len = 3
        ent_type_details = {
            "nodes": f"'{entk}'",
            "edges": f"'{entk[0]}' with src: '{entk[1]}' and dst: '{entk[2]}'"
            if len(entk) == edge_key_len
            else "Invalid key format for edges",
            "props": f"'{entk[1]}' with parent: '{entk[0]}'"
            if len(entk) == props_key_len
            else "Invalid key format for 'props'",
            "terms": f"'{entk[0]}' with origin: '{entk[1]}'",
        }
        return ent_type_details[ent_type]

    def format_entity_annotation(self, action: str, item: tuple) -> str:
        """Check if term annotates an entity and format accordingly."""
        change_detail = ""
        if action in ["added", "removed"] and not isinstance(item[1], Term):
            if not item[1].concept or not item[1].concept.terms:
                return ""
            term_annos = item[1].concept.terms
            term_anno_str = ", ".join(
                [
                    f"'{term_annos[_].value}' with origin '{term_annos[_].origin_name}'"
                    for _ in term_annos
                ],
            )
            return f". {item[1].get_label().capitalize()} annotated by: {term_anno_str}"
        if action == "changed":
            action = "added"
            for attr, changes in item[1].items():
                change_detail += (
                    f". Attribute: '{attr}' updated from "
                    f"'{changes['removed']}' to '{changes['added']}'"
                )
        for anno_ent_type, anno_changes in self.diff.annotations.items():
            for entk, anno_change in anno_changes.items():
                anno_item = anno_change.get(action, {})
                if not anno_item:
                    continue
                for termk in anno_item:
                    if termk != item[0]:
                        continue
                    return (
                        f" which annotates {anno_ent_type[:-1]}: "
                        f"{self.get_detail_by_ent_type(anno_ent_type, entk)}"
                        f"{change_detail}"
                    )
        return ""

    def format_add_rem_detail(
        self,
        ent_type: str,
        action: str,
        item: tuple,
    ) -> str:
        """Format detailed summary for added/removed entities depending on type."""
        detail = f"- {action.capitalize()} {ent_type[:-1]}: "
        if ent_type == "nodes":
            detail += f"'{item[0]}'"
        elif ent_type == "edges":
            detail += f"'{item[0][0]}' with src: '{item[0][1]}' and dst: '{item[0][2]}'"
        elif ent_type == "props":
            detail += f"'{item[0][1]}' with parent: '{item[0][0]}'"
        elif ent_type == "terms":
            detail += f"'{item[0][0]}' with origin: '{item[0][1]}'"
        detail += self.format_entity_annotation(action, item)
        return detail

    def format_changed_detail(self, ent_type: str, item: tuple) -> str:
        """Format detailed summary for changed entities depending on type."""
        if ent_type != "terms":
            return ""
        detail = f"- Changed {ent_type[:-1]}: "
        detail += f"'{item[0][0]}' with origin: '{item[0][1]}'"
        detail += self.format_entity_annotation("changed", item)
        return detail

    def create_summary(self) -> str | None:
        """Generate a string summarizing the differences between two MDFs."""
        if not self.diff.result:
            return None

        overall_summary = self.create_overall_summary()
        detailed_summary = self.create_detailed_summary()

        return f"{overall_summary}\n{detailed_summary}"
