"""
diff.py

Provides diffing functionality for Bento models
"""
import logging
import sys
from typing import Dict, List, Optional, Tuple, Union

from bento_meta.entity import Entity
from bento_meta.model import Model
from bento_meta.objects import Concept, Edge, Node, Property, Term, ValueSet

sys.path.append("..")


class Diff:
    """for manipulating the final result data structure when diff models"""

    def __init__(self):
        """sets holds tree of models, as it is parsed"""
        self.sets = {"nodes": {}, "edges": {}, "props": {}, "terms": {}}
        self.clss = {"nodes": Node, "edges": Edge, "props": Property, "terms": Term}
        """This will eventually hold the diff results"""
        self.result = {}

    def update_result(
        self,
        ent_type: str,
        entk: Union[str, Tuple[str, str], Tuple[str, str, str]],
        att: str,
        a_att,
        b_att,
    ) -> None:
        """
        Updates the diff result with the given entity key and attribute values.

        Called for 'changed' entities (i.e. those with differing attributes)
        """
        logging.info(
            f"  entering update_result with thing {ent_type}, entk {entk}, att {att}"
        )
        ent_type_dict = self.result.setdefault(ent_type, {"changed": {}})
        entk_dict = ent_type_dict["changed"].setdefault(entk, {})
        att_dict = entk_dict.setdefault(att, {})

        att_dict["removed"] = self.sanitize_empty(a_att)
        att_dict["added"] = self.sanitize_empty(b_att)

    def sanitize_empty_list(self, item: list) -> Optional[list]:
        """an option to turn 'a': [] to 'a': None in final result"""
        if item != []:
            return item
        return None

    def sanitize_empty_dict(self, item: dict) -> Optional[dict]:
        """an option to turn 'a': {} to 'a': None in final result"""
        if item != {}:
            return item
        return None

    def sanitize_empty(self, item: Union[list, dict]) -> Optional[Union[list, dict]]:
        """sanitize item to None if empty"""
        if isinstance(item, dict):
            return self.sanitize_empty_dict(item)
        if isinstance(item, list):
            return self.sanitize_empty_list(item)
        return item

    def valuesets_are_different(self, vs_a, vs_b):
        """see if the group of terms in each value set is different"""
        if set(vs_a.terms) == set(vs_b.terms):
            return False
        return True

    def summarize_result(self) -> None:
        """
        Summarizes the differences in the diff dictionary.

        :param diff: The diff dictionary.
        :return: A string summarizing the differences.
        """

        def create_overall_summary():
            summary_added_removed = []
            summary_changed = []
            for ent_type, diffs in self.result.items():
                ents_with_attr_changes = 0
                attr_changes = 0
                for key in diffs:
                    if key in ["added", "removed"]:
                        count = count_items(ent_type, key)
                        if count > 0:
                            summary_added_removed.append(
                                f"{count} {ent_type[:-1]}(s) {key}"
                            )
                    else:
                        ents_with_attr_changes += 1
                        attr_changes += len(diffs[key])
                        # return "; ".join(changed_parts)
                if ents_with_attr_changes != 0 and attr_changes != 0:
                    summary_changed.append(
                        f"{attr_changes} attribute(s) changed for "
                        f"{ents_with_attr_changes} {ent_type[:-1]}(s)"
                    )

            return "; ".join(summary_added_removed + summary_changed)

        def create_detailed_summary():
            detailed_summary = []
            for ent_type, diffs in self.result.items():
                for key in diffs:
                    if key in ["added", "removed"]:
                        items = get_items(ent_type, key)
                        if not items:
                            continue
                        for item in items:
                            detail = format_detail(ent_type, key, item)
                            detailed_summary.append(detail)
            return "\n".join(detailed_summary)

        def count_items(ent_type, action):
            items = get_items(ent_type, action)
            if not items:
                return 0
            return len(items)

        def get_items(ent_type, action):
            items = self.result.get(ent_type, {}).get(action, {})
            if isinstance(items, dict):
                return list(items.items())
            return items

        def format_detail(ent_type, action, item):
            detail = f"- {action.capitalize()} {ent_type[:-1]}: "
            if ent_type == "nodes":
                detail += f"'{item[0]}'"
            elif ent_type == "edges":
                detail += (
                    f"'{item[0][0]}' with src: '{item[0][1]}' and dst: '{item[0][2]}'"
                )
            elif ent_type == "props":
                detail += f"'{item[0][1]}' with parent: '{item[0][0]}'"
            elif ent_type == "terms":
                detail += f"'{item[0][0]}' with origin: '{item[0][1]}'"
            return detail

        if not self.result:
            return

        overall_summary = create_overall_summary()
        detailed_summary = create_detailed_summary()

        summary_str = f"{overall_summary}\n{detailed_summary}"
        self.result["summary"] = summary_str

    def clean_no_diff(self) -> None:
        """Clean up the result dict by removing empty diffs."""
        to_remove = []
        for ent_type, diffs in self.result.items():
            if all(val is None for val in diffs.values()):
                to_remove.append(ent_type)
        for ent_type in to_remove:
            del self.result[ent_type]

    def finalize_result(self, include_summary=False) -> None:
        """adds info for uniq nodes, edges, props from self.sets back to self.result"""
        logging.info("finalizing result")
        for ent_type, diffs in self.sets.items():
            logging.debug(f"key {ent_type} value {diffs} ")
            logging.debug(f"sets is {self.sets}")
            logging.debug(f"result is {self.result}")

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
            self.summarize_result()


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
        logging.debug(f"ok, where is {ent_type} at?")
        logging.debug(f"aset is {aset}")
        logging.debug(f"bset is {bset}")
        logging.debug(f' you want a:{diff_sets[ent_type]["removed"]}')
        logging.debug(f' you want b:{diff_sets[ent_type]["added"]}')


