"""
bento_mdf.mdf.convert
=====================

Utilities for converting MDF YAML to bento-meta objects
"""

from __future__ import annotations

import re
import json
from typing import TYPE_CHECKING
from urllib.parse import unquote

from bento_meta.objects import Edge, Node, Property, Tag, Term, ValueSet
from pdb import set_trace

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
    "Code": "origin_id",
    "CompKey": None,
    "Definition": "origin_definition",
    "Deprecated": "is_deprecated",
    "Desc": "desc",
    "Dst": "dst",
    "Enum": "Enum",
    "Handle": "handle",
    "Key": "is_key",
    "Mul": "multiplicity",
    "NanoID": "nanoid",
    "Nodes": None,
    "Nul": "is_nullable",
    "Origin": "origin_name",
    "PropDefinitions": None,
    "Relationships": None,
    "Req": "is_required",
    "Src": "src",
    "Strict": "is_strict",
    "Term": None,
    "Terms": None,
    # don't translate type spec in init - process in process_prop
    "Type": "Type",
    "UniversalNodeProperties": None,
    "UniversalRelationshipProperites": None,
    "Value": "value",
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
    info = process[ent_cls](init, spec, ent)
    if spec.get("Tags"):
        for t in spec["Tags"]:
            ent.tags[t] = spec_to_entity(
                "",
                {},
                {"key": t, "value": spec["Tags"][t], "_commit": init.get("_commit")},
                Tag,
            )
    return ent


def process_node(init: dict, spec: dict, node: Node) -> None:
    """Additional processing for Node entities."""
    if spec.get('CompKey'):
        node.composite_key_props = spec['CompKey']
    pass

def process_reln(init: dict, spec: dict, edge: Edge) -> None:
    """Additional processing for Relationship entities."""
    pass

def process_term(init: dict, spec: dict, term: Term) -> None:
    """Additional processing for Term entities."""
    if not term.handle:
        term.handle = to_snake_case(term.value)
    if spec.get("definition"):
        term.definition = unquote(term, spec["definition"])


def process_tag(init: dict, spec: dict, tag: Tag):
    """Additional processing for tag entities."""
    pass

