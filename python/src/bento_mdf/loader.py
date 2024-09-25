"""YAML loader for MDF files with methods to check for duplicate keys and elements."""

from typing import Any

from yaml.constructor import ConstructorError
from yaml.loader import SafeLoader
from yaml.nodes import MappingNode, SequenceNode


class MDFLoader(SafeLoader):
    """
    Safe YAML loader for MDF files.

    Adds methods to check for duplicate keys and elements.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the MDFLoader."""
        super().__init__(*args, **kwargs)

    def construct_mapping(
        self,
        node: MappingNode,
        *,
        deep: bool = False,
    ) -> dict:
        """Construct a mapping node with duplicate keys check."""
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None,
                None,
                "expected a mapping node, but found %s" % node.id,
                node.start_mark,
            )
        mapping = {}

        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found unacceptable key (%s)" % exc,
                    key_node.start_mark,
                ) from exc
            value = self.construct_object(value_node, deep=deep)
            if key in mapping:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found duplicated key (%s)" % key,
                    key_node.start_mark,
                )
            mapping[key] = value
        return mapping

    def construct_sequence(
        self,
        node: SequenceNode,
        *,
        deep: bool = False,
    ) -> list:
        """Construct a list of sequence nodes with duplicate elements check."""
        if not isinstance(node, SequenceNode):
            raise ConstructorError(
                None,
                None,
                "expected a sequence node, but found %s" % node.id,
                node.start_mark,
            )
        elts = set()
        for c in node.value:
            if isinstance(c.value, str):  # just check lists of strings
                if c.value in elts:
                    raise ConstructorError(
                        "while constructing a sequence",
                        node.start_mark,
                        "found duplicated element (%s)" % c.value,
                    )
                elts.add(c.value)
        return [self.construct_object(child, deep=deep) for child in node.value]
