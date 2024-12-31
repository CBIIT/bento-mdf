from typing import overload

from bento_meta.objects import Edge, Node, Property, Tag, Term

@overload
def spec_to_entity(
    hdl: str | None,
    spec: dict,
    init: dict,
    ent_cls: type[Node],
) -> Node: ...
@overload
def spec_to_entity(
    hdl: str | None,
    spec: dict,
    init: dict,
    ent_cls: type[Edge],
) -> Edge: ...
@overload
def spec_to_entity(
    hdl: str | None,
    spec: dict,
    init: dict,
    ent_cls: type[Property],
) -> Property: ...
@overload
def spec_to_entity(
    hdl: str | None,
    spec: dict,
    init: dict,
    ent_cls: type[Term],
) -> Term: ...
@overload
def spec_to_entity(
    hdl: str | None,
    spec: dict,
    init: dict,
    ent_cls: type[Tag],
) -> Tag: ...