def diff_simple_atts(
    a_ent: Entity,
    b_ent: Entity,
    simple_atts: List[str],
    ent_type: str,
    entk: Union[str, Tuple[str, str], Tuple[str, str, str]],
    diff: Diff,
) -> None:
    """try and see if the simple attributes are the same"""
    logging.info("...simple")

    for att in simple_atts:
        a_att = getattr(a_ent, att)
        b_att = getattr(b_ent, att)
        if a_att == b_att:
            logging.info(f"...comparing simple {a_att}")
            logging.info(f"...comparing simple {b_att}")
            continue
        diff.update_result(
            ent_type=ent_type, entk=entk, att=att, a_att=a_att, b_att=b_att
        )


def diff_object_atts(
    a_ent: Entity,
    b_ent: Entity,
    obj_atts: List[str],
    ent_type: str,
    entk: Union[str, Tuple[str, str], Tuple[str, str, str]],
    diff: Diff,
) -> None:
    """
    Try and see if the "object" type is the same. a_att, b_att are things like
    concept & value_set that function as containers for collections of terms.

    Other object attributes are generally used to define uniqueness for an
    entity and would be caught by the diff_entities method as added or removed.
    """
    logging.info("...object")
    for att in obj_atts:
        a_att = getattr(a_ent, att)
        b_att = getattr(b_ent, att)

        if a_att == b_att:  # only if both 'None' *or* is same object
            continue
        if not a_att or not b_att:  # one is 'None'
            diff.update_result(
                ent_type=ent_type, entk=entk, att=att, a_att=a_att, b_att=b_att
            )
            continue

        # handle 'term container' objects
        if type(a_att) is type(b_att) and isinstance(a_att, (ValueSet, Concept)):
            if not diff.valuesets_are_different(vs_a=a_att, vs_b=b_att):
                continue
            diff_collection_atts(
                a_ent=a_att,
                b_ent=b_att,
                coll_atts=["terms"],
                ent_type=ent_type,
                entk=entk,
                diff=diff,
            )
        elif getattr(a_att, "handle", None):
            if a_att.handle == b_att.handle:
                continue
            diff.update_result(
                ent_type=ent_type, entk=entk, att=att, a_att=a_att, b_att=b_att
            )
        else:
            attr_warning = f"Can't handle attribute with type {type(a_att).__name__}"
            logging.warning(attr_warning)
            raise AttributeError(attr_warning)


