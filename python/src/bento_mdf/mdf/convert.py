"""
bento_mdf.mdf.convert
=====================

Utilities for converting MDF YAML to bento-meta objects
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import unquote

from bento_meta.objects import Edge, Node, Property, Tag, Term, ValueSet

if TYPE_CHECKING:
    from bento_meta.entity import Entity


def to_snake_case(string: str) -> str:
    """Convert string to snake case representation."""
    string = string.replace(" ", "_")
    string = re.sub(r"(?<=[a-z0-9])_?([A-Z])", r"_\1", string)
    return string.lower()


# keys are valid specified MDF keys
# values are valid attributes of a bento_meta.Entity
mdf_to_meta = {
    "Handle": "handle",
    "Nodes": None,
    "Relationships": None,
    "PropDefinitions": None,
    "UniversalNodeProperties": None,
    "UniversalRelationshipProperites": None,
    "Terms": None,
    "Term": None,
    "Desc": "desc",
    "NanoID": "nanoid",
    "Src": "src",
    "Dst": "dst",
    "Mul": "multiplicity",
    "Value": "value",
    # don't translate type spec in init - process in process_prop
    "Type": "Type",
    "Enum": "Enum",
    "Key": "is_key",
    "Nul": "is_nullable",
    "Req": "is_required",
    "Deprecated": "is_deprecated",
    "Strict": "is_strict",
    "Origin": "origin_name",
    "Definition": "origin_definition",
    "Code": "origin_id",
    "Version": "origin_version",
}

# scalar types - shall match mdf_schema["defs"]["simpleType"]["enum"]
simple_types = [
    "number",
    "integer",
    "string",
    "datetime",
    "url",
    "boolean",
    "TBD",
]

# "declare"
process = {}


# hdl: handle, spec: MDF specifier object (from YAML)
# init: additional (bento-meta) attributes,
# entCls: bento-meta entity class (bareword)


def spec_to_entity(
    hdl: str | None,
    spec: dict,
    init: dict,
    ent_cls: type[Node | Edge | Property | Term | Tag],
) -> Entity:
    """Translate part of MDF YAML to bento-meta entity."""
    for k in spec:
        if k in mdf_to_meta and mdf_to_meta[k] is not None:
            init[mdf_to_meta[k]] = spec[k]
    if hdl and "handle" not in init:
        init["handle"] = hdl
    # init now contains (translated) spec keys and its original keys
    ent = ent_cls(init)
    info = process[ent_cls](init, ent)
    if spec.get("Tags"):
        for t in spec["Tags"]:
            ent.tags[t] = spec_to_entity(
                "",
                {},
                {"key": t, "value": spec["Tags"][t], "_commit": init.get("_commit")},
                Tag,
            )
    return ent


def process_node(spec: dict, node: Node) -> None:
    """Additional processing for Node entities."""


def process_reln(spec: dict, edge: Edge) -> None:
    """Additional processing for Relationship entities."""


def process_term(spec: dict, term: Term) -> None:
    """Additional processing for Term entities."""
    if not term.handle:
        term.handle = to_snake_case(term.value)
    if spec.get("definition"):
        term.definition = unquote(term, spec["definition"])


def process_tag(spec: dict, tag: Tag):
    """Additional processing for tag entities."""


def process_prop(spec: dict, prop: Property) -> None:
    """Additional processing for Property entities."""
    ty_spec = spec.get("Enum") or spec.get("Type")
    # kludge to process deprecated {"Type": {"Enum": [...]}} construct:
    if isinstance(ty_spec, dict) and "Enum" in ty_spec:
        ty_spec = ty_spec["Enum"]
    domain_spec = typespec_to_domain_spec(ty_spec)
    if domain_spec["value_domain"] != "value_set":
        for attr in domain_spec:
            prop.__setattr__(attr, domain_spec[attr])
    else:  # is "value_set"
        prop.value_domain = "value_set"
        if domain_spec.get("url"):
            prop.value_set = ValueSet(
                {"url": domain_spec["url"], "_commit": prop._commit},
            )
        elif domain_spec.get("value_set"):
            # create 'dummy' ValueSet to hold Enum terms,
            # but merge them with any Terms section terms in mdf.py
            prop.value_set = ValueSet({"_commit": "dummy"})
            for tm_init in domain_spec["value_set"]:
                tm_init["origin_name"] = prop.model
                term = spec_to_entity(None, {"_commit": prop._commit}, tm_init, Term)
                prop.value_set.terms[term.handle] = term
        else:
            msg = f"Can't evaluate value_set spec {domain_spec}"
            raise RuntimeError(msg)


process = {
    Node: process_node,
    Edge: process_reln,
    Property: process_prop,
    Term: process_term,
    Tag: process_tag,
}


def typespec_to_domain_spec(spec: str | dict | list) -> dict:
    # simple type
    if isinstance(spec, str):
        return {"value_domain": spec}
    elif isinstance(spec, dict):
        # regex type
        if spec.get("pattern"):
            return {"value_domain": "regexp", "pattern": spec["pattern"]}
        # numberWithUnits type
        if spec.get("units"):
            return {
                "value_domain": spec["value_type"],
                "units": ";".join(spec["units"]),
            }
        # list type
        if spec.get("item_type"):
            return {
                "value_domain": "list",
                "item_domain": typespec_to_domain_spec(spec["item_type"]),
            }
    # enum type
    elif isinstance(spec, list):
        # do not implement union type for now
        # assume a value_set, as a list of term handles or a single url/path
        # don't merge terms here, but in process_prop
        # list of term initializers returned
        #   term values == term handles
        if (
            len(spec) == 1
            and isinstance(spec[0], str)
            and re.match(
                "^/|.*://",
                spec[0],
            )
        ):
            return {"value_domain": "value_set", "url": spec[0]}
        else:
            vs = []
            for tm in spec:
                if isinstance(tm, bool):
                    tm = "True" if tm else "False"  # stringify any booleans
                vs.append({"handle": tm, "value": tm})
            return {"value_domain": "value_set", "value_set": vs}
    # unknown - default domain
    else:
        return {"value_domain": Property.default("value_domain")}
