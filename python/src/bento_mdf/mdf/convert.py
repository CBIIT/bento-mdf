"""
bento_mdf.mdf.convert
=====================

Utilities for converting MDF YAML to bento-meta objects
"""
import re
from pdb import set_trace
from bento_meta.objects import Node, Edge, Property, Term, Tag, ValueSet


def to_snake_case(string: str) -> str:
    """converts given string to snake case representation"""
    string = string.replace(" ", "_")
    string = re.sub(r"(?<=[a-z0-9])_?([A-Z])", r"_\1", string)
    return string.lower()


# keys are valid specified MDF keys
# values are valid attributes of a bento_meta.Entity
mdf_to_meta = {
    "Handle": "handle",
    "Nodes": None,
    "Relationships": Node,
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
    "Type": None,
    "Enum": None,
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
# model: bento-meta model object
def spec_to_entity(hdl, spec, init, entCls, model=None):
    for k in spec:
        if k in mdf_to_meta and mdf_to_meta[k] != None:
            init[mdf_to_meta[k]] = spec[k]
    if hdl and "handle" not in init:
        init["handle"] = hdl
    ent = entCls(init)
    process[entCls](init, ent)
    if "Tags" in spec and spec["Tags"]:
        for t in spec["Tags"]:
            ent.tags[t] = spec_to_entity(
                "", {}, {"key":t, "value": spec["Tags"][t],
                         "_commit": init.get("_commit")},
                Tag)
    return ent


def process_node(spec, node, model=None):
    # noop
    return node


def process_reln(spec, edge, model=None):
    #noop
    return edge


def process_term(spec, term, model=None):
    #noop
    return term


def process_tag(spec, tag, model=None):
    #noop
    return tag


def process_prop(spec, prop, model=None):
    
    return prop


process = {
    Node: process_node,
    Edge: process_reln,
    Property: process_prop,
    Term: process_term,
    Tag: process_tag,
}

def typespec_to_value_domain(spec, prop):
    # simple type
    if isinstance(spec, str):
        return {"value_domain": spec}
    # 
    elif isinstance(spec, dict):
        # regex type
        if spec.get("pattern"):
            return {"value_domain": "regexp",
                    "pattern": spec["pattern"]}
        # numberWithUnits type
        if spec.get("units"):
            return {"value_domain": spec["value_type"],
                    "units": ";".join(spec["units"])}
        # list type
        if spec.get("item_type"):
            return {"value_domain": "list",
                    "item_domain": typespec_to_value_domain(spec["item_type"])}
    elif isinstance(spec, list):
        # do not implement union type for now
        # assume a value_set, as a list of term handles or a single url/path
            