def process_prop(init: dict, spec: dict, prop: Property) -> None:
    """Additional processing for Property entities."""
    ty_spec = init.get("Enum") or init.get("Type")
    domain_spec = typespec_to_domain_spec(ty_spec)
    if (
        domain_spec["value_domain"] != "value_set"
        and domain_spec.get("item_domain") != "value_set"
    ):
        for attr in domain_spec:
            prop.__setattr__(attr, domain_spec[attr])
    else:  # is "value_set" or "list" with item_domain "value_set"
        if domain_spec["value_domain"] == "list":
            prop.value_domain = "list"
            prop.item_domain = "value_set"
        else:
            prop.value_domain = "value_set"
        if domain_spec.get("units"):
            prop.units = domain_spec["units"]
        if domain_spec.get("pattern"):
            prop.pattern = domain_spec["pattern"]
        if domain_spec.get("url"):
            prop.value_set = ValueSet(
                {"url": domain_spec["url"], "_commit": prop._commit},
            )
        elif domain_spec.get("path"):
            prop.value_set = ValueSet(
                {"path": domain_spec["path"], "_commit": prop._commit},
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
    # set default values for unprovided attrs
    prop_attrs_with_defaults = {
        "is_strict": True,
        "is_key": False,
        "is_nullable": False,
        "is_required": False,
    }
    for attr, default in prop_attrs_with_defaults.items():
        if getattr(prop, attr) is None:
            setattr(prop, attr, default)


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
    if isinstance(spec, dict):
        # list type
        if spec.get("value_type") == "list":
            domain_spec = {"value_domain": "list"}
            list_spec = spec.get("item_type") or spec.get("Enum")
            item_domain_spec = typespec_to_domain_spec(list_spec)
            domain_spec["item_domain"] = item_domain_spec["value_domain"]
            for key in ("units", "value_set", "url", "path"):
                if key not in item_domain_spec:
                    continue
                domain_spec[key] = item_domain_spec[key]
            return domain_spec
        # regex type
        if spec.get("pattern"):
            # TODO: add regex flavor attribute to bento-meta Property entity?
            return {"value_domain": "regexp", "pattern": spec["pattern"]}
        # numberWithUnits type
        if spec.get("units"):
            domain_spec = {"value_domain": spec["value_type"]}
            if isinstance(spec["units"][0], dict) and spec["units"][0].get("pattern"):
                item_domain_spec = typespec_to_domain_spec(spec["units"][0])
                domain_spec["units"] = item_domain_spec["value_domain"]
                domain_spec["pattern"] = item_domain_spec["pattern"]
            else:
                domain_spec["units"] = ";".join(spec["units"])
            return domain_spec
    # enum type
    if isinstance(spec, list):
        # do not implement union type for now
        # assume a value_set, as a list of term handles or a single url/path
        # don't merge terms here, but in process_prop
        # list of term initializers returned
        #   term values == term handles
        if (
            len(spec) == 1
            and isinstance(spec[0], str)
        ):
            if re.match("^[a-z][a-z]*://",spec[0]):
                return {"value_domain": "value_set", "url": spec[0]}
            elif re.match("^/.*",spec[0]):
                return {"value_domain": "value_set", "path": spec[0]}
        vs = []
        for tm in spec:
            if isinstance(tm, bool):
                tm = "True" if tm else "False"  # stringify any booleans
            vs.append({"handle": tm, "value": tm})
        return {"value_domain": "value_set", "value_set": vs}
    # unknown - default domain
    return {"value_domain": Property.default("value_domain")}


def entity_to_spec(
        ent: Entity,
        spec: dict = None
) -> dict:
    if spec is None:
        spec = {}
    if ent.tags:
        tags = {}
        for t in ent.tags.values():
            entity_to_spec(t,tags)
        spec["Tags"] = tags
    if "concept" in ent.attspec and ent.concept and ent.concept.terms:
        spec["Term"] = [entity_to_spec(t) for t in ent.concept.terms.values()]
    if ent.desc:
        spec["Desc"] = ent.desc
    if isinstance(ent, Node):
        spec["Props"] = sorted([x.handle for x in ent.props.values()])
        if len(spec["Props"]) == 0:
            spec["Props"] = None
        pass
    elif isinstance(ent, Property):
        if ent.is_nullable is not None:
            spec["Nul"] = ent.is_nullable
        if ent.is_required is not None:
            spec["Req"] = ent.is_required
        if ent.is_strict is not None:
            spec["Strict"] = ent.is_strict
        if ent.is_key is not None:
            spec["Key"] = ent.is_key
        if ent.is_deprecated is not None:
            spec["Deprecated"] = ent.is_deprecated
        if ent.value_domain == 'value_set':
            spec["Enum"] = domain_spec_to_typespec(ent)
        else:
            spec["Type"] = domain_spec_to_typespec(ent)
        pass
    elif isinstance(ent, Edge):
        # note that edge mdf specs must be merged correctly in the caller
        if ent.is_required:
            spec["Req"] = True
        if ent.multiplicity:
            spec["Mul"] = ent.multiplicity
        spec["Src"] = ent.src.handle
        spec["Dst"] = ent.dst.handle
        spec["Props"] = sorted([x.handle for x in ent.props.values()])
        if len(spec["Props"]) == 0:
            spec["Props"] = None
        pass
    elif isinstance(ent, Term):
        spec["Value"] = ent.value
        spec["Origin"] = ent.origin_name
        if ent.origin_definition:
            spec["Definition"] = ent.origin_definition
        if ent.origin_version:
            spec["Version"] = ent.origin_version
        if ent.origin_id:
            spec["Code"] = ent.origin_id
        pass
    elif isinstance(ent, Tag):
        spec[ent.key] = ent.value
        pass
    else:
        raise RuntimeError(f'Cannot process Entity subtype: {ent}')
    return spec


def domain_spec_to_typespec(prop : Property) -> str | dict:
    ret = {}
    if prop.value_domain == 'value_set':
        if prop.value_set.url:
            ret = [prop.value_set.url]
        elif prop.value_set.path:
            ret = [prop.value_set.path]
        else:
            ret = [x for x in prop.terms]
    elif prop.value_domain == 'list':
        ret["value_type"] = 'list'
        if prop.item_domain == "value_set":
            if prop.value_set.url:
                ret["Enum"] = [prop.value_set.url]
            elif prop.value_set.path:
                ret["Enum"] = [prop.value_set.path]
            else:
                ret["Enum"] = [x for x in prop.terms]
        else:
            if prop.units:
                ret["item_type"] = {"value_type": prop.item_domain,
                                    "units": prop.units.split(";")}
            elif prop.pattern:
                ret["item_type"] = {"pattern": prop.pattern}
            else:
                ret["item_type"] = prop.item_domain
    elif prop.units:
        ret["value_type"] = prop.value_domain
        if prop.units == "regexp":
            ret["units"] = [{"pattern": prop.pattern}]
        else:
            ret["units"] = prop.units.split(";")
    elif prop.pattern:
        ret["pattern"] = prop.pattern
    else:
        ret = prop.value_domain
    return ret
