"""Provides diffing functionality for Bento models."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bento_meta.entity import CollValue, Entity
from bento_meta.objects import Concept, Edge, Node, Property, Tag, Term, ValueSet

from bento_mdf.diff_summary import DiffSummary

if TYPE_CHECKING:
    from bento_meta.model import Model


class Diff:
    """Class for manipulating the final result data structure when diff models."""

    def __init__(self) -> None:
        """Initialize the diff object. Sets hold tree of model as it is parsed."""
        self.sets = {"nodes": {}, "edges": {}, "props": {}, "terms": {}}
        self.clss = {"nodes": Node, "edges": Edge, "props": Property, "terms": Term}
        self.result = {}  # This will eventually hold the diff results
        self.annotations = {"nodes": {}, "edges": {}, "props": {}, "terms": {}}

    def update_result(
        self,
        ent_type: str,
        entk: str | tuple[str, str] | tuple[str, str, str],
        att: str,
        a_att: str | int | Entity | CollValue | dict[str, Tag] | list | None,
        b_att: str | int | Entity | CollValue | dict[str, Tag] | list | None,
    ) -> None:
        """
        Update the diff result with the given entity key and attribute values.

        Called for 'changed' entities (i.e. those with differing attributes)
        """
        logging.info(
            "  entering update_result with thing %s, entk %s, att %s",
            ent_type,
            entk,
            att,
        )
        ent_type_dict = self.result.setdefault(ent_type, {"changed": {}})
        entk_dict = ent_type_dict["changed"].setdefault(entk, {})
        att_dict = entk_dict.setdefault(att, {})

        att_dict["removed"] = self.sanitize_empty(a_att)
        att_dict["added"] = self.sanitize_empty(b_att)

    def sanitize_empty_list(self, item: list) -> list | None:
        """Turn 'a': [] to 'a': None in final result."""
        if item != []:
            return item
        return None

    def sanitize_empty_dict(self, item: dict) -> dict | None:
        """Turn 'a': {} to 'a': None in final result."""
        if item != {}:
            return item
        return None

    def sanitize_empty(
        self,
        item: str | int | Entity | CollValue | dict[str, Tag] | list | None,
    ) -> str | int | Entity | CollValue | dict[str, Tag] | list | None:
        """Sanitize item to None if empty."""
        if isinstance(item, dict):
            return self.sanitize_empty_dict(item)
        if isinstance(item, list):
            return self.sanitize_empty_list(item)
        return item

    def valuesets_are_different(
        self,
        vs_a: ValueSet | Concept,
        vs_b: ValueSet | Concept,
    ) -> bool:
        """See if the group of terms in each value set is different."""
        if set(vs_a.terms) == set(vs_b.terms):
            return False
        return True

    def clean_no_diff(self) -> None:
        """Clean up the result dict by removing empty diffs."""
        to_remove = []
        for ent_type, diffs in self.result.items():
            if all(val is None for val in diffs.values()):
                to_remove.append(ent_type)
        for ent_type in to_remove:
            del self.result[ent_type]

    def finalize_result(self, *, include_summary: bool = False) -> None:
        """Add info for uniq nodes, edges, props from self.sets back to self.result."""
        logging.info("finalizing result")
        for ent_type, diffs in self.sets.items():
            logging.debug("key %s value %s ", ent_type, diffs)
            logging.debug("sets is %s", self.sets)
            logging.debug("result is %s", self.result)

            # if (value["removed"] != []) or (value["added"] != []):
            if (diffs["removed"] is not None) or (diffs["added"] is not None):
                cleaned_a = self.sanitize_empty(diffs["removed"])
                cleaned_b = self.sanitize_empty(diffs["added"])

                # the key (node/edges/prop) may not be in results (no common diff yet found!)
                if ent_type not in self.result:
                    self.result[ent_type] = {}
                self.result[ent_type].update({"removed": cleaned_a, "added": cleaned_b})
        self.clean_no_diff()
        if include_summary:
            self.result["summary"] = DiffSummary(self).create_summary()


def diff_entities(mdl_a: Model, mdl_b: Model, diff: Diff) -> None:
    """
    Populate diff.sets with unique entities from each model.

    "removed": entity in mdl_a but not in mdl_b
    "added": entity in mdl_b but not in mdl_a
    "common": entity found in both models
    """
    diff_sets = diff.sets

    for ent_type, ent_handles in diff_sets.items():
        a_ents = getattr(mdl_a, ent_type)
        b_ents = getattr(mdl_b, ent_type)
        aset = set(a_ents)
        bset = set(b_ents)
        ent_handles["removed"] = {x: a_ents[x] for x in set(aset - bset)}
        ent_handles["added"] = {x: b_ents[x] for x in set(bset - aset)}
        ent_handles["common"] = {
            x: {"a": a_ents[x], "b": b_ents[x]} for x in set(aset & bset)
        }
        logging.debug("ok, where is %s at?", ent_type)
        logging.debug("aset is %s", aset)
        logging.debug("bset is %s", bset)
        logging.debug(" you want a: %s", diff_sets[ent_type]["removed"])
        logging.debug(" you want b: %s", diff_sets[ent_type]["added"])


def diff_simple_atts(
    a_ent: Entity,
    b_ent: Entity,
    simple_atts: list[str],
    ent_type: str,
    entk: str | tuple[str, str] | tuple[str, str, str],
    diff: Diff,
) -> None:
    """Check if the simple attributes are the same."""
    logging.info("...simple")

    for att in simple_atts:
        a_att = getattr(a_ent, att)
        b_att = getattr(b_ent, att)
        if a_att == b_att:
            logging.info("...comparing simple %s", a_att)
            logging.info("...comparing simple %s", b_att)
            continue
        diff.update_result(ent_type, entk, att, a_att, b_att)


def diff_object_atts(
    a_ent: Entity,
    b_ent: Entity,
    obj_atts: list[str],
    ent_type: str,
    entk: str | tuple[str, str] | tuple[str, str, str],
    diff: Diff,
) -> None:
    """
    Check if the "object" type attrs are the same.

    a_att, b_att are entities like concept & value_set that function as containers
    for collections of terms.

    Other object attributes are generally used to define uniqueness for an
    entity and should be caught by the diff_entities method as added or removed.
    """
    logging.info("...object")
    for att in obj_atts:
        a_att = getattr(a_ent, att)
        b_att = getattr(b_ent, att)
        if a_att == b_att:  # only if both 'None' *or* is same object
            continue
        # handle 'term container' objects
        if att == "concept":
            diff.annotations[ent_type][entk] = {
                "removed": getattr(a_att, "terms", None),
                "added": getattr(b_att, "terms", None),
            }
        if not a_att and isinstance(b_att, (ValueSet, Concept)):
            a_att = Concept() if att == "concept" else ValueSet()
            diff_collection_atts(a_att, b_att, ["terms"], ent_type, entk, diff)
        if not b_att and isinstance(a_att, (ValueSet, Concept)):
            b_att = Concept() if att == "concept" else ValueSet()
            diff_collection_atts(a_att, b_att, ["terms"], ent_type, entk, diff)
        if type(a_att) is type(b_att) and isinstance(a_att, (ValueSet, Concept)):
            if not diff.valuesets_are_different(a_att, b_att):
                continue
            diff_collection_atts(a_att, b_att, ["terms"], ent_type, entk, diff)
        elif getattr(a_att, "handle", None):
            if a_att.handle == b_att.handle:
                continue
            diff.update_result(ent_type, entk, att, a_att, b_att)
        else:
            attr_warning = f"Can't handle attribute with type {type(a_att).__name__}"
            logging.warning(attr_warning)
            raise AttributeError(attr_warning)


def diff_collection_atts(
    a_ent: Entity,
    b_ent: Entity,
    coll_atts: list[str],
    ent_type: str,
    entk: str | tuple[str, str] | tuple[str, str, str],
    diff: Diff,
) -> None:
    """Check if the "collection" attributes (e.g. props, tags, terms) are the same."""
    logging.info("...collection")
    for att in coll_atts:
        a_coll = getattr(a_ent, att)
        b_coll = getattr(b_ent, att)
        if set(a_coll) == set(b_coll):
            # compare simple atts for coll atts that don't already (e.g. tags)
            if att == "tags":
                diff_tag_values(a_coll, b_coll, ent_type, entk, diff)
            continue
        removed_coll = {x: a_coll[x] for x in list(set(a_coll) - set(b_coll))}
        added_coll = {x: b_coll[x] for x in list(set(b_coll) - set(a_coll))}
        if att == "terms":
            if isinstance(a_ent, ValueSet):
                att = "value_set"
            elif isinstance(a_ent, Concept):
                att = "concept"
        diff.update_result(ent_type, entk, att, removed_coll, added_coll)


def diff_tag_values(
    a_tags: dict[str, Tag],
    b_tags: dict[str, Tag],
    ent_type: str,
    entk: str | tuple[str, str] | tuple[str, str, str],
    diff: Diff,
) -> None:
    """Diff values for tags w/ same key."""
    for tagk, a_tag in a_tags.items():
        b_tag = b_tags[tagk]
        if a_tag.value == b_tag.value:
            continue
        diff.update_result(ent_type, entk, "tags", {tagk: a_tag}, {tagk: b_tag})


def get_ent_atts(ent_type: str, diff: Diff) -> dict:
    """
    Return dictionary of object attributes by entity type.

    Includes generic attributes from the Entity class.
    """
    # cls becomes a "Node" object, "Edge" object, etc
    cls = diff.clss[ent_type]
    generic_atts = {x: y for x, y in Entity.attspec_.items() if x[0] != "_"}
    class_atts = cls.attspec_
    return {**generic_atts, **class_atts}


def get_simple_atts(ent_atts: dict) -> list[str]:
    """Find the simple attributes from the entity attribute spec."""
    return [x for x, y in ent_atts.items() if y == "simple"]


def get_object_atts(ent_atts: dict) -> list[str]:
    """Find the object attributes from the entity attribute spec."""
    return [x for x, y in ent_atts.items() if y == "object"]


def get_collection_atts(ent_atts: dict) -> list[str]:
    """Find the collection attributes from the entity attribute spec."""
    return [x for x, y in ent_atts.items() if y == "collection"]


def diff_attributes(diff: Diff) -> None:
    """Populate diff.sets with added/removed/changed attributes for common entities."""
    sets = diff.sets

    for ent_type, ent_handles in sets.items():
        logging.info("now doing ..%s", ent_type)
        ent_atts = get_ent_atts(ent_type, diff)
        simple_atts = get_simple_atts(ent_atts)
        obj_atts = get_object_atts(ent_atts)
        coll_atts = get_collection_atts(ent_atts)

        for entk, ab_ent_dict in ent_handles["common"].items():
            logging.info("...common entk is %s", entk)
            a_ent = ab_ent_dict["a"]
            b_ent = ab_ent_dict["b"]

            diff_simple_atts(a_ent, b_ent, simple_atts, ent_type, entk, diff)

            diff_object_atts(a_ent, b_ent, obj_atts, ent_type, entk, diff)

            diff_collection_atts(a_ent, b_ent, coll_atts, ent_type, entk, diff)


def diff_objects_to_attr_dict(
    obj: Entity | dict | list | tuple,
) -> Entity | dict | list | tuple:
    """Recursively convert bento_meta objects to attribute dictionaries."""
    # If the object has a get_attr_dict method, call it
    if hasattr(obj, "get_attr_dict") and isinstance(obj, Entity):
        # kludge: add False" attr values to entity attr dict until fixed in bento-meta
        attr_dict = obj.get_attr_dict()
        for att in type(obj).attspec:
            if att not in attr_dict and getattr(obj, att) is False:
                attr_dict[att] = "False"
        return attr_dict

    # If the object is a dictionary, recursively call this function on its values
    if isinstance(obj, dict):
        return {key: diff_objects_to_attr_dict(value) for key, value in obj.items()}

    # If the object is a list or tuple, recursively call this function on its elements
    if isinstance(obj, (list, tuple)):
        return type(obj)(diff_objects_to_attr_dict(elem) for elem in obj)

    return obj


def diff_models(
    mdl_a: Model,
    mdl_b: Model,
    *,
    objects_as_dicts: bool = False,
    include_summary: bool = False,
) -> dict:
    """
    Find the diff between two models.

    Populate the diff results into "sets" and keep some final stuff in result.result

    objects_as_dicts: return attr dicts instead of bento_meta objects.
    include_summary: include a summary of the diff in the result.
    """
    diff_ = Diff()

    logging.info("point A")
    diff_entities(mdl_a, mdl_b, diff_)

    logging.info("point B")
    diff_attributes(diff_)

    logging.info("done")
    diff_.finalize_result(include_summary=include_summary)
    result = diff_.result

    if objects_as_dicts:
        result = diff_objects_to_attr_dict(result)
        if not isinstance(result, dict):
            msg = "Error converting Entities in diff to attribute dictionaries."
            raise ValueError(msg)

    return result
