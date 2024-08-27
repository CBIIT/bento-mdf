"""
bento_mdf.mdf
==============

This module contains :class:`MDF`, a class for reading a graph data model in
Model Description Format into a :class:`bento_meta.model.Model` object, and
writing the opposite way.

"""
import json
import logging
import re
import sys
from collections import ChainMap
from tempfile import TemporaryFile
from typing import Dict

import requests
import yaml
from .convert import to_snake_case, spec_to_entity
from ..validator import MDFValidator
from bento_meta.entity import ArgError, Entity
from bento_meta.model import Model
from bento_meta.objects import Edge, Node, Property, Tag, Term, ValueSet
from nanoid import generate
from tqdm import tqdm

sys.path.extend([".", ".."])


def make_nano():
    return generate(
        size=6, alphabet="abcdefghijkmnopqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ0123456789"
    )


class MDF(object):
    def __init__(
        self,
        *yaml_files,
        handle=None,
        model=None,
        _commit=None,
        mdf_schema=None,
        raiseError=False,
        logger=logging.getLogger(__name__),
    ):
        """Create a :class:`Model` from MDF YAML files/Write a :class:`Model` to YAML
        :param str|file|url *yaml_files: MDF filenames or file objects,
        in desired merge order
        :param str handle: Handle (name) for the resulting Model
        :param :class:`Model` model: Model to convert to MDF
        :param boolean raiseError: raise on error if True
        :param :class:`logging.Logger` logger: Python logger (suitable default)
        :attribute model: the :class:`bento_meta.model.Model` created"""
        if model and not isinstance(model, Model):
            raise ArgError("arg model= must be a Model instance")

        self.files = yaml_files
        self.mdf = {}
        self.mdf_schema = mdf_schema
        self._model = model
        self._commit = _commit
        self._terms = {}
        self._props = {}
        self.version = None
        self.uri = None
        self.logger = logger
        if model:
            self.handle = model.handle
        else:
            self.handle = handle
        if self.files:
            self.load_yaml()
            self.create_model(raiseError=raiseError)
        else:
            if not model:
                self.logger.warning("No MDF files or model provided to constructor")

    @property
    def model(self):
        """The :class:`bento_meta.model.Model` object created from the
        MDF input"""
        return self._model

    def load_yaml(self, verify=True):
        """Validate and load YAML files or open file handles specified in constructor"""
        vargs = []
        for f in self.files:
            if isinstance(f, str):
                if re.match("(?:file|https?)://", f):
                    response = requests.get(f, verify=verify)
                    if not response.ok:
                        self.logger.error(
                            "Fetching url {} returned code {}".format(
                                response.url, response.status_code
                            )
                        )
                        raise ArgError(
                            "Fetching url {} returned code {}".format(
                                response.url, response.status_code
                            )
                        )
                    response.encoding = "utf8"
                    fh = TemporaryFile()
                    for chunk in response.iter_content(chunk_size=128):
                        fh.write(chunk)
                    fh.seek(0)
                    vargs.append(fh)
                else:
                    fh = open(f, "r")
                    vargs.append(fh)
            else:
                vargs.append(f)

        v = MDFValidator(self.mdf_schema, *vargs, raiseError=True)
        self.mdf_schema = v.load_and_validate_schema()
        self.mdf = v.load_and_validate_yaml()
        self.mdf = self.mdf.as_dict()

    def create_model(self, raiseError=False):
        """Create :class:`Model` instance from loaded YAML
        :param boolean raiseError: Raise if MDF errors found
        Note: This is brittle, since the syntax of MDF is hard-coded
        into this method."""
        success = True
        if not self.mdf.keys():
            raise ValueError("attribute 'mdf' not set - are yamls loaded?")
        if self.mdf.get("Version"):
            self.version = self.mdf["Version"]
        if self.mdf.get("URI"):
            self.uri = self.mdf["URI"]
        if self.handle:
            self._model = Model(handle=self.handle,
                                version=self.version,
                                uri=self.uri)
        elif self.mdf.get("Handle"):
            self.handle = self.mdf["Handle"]
            self._model = Model(handle=self.mdf["Handle"],
                                version=self.version,
                                uri=self.uri)
        else:
            self.logger.error("Model handle not present in MDF nor provided in args")
            success = False
        ypropdefs = self.mdf["PropDefinitions"]
        yterms = self.mdf.get("Terms")
        yunps = self.mdf.get("UniversalNodeProperties")
        yurps = self.mdf.get("UniversalRelationshipProperties")


        # create terms first, if any -- properties depend on these
        if "Terms" in self.mdf:
            for t_hdl in tqdm(self.mdf["Terms"]):
                spec = self.mdf["Terms"][t_hdl]
                if "Value" not in spec:
                    self.logger.error(
                        f"Term specs must have a Value key and a non-null string value (term '{t_hdl}')"
                    )
                    success = False
                if "Origin" not in spec:
                    self.logger.warning(
                        f"No Origin provided for term '{t_hdl}'"
                    )
                term = spec_to_entity(t_hdl, spec,
                                      {"_commit": self._commit},
                                      Term)
                self._terms[(term.handle, term.origin_name)] = term

        # create nodes
        for n in self.mdf["Nodes"]:
            spec = self.mdf["Nodes"][n]
            node = self._model.add_node(
                spec_to_entity(n, spec, 
                               {"model": self.handle, "_commit": self._commit},
                               Node, self._model)
            )
            if "Term" in spec:
                self.annotate_entity_from_mdf(node, spec["Term"])

        # create edges (relationships)
        for e in self.mdf["Relationships"]:
            spec = self.mdf["Relationships"][e]
            for ends in spec["Ends"]:
                if ends["Src"] not in self._model.nodes:
                    self.logger.warning(
                        "No node '{src}' defined for edge "
                        "spec '{ename}' from '{src}' to '{dst}'".format(
                            src=ends["Src"], dst=ends["Dst"], ename=e
                        )
                    )
                    continue
                if ends["Dst"] not in self._model.nodes:
                    self.logger.warning(
                        "No node '{dst}' defined for edge "
                        "spec '{ename}' from '{src}' to '{dst}'".format(
                            src=ends["Src"], dst=ends["Dst"], ename=e
                        )
                    )
                    continue
                init = {
                    "handle": e,
                    "model": self.handle,
                    "src": self._model.nodes[ends["Src"]],
                    "dst": self._model.nodes[ends["Dst"]],
                    "multiplicity": ends.get("Mul") or spec.get("Mul"),
                    "desc": ends.get("Desc") or spec.get("Desc"),
                    "_commit": self._commit,
                }
                if not init["multiplicity"]:
                    self.logger.warning(
                        "edge '{ename}' from '{src}' to '{dst}' "
                        "does not specify a multiplicity".format(
                            ename=e, src=ends["Src"], dst=ends["Dst"]
                        )
                    )
                    init["multiplicity"] = Edge.default("multiplicity")
                if init["multiplicity"] not in (
                    "many_to_many",
                    "many_to_one",
                    "one_to_many",
                    "one_to_one",
                ):
                    self.logger.warning(
                        "edge '{ename}' from '{src}' to '{dst}'"
                        " has non-standard multiplicity '{mult}'".format(
                            ename=e,
                            src=ends["Src"],
                            dst=ends["Dst"],
                            mult=init["multiplicity"],
                        )
                    )
                # if tags are set in the Ends entry, these will be attached
                # to the Edge, _rather than_ tags set in the "edge key" or spec
                # level
                spec["Tags"] = ends.get("Tags") or spec.get("Tags")
                edge = self._model.add_edge(
                    spec_to_entity(e, spec, init,
                                   Edge, self._model)
                )
                term = ends.get("Term") or spec.get("Term")
                if term:
                    self.annotate_entity_from_mdf(edge, term)

        # create properties
        propnames = {}
        for ent in ChainMap(self._model.nodes, self._model.edges).values():
            if isinstance(ent, Node):
                pnames = ynodes[ent.handle]["Props"]
                if yunps:  # universal node props
                    pnames.extend(yunps["mayHave"] if yunps.get("mayHave") else [])
                    pnames.extend(yunps["mustHave"] if yunps.get("mustHave") else [])
                if pnames:
                    propnames[ent] = pnames
            elif isinstance(ent, Edge):
                # props elts appearing in Ends hash take precedence over
                # Props elt in the handle's hash
                (hdl, src, dst) = ent.triplet
                ends = [
                    e
                    for e in yedges[hdl]["Ends"]
                    if e["Src"] == src and e["Dst"] == dst
                ]
                if len(ends) > 1:
                    self.logger.warning(
                        "edge '{ename}' has more than one Ends pair Src:'{src}',"
                        "Dst:'{dst}'".format(ename=hdl, src=src, dst=dst)
                    )
                end = ends[0]

                # note the end-specified props _replace_ the edge-specified props,
                # they are not merged:
                pnames = end.get("Props") or yedges[hdl].get("Props")
                if yurps:  # universal relationship props
                    pnames.extend(yurps["mayHave"] if yurps.get("mayHave") else [])
                    pnames.extend(yurps["mustHave"] if yurps.get("mustHave") else [])
                if pnames:
                    propnames[ent] = pnames
            else:
                self.logger.error(
                    "Unhandled entity type {type} for properties".format(
                        type=type(ent).__name__
                    )
                )
                success = False
        prop_of = {}
        for ent in propnames:
            for p in propnames[ent]:
                if prop_of.get(p):
                    prop_of[p].append(ent)
                else:
                    prop_of[p] = [ent]
        defns_for = set(ypropdefs.keys())
        for pname in prop_of:
            for ent in prop_of[pname]:
                force = False
                # see if a qualified name is defined in propdefs:
                key = ent.handle + "." + pname
                ypdef = ypropdefs.get(key)
                if ypdef:
                    # force creation of new prop for a explicitly qualified MDF property
                    force = True
                else:
                    key = pname
                    ypdef = ypropdefs.get(pname)
                if not ypdef:
                    self.logger.warning(
                        "property '{pname}' does not have a corresponding "
                        "propdef for entity '{handle}'".format(
                            pname=pname, handle=ent.handle
                        )
                    )
                    continue
                else:
                    if key in defns_for:
                        defns_for.remove(key)
                prop = self.create_or_merge_prop_from_mdf(
                    ypdef, p_hdl=pname, force_create=force
                )
                self._model.add_prop(ent, prop)
                ent.props[prop.handle] = prop
        if defns_for:
            self.logger.warning(
                "No properties in model corresponding to the following "
                "PropDefintions: {}".format(defns_for)
            )
        if raiseError and not success:
            raise RuntimeError("MDF errors found; see log output.")
        return self._model

    def create_or_merge_prop_from_mdf(self, spec, p_hdl, force_create):
        if not force_create and (self.handle, p_hdl) in self._props:
            return
        prop = spec_to_entity(
            p_hdl, spec,
            {"handle": p_hdl, "model": self.handle, "_commit": self._commit},
            Property, self._model)
        if "Term" in spec:
            self.annotate_entity_from_mdf(prop, spec["Term"])
        if force_create:
            return prop
        self._props[(prop.model, prop.handle)] = prop
        return self._props[(prop.model, prop.handle)]

    def annotate_entity_from_mdf(self, ent, yterm_list):
        for spec in yterm_list:
            if "Value" not in spec:
                self.logger.error(
                    f"Term specs must have a Value key and a non-null string value, in entity '{ent.handle}'"
                )
                return False
            if "Origin" not in spec:
                self.logger.warning(
                    f"No Origin provided for Term annotation in entity '{ent.handle}'"
                )
                spec["Origin"] = self.handle
            term = spec_to_entity(None, spec,
                                  {"_commit": self._commit},
                                  Term
                                  )
            # merge or record term
            if not self._terms.get((term.handle, term.origin_name)):
                self._terms[(term.handle, term.origin_name)] = term
            else:
                term = self._terms[(term.handle, term.origin_name)]

            self._model.annotate(ent, term)
            if self._commit:
                if not ent.concept._commit:
                    ent.concept._commit = self._commit

    def add_entity_tags_to_mdf(self, entity: Entity, mdf_entity: Dict):
        """If entity has tags property, add them to its MDF representation"""
        if not entity.tags:
            return
        mdf_entity["Tags"] = {}
        for t in entity.tags:
            mdf_entity["Tags"][t] = entity.tags[t].value

    def write_mdf(self, model=None, file=None):
        """
        Write a :class:`Model` to a model description file (MDF)
        :param :class:`Model` model: Model to convert (if None, use the model attribute of the MDF object)
        :param str|file file: File name or object to write to (default is None; just return the MDF as dict)
        :returns: MDF as dict
        """
        if not model:
            model = self.model
        mdf = {
            "Nodes": {},
            "Relationships": {},
            "PropDefinitions": {},
            "Terms": {},
            "Handle": model.handle,
        }
        for nd in sorted(model.nodes):
            node = model.nodes[nd]
            mdf_node = {}
            mdf["Nodes"][nd] = mdf_node
            self.add_entity_tags_to_mdf(entity=node, mdf_entity=mdf_node)
            self.add_entity_concept_to_mdf(entity=node, mdf_entity=mdf_node)

            mdf_node["Props"] = list(sorted(node.props))

            if node.nanoid:
                mdf_node["NanoID"] = node.nanoid
            if node.desc:
                mdf_node["Desc"] = node.desc
        # write props only in Ends object (no default set of properties)
        # MDF - if props are defined above the Ends object, this is the default set of properties
        # for any fully qualified edge without explicit properties. But if there are explict
        # properties applied to a fully qualified edge (i.e., in the Ends object), these are
        # the only properties for that edge.
        for rl in sorted(model.edges):
            edge = model.edges[rl]
            mdf_edge = {}
            ends = {}
            if edge.handle in mdf["Relationships"]:
                mdf_edge = mdf["Relationships"][edge.handle]
            else:
                mdf["Relationships"][edge.handle] = mdf_edge
            ends = {"Src": edge.src.handle, "Dst": edge.dst.handle}
            if "Ends" in mdf_edge:
                mdf_edge["Ends"].append(ends)
            else:
                mdf_edge["Ends"] = [ends]
            if "Mul" not in mdf_edge:
                mdf_edge["Mul"] = edge.multiplicity or Edge.default("multiplicity")
            else:
                if mdf_edge["Mul"] != edge.multiplicity:
                    ends["Mul"] = edge.multiplicity
            self.add_entity_tags_to_mdf(entity=edge, mdf_entity=mdf_edge)
            if edge.is_required:
                ends["Req"] = True
            if edge.props:
                ends["Props"] = sorted(list(set(edge.props)))
            else:
                ends["Props"] = None
            if edge.nanoid:
                ends["NanoID"] = edge.nanoid
            if edge.desc:
                if not mdf_edge.get("Desc"):
                    mdf_edge["Desc"] = edge.desc
                else:
                    ends["Desc"] = edge.desc
            self.add_entity_concept_to_mdf(entity=edge, mdf_entity=mdf_edge)
        prnames = []
        props = {}
        for pr in model.props:
            prname = pr[len(pr) - 1]
            prnames.append(prname)
            # if props.get(prname):
            #    self.logger.warning("Property name collision at {}".format(pr))
            if not prname in props:
                props[prname] = model.props[pr]
        for prname in sorted(prnames):
            prop = props[prname]
            mdf_prop = {}
            mdf["PropDefinitions"][prname] = mdf_prop
            self.add_entity_tags_to_mdf(entity=prop, mdf_entity=mdf_prop)
            if prop.value_domain == "value_set":
                mdf_prop["Enum"] = self.calc_prop_type(prop)
                for t in prop.terms:
                    # if t in mdf["Terms"]:
                    #    self.logger.warning("Term collision at {} (property {})".format(t, prop.handle))
                    if t in mdf["Terms"]:
                        continue
                    pt = prop.terms[t]
                    mdf_pt = {}
                    self.add_entity_concept_to_mdf(entity=pt, mdf_entity=mdf_pt)
                    self.add_entity_tags_to_mdf(entity=pt, mdf_entity=mdf_pt)
                    mdf["Terms"][t] = {
                        **mdf_pt,
                        **{
                            "Value": pt.value,
                            "Definition": pt.origin_definition,
                            "Origin": pt.origin_name,
                            "Code": pt.origin_id,
                            "Handle": pt.handle if pt.handle else pt.value,
                        },
                    }
            else:
                mdf_prop["Type"] = self.calc_prop_type(prop)
            if prop.is_required:
                mdf_prop["Req"] = True
            if prop.nanoid:
                mdf_prop["NanoID"] = prop.nanoid
            if prop.desc:
                mdf_prop["Desc"] = prop.desc
            self.add_entity_concept_to_mdf(entity=prop, mdf_entity=mdf_prop)
        if file:
            fh = file
            if isinstance(file, str):
                fh = open(file, "w")
            yaml.dump(mdf, stream=fh, indent=4)

        return mdf

    def calc_prop_type(self, prop):
        if not prop.value_domain:
            return Property.default("value_domain")
        if prop.value_domain == "regexp":
            if not prop.pattern:
                self.logger.warning(
                    "Property {} has 'regexp' value domain, but no pattern specified".format(
                        prop.handle
                    )
                )
                return {"pattern": "^.*$"}
            else:
                return {"pattern": prop.pattern}
        if prop.units:
            return {"value_type": prop.value_domain, "units": prop.units.split(";")}
        if prop.value_domain == "value_set":
            if not prop.value_set:
                self.logger.warning(
                    "Property {} has 'value_set' value domain, but value_set attribute is None".format(
                        prop.handle
                    )
                )
                return "string"
            values = []
            for trm in sorted(prop.terms):
                values.append(trm)
            return values
        # otherwise
        return prop.value_domain
    def add_entity_concept_to_mdf(self, entity: Entity, mdf_entity: Dict):
        """If entity has concept property, add its terms to MDF"""
        if not entity.concept:
            return
        if not entity.concept.terms:
            self.logger.warning(
                f"{entity.get_label().capitalize} "
                f"'{entity.handle}' has associated concept but with no terms defined"
            )
        else:
            mdf_entity["Term"] = [
                {
                    "Value": tm.value,
                    "Definition": tm.origin_definition,
                    "Origin": tm.origin_name,
                    "Code": tm.origin_id,
                    "Handle": tm.handle if tm.handle else tm.value,
                }
                for tm in entity.concept.terms.values()
            ]
