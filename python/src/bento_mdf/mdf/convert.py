"""
bento_mdf.mdf.convert
=====================

Utilities for converting MDF YAML to bento-meta objects
"""
import re
from urllib.parse import unquote
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
    #
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

def spec_to_entity(hdl, spec, init, entCls):
    for k in spec:
        if k in mdf_to_meta and mdf_to_meta[k] != None:
            init[mdf_to_meta[k]] = spec[k]
    if hdl and "handle" not in init:
        init["handle"] = hdl
    # init now contains (translated) spec keys and its original keys
    ent = entCls(init)
    info = process[entCls](init, ent)
    if "Tags" in spec and spec["Tags"]:
        for t in spec["Tags"]:
            ent.tags[t] = spec_to_entity(
                "", {}, {"key":t, "value": spec["Tags"][t],
                         "_commit": init.get("_commit")},
                Tag)
    return ent


def process_node(spec, node):
    # noop
    return


def process_reln(spec, edge):
    #noop
    return


def process_term(spec, term):
    if not term.handle:
        term.handle = to_snake_case(term.value)
    if spec.get("definition"):
        term.definition = unquote(term, spec["definition"])
    return


def process_tag(spec, tag):
    #noop
    return


def process_prop(spec, prop):
    ty_spec = spec.get("Enum") or spec.get("Type")
    domain_spec = typespec_to_domain_spec(ty_spec)
    if domain_spec["value_domain"] != "value_set":
        for attr in domain_spec:
            prop.__setattr__(attr, domain_spec[attr])
    else: # is "value_set"
        prop.value_domain = "value_set"
        if domain_spec.get("url"):
            prop.value_set = ValueSet({"url": domain_spec["url"],
                                       "_commit": prop._commit})
        elif domain_spec.get("value_set"):
            # create 'dummy' ValueSet to hold Enum terms,
            # but merge them with any Terms section terms in mdf.py
            prop.value_set = ValueSet({"_commit":"dummy"})
            for tm_init in domain_spec["value_set"]:
                tm_init["origin_name"] = prop.model
                term = spec_to_entity(None,
                                      {"_commit": prop._commit},
                                      tm_init, Term)
                prop.value_set.terms[term.handle] = term
        else:
            raise RuntimeError("Can't evaluate value_set spec {domain_spec}")
    return


process = {
    Node: process_node,
    Edge: process_reln,
    Property: process_prop,
    Term: process_term,
    Tag: process_tag,
}


def typespec_to_domain_spec(spec):
    # simple type
    if isinstance(spec, str):
        return {"value_domain": spec}
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
                    "item_domain": typespec_to_domain_spec(spec["item_type"])}
    # enum type
    elif isinstance(spec, list):
        # do not implement union type for now
        # assume a value_set, as a list of term handles or a single url/path
        # don't merge terms here, but in process_prop
        # list of term initializers returned
        #   term values == term handles
        if len(spec) == 1 and isinstance(spec[0], str) and re.match(
                "^/|.*://", spec[0]
        ):
            return {"value_domain": "value_set",
                    "url": spec[0]}
        else:
            vs = []
            for tm in spec:
                if isinstance(tm, bool):
                    tm = "True" if tm else "False"; # stringify any booleans
                vs.append({"handle": tm, "value": tm})
            return {"value_domain": "value_set",
                    "value_set": vs}
    # unknown - default domain
    else:
        return {"value_domain": Property.default("value_domain")}