def diff_collection_atts(
    a_ent: Entity,
    b_ent: Entity,
    coll_atts: List[str],
    ent_type: str,
    entk: Union[str, Tuple[str, str], Tuple[str, str, str]],
    diff: Diff,
) -> None:
    """
    Try and see if the "collection" set is the same.

    These are things like props, tags, & terms.
    """
    logging.info("...collection")
    for att in coll_atts:
        a_coll = getattr(a_ent, att)
        b_coll = getattr(b_ent, att)
        if set(a_coll) == set(b_coll):
            continue
        removed_coll = {x: a_coll[x] for x in list(set(a_coll) - set(b_coll))}
        added_coll = {x: b_coll[x] for x in list(set(b_coll) - set(a_coll))}
        if att == "terms":
            if isinstance(a_ent, ValueSet):
                att = "value_set"
            elif isinstance(a_ent, Concept):
                att = "concept"
        diff.update_result(
            ent_type=ent_type,
            entk=entk,
            att=att,
            a_att=removed_coll,
            b_att=added_coll,
        )


def get_ent_atts(ent_type: str, diff: Diff) -> dict:
    """
    Returns dictionary of object attributes by entity type,
    including generic attributes from the Entity class
    """
    # cls becomes a "Node" object, "Edge" object, etc
    cls = diff.clss[ent_type]
    generic_atts = {x: y for x, y in Entity.attspec_.items() if x[0] != "_"}
    class_atts = cls.attspec_
    return {**generic_atts, **class_atts}


def get_simple_atts(ent_atts: dict) -> List[str]:
    """Find the simple attributes from the entity attribute spec"""
    return [x for x, y in ent_atts.items() if y == "simple"]


def get_object_atts(ent_atts: dict) -> List[str]:
    """Find the simple attributes from the entity attribute spec"""
    return [x for x, y in ent_atts.items() if y == "object"]


def get_collection_atts(ent_atts: dict) -> List[str]:
    """Find the simple attributes from the entity attribute spec"""
    return [x for x, y in ent_atts.items() if y == "collection"]


def diff_attributes(diff: Diff) -> None:
    """
    Populate diff.sets with added/removed/changed attributes for common entities.
    """

    sets = diff.sets

    for ent_type, ent_handles in sets.items():
        logging.info(f"now doing ..{ent_type}")
        ent_atts = get_ent_atts(ent_type=ent_type, diff=diff)
        simple_atts = get_simple_atts(ent_atts=ent_atts)
        obj_atts = get_object_atts(ent_atts=ent_atts)
        coll_atts = get_collection_atts(ent_atts=ent_atts)

        for entk, ab_ent_dict in ent_handles["common"].items():
            logging.info(f"...common entk is {entk}")
            a_ent = ab_ent_dict["a"]
            b_ent = ab_ent_dict["b"]

            diff_simple_atts(
                a_ent=a_ent,
                b_ent=b_ent,
                simple_atts=simple_atts,
                ent_type=ent_type,
                entk=entk,
                diff=diff,
            )

            diff_object_atts(
                a_ent=a_ent,
                b_ent=b_ent,
                obj_atts=obj_atts,
                ent_type=ent_type,
                entk=entk,
                diff=diff,
            )

            diff_collection_atts(
                a_ent=a_ent,
                b_ent=b_ent,
                coll_atts=coll_atts,
                ent_type=ent_type,
                entk=entk,
                diff=diff,
            )


def diff_objects_to_attr_dict(obj):
    """Recursively converts bento_meta objects to attribute dictionaries"""
    # If the object has a get_attr_dict method, call it
    if hasattr(obj, "get_attr_dict"):
        return obj.get_attr_dict()

    # If the object is a dictionary, recursively call this function on its values
    if isinstance(obj, dict):
        return {key: diff_objects_to_attr_dict(value) for key, value in obj.items()}

    # If the object is a list or tuple, recursively call this function on its elements
    if isinstance(obj, (list, tuple)):
        return type(obj)(diff_objects_to_attr_dict(elem) for elem in obj)

    # Otherwise, return the object unchanged
    return obj


def diff_models(
    mdl_a: Model, mdl_b: Model, objects_as_dicts=False, include_summary=False
) -> Dict:
    """
    find the diff between two models
    populate the diff results into "sets" and keep some final stuff in result.result

    objects_as_dicts: if set to True, will convert bento_meta objects to attr dicts before returning
    include_summary: if set to True, will include summary string of diff changes
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

    return result
