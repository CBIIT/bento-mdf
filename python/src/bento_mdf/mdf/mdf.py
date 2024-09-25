"""
Load Model Description Format (MDF) files to bento-meta Models.

This module contains :class:`MDF`, a class for reading a graph data model in
Model Description Format into a :class:`bento_meta.model.Model` object.
"""

from __future__ import annotations

import logging
import re
from collections import ChainMap
from pathlib import Path
from tempfile import TemporaryFile

import requests
from bento_meta.entity import ArgError, Entity
from bento_meta.model import Model
from bento_meta.objects import Edge, Node, Property, Term
from nanoid import generate
from tqdm import tqdm

from bento_mdf.mdf.convert import spec_to_entity
from bento_mdf.validator import MDFValidator


def make_nano() -> str:
    """Generate a 6-character alphanumeric string."""
    return generate(
        size=6,
        alphabet="abcdefghijkmnopqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ0123456789",
    )


class MDF:
    """MDF class for reading MDF files into a bento-meta Model."""

    def __init__(
        self,
        *yaml_files: str | Path | list[str | Path],
        handle: str | None = None,
        model: Model | None = None,
        _commit: str | None = None,
        mdf_schema: str | Path | None = None,
        raise_error: bool = False,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Create a :class:`Model` from MDF YAML files/Write a :class:`Model` to YAML.

        :param str|file|url *yaml_files: MDF filenames or file objects,
        in desired merge order
        :param str handle: Handle (name) for the resulting Model
        :param :class:`Model` model: Model to convert to MDF
        :param boolean raise_error: raise on error if True
        :param :class:`logging.Logger` logger: Python logger (suitable default)
        :attribute model: the :class:`bento_meta.model.Model` created
        """
        if model and not isinstance(model, Model):
            msg = "arg model= must be a Model instance"
            raise ArgError(msg)

        self.files = yaml_files
        self.mdf = {}
        self.mdf_schema = mdf_schema
        self._model = model
        self._commit = _commit
        self._annotations = {}
        self._terms = {}
        self._props = {}
        self.version = None
        self.uri = None
        self.logger = logger or logging.getLogger(__name__)
        self.create_model_success = False
        if model:
            self.handle = model.handle
        else:
            self.handle = handle
        if self.files:
            self.load_yaml()
            self.create_model(raise_error=raise_error)
        elif not model:
            self.logger.warning("No MDF files or model provided to constructor")

    @property
    def model(self) -> Model:
        """The :class:`bento_meta.model.Model` object created from the MDF input."""
        if not self._model:
            msg = "Can't fetch model from MDF."
            self.logger.error(msg)
            raise ArgError(msg)
        return self._model

    def load_yaml(self, *, verify: bool = True) -> None:
        """Validate and load YAML files or open file handles specified in constructor."""
        vargs = []
        for f in self.files:
            if isinstance(f, str) and re.match("(?:file|https?)://", f):
                self.load_yaml_vargs_from_url(vargs, f, verify=verify)
            elif isinstance(f, str) and Path(f).exists():
                fh = Path(f).open(encoding="utf-8")
                vargs.append(fh)
            else:  # assume file-like object
                vargs.append(f)

        v = MDFValidator(self.mdf_schema, *vargs, raise_error=True)
        self.mdf_schema = v.load_and_validate_schema()
        self.mdf = v.load_and_validate_yaml()
        if not self.mdf_schema:
            msg = "Error loading & validating MDF schema"
            raise ValueError(msg)
        if not self.mdf:
            msg = "Error loading & validating YAML instance"
            raise ValueError(msg)
        self.mdf = self.mdf.as_dict()

        for fh in vargs:
            if hasattr(fh, "close") and callable(fh.close):
                fh.close()

    def load_yaml_vargs_from_url(
        self,
        vargs: list,
        url: str,
        *,
        verify: bool = True,
    ) -> None:
        """Load YAML from a URL."""
        response = requests.get(url, verify=verify, timeout=10)
        if not response.ok:
            msg = f"Fetching url {response.url} returned code {response.status_code}"
            self.logger.error(msg)
            raise ArgError(msg)
        response.encoding = "utf8"
        fh = TemporaryFile()
        for chunk in response.iter_content(chunk_size=128):
            fh.write(chunk)
        fh.seek(0)
        vargs.append(fh)

    def create_model(self, *, raise_error: bool = False) -> Model:
        """
        Create :class:`Model` instance from loaded YAML.

        Handling enumerated acceptable values ("value sets"):

        If the input MDF does not have a Terms: section, the strings listed under
        an Enum: key are interpreted as literal Term values (i.e., the expected data),
        and the Origin of each Term is set as the model handle (i.e.,the model is itself
        the authority defining the acceptable values)

        However, if the input MDF contains a Terms: section, then each string of an Enum:
        array is first treated as a Term handle, and is used to look up a corresponding Term
        in the the Terms: section. If found, the definition in the Terms: section is used.
        If no referenced Term is found, then the string is treated
        as a literal Term value with the model as origin, as in the previous paragraph.

        :param boolean raiseError: Raise if MDF errors found
        Note: This is brittle, since the syntax of MDF is hard-coded into this method.
        """
        self.create_model_success = True
        if not self.mdf.keys():
            msg = "attribute 'mdf' not set - are yamls loaded?"
            raise ValueError(msg)
        self.version = self.mdf.get("Version")
        self.uri = self.mdf.get("URI")

        if self.handle:
            self._model = Model(handle=self.handle, version=self.version, uri=self.uri)
        elif self.mdf.get("Handle"):
            self.handle = self.mdf["Handle"]
            self._model = Model(
                handle=self.mdf["Handle"],
                version=self.version,
                uri=self.uri,
            )
        else:
            self.logger.error("Model handle not present in MDF nor provided in args")
            self.create_model_success = False

        self.create_terms()  # create terms first, if any -- properties depend on these
        self.create_nodes()
        self.create_edges()
        self.create_props()
        if raise_error and not self.create_model_success:
            msg = "MDF errors found; see log output."
            raise RuntimeError(msg)

        # now add the terms collected in self._terms to the model (self._model)...

        return self.model

    def create_terms(self) -> None:
        """Create terms from loaded YAML."""
        if "Terms" not in self.mdf:
            return
        for t_hdl, spec in tqdm(self.mdf["Terms"].items()):
            if "Value" not in spec:
                self.logger.error(
                    "Term specs must have a Value key and a non-null string value"
                    "(term '%s')",
                    t_hdl,
                )
                self.model_create_success = False
            if "Origin" not in spec:
                self.logger.warning(
                    f"No Origin provided for term '{t_hdl}'",
                )
            term = spec_to_entity(t_hdl, spec, {"_commit": self._commit}, Term)
            self._terms[term.handle] = term

    def create_nodes(self) -> None:
        """Create nodes from loaded YAML."""
        for n, spec in self.mdf["Nodes"].items():
            node = self.model.add_node(
                spec_to_entity(
                    n,
                    spec,
                    {"model": self.handle, "_commit": self._commit},
                    Node,
                ),
            )
            if "Term" in spec:
                self.annotate_entity_from_mdf(node, spec["Term"])

    def create_edges(self) -> None:
        """Create edges from loaded YAML."""
        for e, spec in self.mdf["Relationships"].items():
            for ends in spec["Ends"]:
                for end in [ends["Src"], ends["Dst"]]:
                    if end not in self.model.nodes:
                        self.logger.warning(
                            "No node '%s' defined for edge spec '%s' from '%s' to '%s'",
                            end,
                            e,
                            ends["Src"],
                            ends["Dst"],
                        )
                        continue
                if not spec.get("Mul"):
                    self.logger.warning(
                        "edge '%s' from '%s' to '%s' "
                        "does not specify a multiplicity",
                        e,
                        ends["Src"],
                        ends["Dst"],
                    )
                if spec.get("Mul") not in (
                    "one_to_one",
                    "one_to_many",
                    "many_to_one",
                    "many_to_many",
                ):
                    self.logger.warning(
                        "edge '%s' from '%s' to '%s'"
                        " has non-standard multiplicity '%s'",
                        e,
                        ends["Src"],
                        ends["Dst"],
                        spec.get("Mul"),
                    )
                # if tags are set in the Ends entry, these will be attached
                # to the Edge, _rather than_ tags set in the "edge key" or spec
                # level
                spec["Tags"] = ends.get("Tags") or spec.get("Tags")
                edge = self.model.add_edge(
                    spec_to_entity(
                        e,
                        spec,
                        {
                            "model": self.handle,
                            "_commit": self._commit,
                            "src": self.model.nodes[ends["Src"]],
                            "dst": self.model.nodes[ends["Dst"]],
                            "multiplicity": ends.get("Mul")
                            or spec.get("Mul")
                            or Edge.default("multiplicity"),
                        },
                        Edge,
                    ),
                )
                term = ends.get("Term") or spec.get("Term")
                if term:
                    self.annotate_entity_from_mdf(edge, term)

    def create_props(self) -> None:
        """Create properties from loaded YAML."""
        yunps = self.mdf.get("UniversalNodeProperties")
        yurps = self.mdf.get("UniversalRelationshipProperties")

        propnames = {}
        for ent in ChainMap(self.model.nodes, self.model.edges).values():
            if isinstance(ent, Node):
                pnames = self.mdf["Nodes"][ent.handle]["Props"] or []
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
                    for e in self.mdf["Relationships"][hdl]["Ends"]
                    if e["Src"] == src and e["Dst"] == dst
                ]
                if len(ends) > 1:
                    self.logger.warning(
                        "edge '%s' has more than one Ends pair Src:'%s',Dst:'%s'",
                        hdl,
                        src,
                        dst,
                    )
                end = ends[0]

                # note the end-specified props _replace_ the edge-specified props,
                # they are not merged:
                pnames = (
                    end.get("Props")
                    or self.mdf["Relationships"][hdl].get("Props")
                    or []
                )
                if yurps:  # universal relationship props
                    pnames.extend(yurps["mayHave"] if yurps.get("mayHave") else [])
                    pnames.extend(yurps["mustHave"] if yurps.get("mustHave") else [])
                if pnames:
                    propnames[ent] = pnames
            else:
                self.logger.error(
                    "Unhandled entity type %s for properties",
                    type(ent).__name__,
                )
                self.create_model_success = False
        prop_of = {}
        for ent in propnames:
            for p in propnames[ent]:
                if prop_of.get(p):
                    prop_of[p].append(ent)
                else:
                    prop_of[p] = [ent]
        propdefs = self.mdf["PropDefinitions"]
        defns_for = set(propdefs.keys())
        for pname in prop_of:
            for ent in prop_of[pname]:
                force = False
                # see if a qualified name is defined in propdefs:
                key = ent.handle + "." + pname
                spec = propdefs.get(key)
                if spec:
                    # force creation of new prop for a explicitly qualified MDF property
                    force = True
                else:
                    key = pname
                    spec = propdefs.get(pname)
                if not spec:
                    self.logger.warning(
                        "property '%s' does not have a corresponding "
                        "propdef for entity '%s'",
                        pname,
                        ent.handle,
                    )
                    continue
                if key in defns_for:
                    defns_for.remove(key)
                prop = self.create_or_merge_prop_from_mdf(
                    spec,
                    p_hdl=pname,
                    force_create=force,
                )
                self.model.add_prop(ent, prop)
                ent.props[prop.handle] = prop
        if defns_for:
            self.logger.warning(
                "No properties in model corresponding to the following "
                "PropDefintions: %s",
                defns_for,
            )

    def create_or_merge_prop_from_mdf(
        self,
        spec: dict,
        p_hdl: str,
        *,
        force_create: bool,
    ) -> Property:
        if not force_create and (self.handle, p_hdl) in self._props:
            pass
        else:
            prop = spec_to_entity(
                p_hdl,
                spec,
                {"handle": p_hdl, "model": self.handle, "_commit": self._commit},
                Property,
            )
            if prop.value_set and prop.value_set._commit == "dummy":
                terms = []
                # merge terms references in enums into terms defined
                # in a separate Terms: section
                for t in prop.value_set.terms:
                    if self._terms.get(t):
                        terms.append(self._terms[t])
                    else:
                        terms.append(prop.value_set.terms[t])
                # allow bento_meta.model machinery to create
                # the actual value_set object and store
                # terms in Model object:
                if prop.value_domain == "list" and prop.item_domain == "value_set":
                    # kludge so Model.add_terms works with list type props with val sets
                    prop.value_domain = "value_set"
                    self.model.add_terms(prop, *terms)
                    prop.value_domain = "list"
                else:
                    self.model.add_terms(prop, *terms)

            if "Term" in spec:
                self.annotate_entity_from_mdf(prop, spec["Term"])
            if force_create:
                return prop
            self._props[(prop.model, prop.handle)] = prop
        return self._props[(self.handle, p_hdl)]

    def annotate_entity_from_mdf(self, ent: Entity, yterm_list: list) -> None:
        """Annotate an entity from a list of term references in MDF."""
        for spec in yterm_list:
            if "Value" not in spec:
                self.logger.error(
                    "Term specs must have a Value key and a non-null string value, "
                    "in entity '%s'",
                    ent.handle,
                )
                return
            if "Origin" not in spec:
                self.logger.warning(
                    "No Origin provided for Term annotation in entity '%s'",
                    ent.handle,
                )
                spec["Origin"] = self.handle
            term = spec_to_entity(None, spec, {"_commit": self._commit}, Term)
            # merge or record term
            if not self._annotations.get((term.handle, term.origin_name)):
                self._annotations[(term.handle, term.origin_name)] = term
            else:
                term = self._annotations[(term.handle, term.origin_name)]

            self.model.annotate(ent, term)
            if self._commit and not ent.concept._commit:
                ent.concept._commit = self._commit
