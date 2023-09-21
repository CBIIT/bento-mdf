"""
diff.py

Provides diffing functionality for Bento models
"""
import logging
import sys
from typing import Dict, List, Optional, Tuple, Union
from warnings import warn

from bento_meta.entity import Entity
from bento_meta.model import Model
from bento_meta.objects import Concept, Edge, Node, Property, ValueSet

sys.path.append("..")


class Diff:
    """for manipulating the final result data structure when diff models"""

    def __init__(self):
        """sets holds tree of models, as it is parsed"""
        self.sets = {"nodes": {}, "edges": {}, "props": {}}
        # "terms": {} }
        self.clss = {"nodes": Node, "edges": Edge, "props": Property}
        """This will eventually hold the diff results"""
        self.result = {}

    def update_result(
        self, thing: str, entk: Union[str, Tuple[str, str]], att: str, a_att, b_att
    ) -> None:
        """Updates the diff result with the given entity key and attribute values."""
        logging.info(
            f"  entering update_result with thing {thing}, entk {entk}, att {att}"
        )
        if thing not in self.result:
            self.result[thing] = {}
        if entk not in self.result[thing]:
            self.result[thing][entk] = {}
        if att not in self.result[thing][entk]:
            self.result[thing][entk][att] = {}
        cleaned_a_att = self.sanitize_empty_list(a_att)
        cleaned_b_att = self.sanitize_empty_list(b_att)
        self.result[thing][entk][att]["removed"] = cleaned_a_att
        self.result[thing][entk][att]["added"] = cleaned_b_att

    def sanitize_empty_list(self, item: List) -> Optional[List]:
        """an option to turn 'a': [] to 'a': None in final result"""
        if item != []:
            return item
        return None

    def valuesets_are_different(self, vs_a, vs_b):
        """see if the group of terms in each value set is different"""

        # compare sets of terms
        # a_att.terms
        #   {'FFPE': <bento_meta.objects.Term object at 0x10..>,
        #    'Snap Frozen': <bento_meta.objects.Term object at 0x10..>}
        # set(a_att.terms)
        #   {'Snap Frozen', 'FFPE'}
        set_of_terms_in_a = set(vs_a.terms)
        set_of_terms_in_b = set(vs_b.terms)

        if set_of_terms_in_a == set_of_terms_in_b:
            return False
        return True

    def finalize_result(self) -> None:
        """adds info for uniq nodes, edges, props from self.sets back to self.result"""
        logging.info("finalizing result")
        for key, value in self.sets.items():
            logging.debug(f"key {key} value {value} ")
            logging.debug(f"sets is {self.sets}")
            logging.debug(f"result is {self.result}")

            if (value["removed"] != []) or (value["added"] != []):
                cleaned_a = self.sanitize_empty_list(value["removed"])
                cleaned_b = self.sanitize_empty_list(value["added"])

                # the key (node/edges/prop) may not be in results (no common diff yet found!)
                if key not in self.result:
                    self.result[key] = {}
                self.result[key].update({"removed": cleaned_a, "added": cleaned_b})


# TODO: separate functionality - currently diffs ents btwn the 2 models
# as well as fetching the actual bento-meta Entities from the models?
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
    entk: Union[str, Tuple[str, str]],
    diff: Diff,
) -> None:
    """try and see if the simple attributes are the same"""
    logging.info("...simple")

    for att in simple_atts:
        if getattr(a_ent, att) == getattr(b_ent, att):
            logging.info(f"...comparing simple {getattr(a_ent, att)}")
            logging.info(f"...comparing simple {getattr(b_ent, att)}")
            continue
        diff.update_result(
            ent_type,
            entk,
            att,
            getattr(a_ent, att),
            getattr(b_ent, att),
        )


def diff_object_atts(
    a_ent: Entity,
    b_ent: Entity,
    obj_atts: List[str],
    ent_type: str,
    entk: Union[str, Tuple[str, str]],
    diff: Diff,
) -> None:
    """
    try and see if the "object" type is the same?

    a_att,b_att are things like "valuesets", "properties"
    """
    logging.info("...object")
    for att in obj_atts:
        a_att = getattr(a_ent, att)
        b_att = getattr(b_ent, att)

        if a_att == b_att:  # only if both 'None' *or* is same object
            continue
        if not a_att or not b_att:  # one is 'None'
            diff.update_result(ent_type, entk, att, a_att, b_att)
            continue

        if type(a_att) is type(b_att):
            if isinstance(a_att, ValueSet):  # kludge for ValueSet+Terms
                if diff.valuesets_are_different(a_att, b_att):
                    diff.update_result(
                        ent_type,
                        entk,
                        att,
                        list(set(a_att.terms) - set(b_att.terms)),
                        list(set(b_att.terms) - set(a_att.terms)),
                    )
            # items are something-other-than valuesets
            # items are concepts
            elif isinstance(a_att, Concept):
                continue  # new concept nanos generated when Model loaded so can't compare???
            elif getattr(a_att, "handle"):
                if a_att.handle == b_att.handle:
                    continue
                diff.update_result(ent_type, entk, att, a_att, b_att)
            else:
                warn(f"can't handle attribute with type {type(a_att).__name__}")
                logging.warning(
                    f"can't handle attribute with type {type(a_att).__name__}"
                )
        else:
            diff.update_result(ent_type, entk, att, a_att, b_att)


def diff_collection_atts(
    a_ent: Entity,
    b_ent: Entity,
    coll_atts: List[str],
    ent_type: str,
    entk: Union[str, Tuple[str, str]],
    diff: Diff,
) -> None:
    """try and see if the "collection" set is the same?"""
    logging.info("...collection")
    for att in coll_atts:
        aset = set(getattr(a_ent, att))
        bset = set(getattr(b_ent, att))
        if aset != bset:
            diff.update_result(
                ent_type,
                entk,
                att,
                list(set(aset - bset)),
                list(set(bset - aset)),
            )


def diff_attributes(diff: Diff) -> None:
    """
    Populate diff.sets with added/removed/changed attributes for common entities.
    """

    sets = diff.sets
    clss = diff.clss

    for ent_type, ent_handles in sets.items():
        logging.info(f"now doing ..{ent_type}")
        # cls becomes a "Node" object, "Edge" object, etc
        cls = clss[ent_type]

        simple_atts = [x for x, y in cls.attspec_.items() if y == "simple"]
        obj_atts = [x for x, y in cls.attspec_.items() if y == "object"]
        coll_atts = [x for x, y in cls.attspec_.items() if y == "collection"]

        for entk, ab_ent_dict in ent_handles["common"].items():
            logging.info(f"...common entk is {entk}")
            a_ent = ab_ent_dict["a"]
            b_ent = ab_ent_dict["b"]

            diff_simple_atts(a_ent, b_ent, simple_atts, ent_type, entk, diff)

            diff_object_atts(a_ent, b_ent, obj_atts, ent_type, entk, diff)

            diff_collection_atts(a_ent, b_ent, coll_atts, ent_type, entk, diff)


def diff_models(mdl_a: Model, mdl_b: Model) -> Dict:
    """
    find the diff between two models
    populate the diff results into "sets" and keep some final stuff in result.result
    """
    diff_ = Diff()

    logging.info("point A")
    diff_entities(mdl_a, mdl_b, diff_)

    logging.info("point B")
    diff_attributes(diff_)

    logging.info("done")
    diff_.finalize_result()
    return diff_.result
