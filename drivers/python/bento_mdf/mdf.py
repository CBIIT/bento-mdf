"""
bento_mdf.mdf
==============

This module contains :class:`MDF`, a class for reading a graph data model in
Model Description Format into a :class:`bento_meta.model.Model` object, and 
writing the opposite way.

"""
import sys
import yaml
import logging
from tqdm import tqdm
from urllib.parse import unquote
from tempfile import TemporaryFile
from bento_mdf.validator import MDFValidator
from bento_meta.model import Model
from bento_meta.entity import ArgError, CollValue
from bento_meta.objects import (
    Node,
    Edge,
    Property,
    Term,
    ValueSet,
    Tag,
    Origin,
)
import re
import requests
from collections import ChainMap
from nanoid import generate
import json

from pdb import set_trace

sys.path.extend([".", ".."])

def make_nano():
    return generate(
        size=6,
        alphabet="abcdefghijkmnopqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ0123456789"
    )

class MDF(object):
    def __init__(self, *yaml_files, handle=None, model=None, _commit=None,
                 raiseError=False, logger=logging.getLogger(__name__)):
        """Create a :class:`Model` from MDF YAML files/Write a :class:`Model` to YAML
        :param str|file|url *yaml_files: MDF filenames or file objects, 
        in desired merge order
        :param str handle: Handle (name) for the resulting Model
        :param :class:`Model` model: Model to convert to MDF
        :param boolean raiseError: raise on error if True
        :param :class:`logging.Logger` logger: Python logger (suitable default)
        :attribute model: the :class:`bento_meta.model.Model` created"""
        if not model and (not handle or not isinstance(handle, str)):
            raise ArgError("arg handle= must be a str - name for model")
        if model and not isinstance(model,Model):
            raise ArgError("arg model= must be a Model instance")
            
        self.files = yaml_files
        self.schema = {}
        self._model = model
        self._commit = _commit
        self._terms = {}
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
                            ))
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
                
        v = MDFValidator(None, *vargs, raiseError=True)
        self.schema = v.load_and_validate_yaml()

    def create_model(self, raiseError=False):
        """Create :class:`Model` instance from loaded YAML
        :param boolean raiseError: Raise if MDF errors found
        Note: This is brittle, since the syntax of MDF is hard-coded
        into this method."""
        success=True
        if not self.schema.keys():
            raise ValueError("attribute 'schema' not set - are yamls loaded?")
        if (self.handle):
            self._model = Model(handle=self.handle)
        elif (self.schema.get("Handle")):
            self.handle = self.schema["Handle"]
            self._model = Model(handle=self.schema["Handle"])
        else:
            self.logger.error("Model handle not present in MDF nor provided in args")
            success = False
            
        ynodes = self.schema["Nodes"]
        yedges = self.schema["Relationships"]
        ypropdefs = self.schema["PropDefinitions"]
        yunps = self.schema.get("UniversalNodeProperties")
        yurps = self.schema.get("UniversalRelationshipProperties")
        yterms = self.schema.get("Terms")
        if yterms:
            yterms = yterms.as_dict()

        # create terms first, if any -- properties depend on these
        if yterms:
            for t_hdl in tqdm(yterms):
                ytm = yterms[t_hdl]
                tm = self.create_term_from_mdf(ytm, t_hdl)
                if not tm:
                    success = False
                else:
                    self._terms[t_hdl] = tm
                    self._terms[tm.value] = tm
        
        # create nodes
        for n in ynodes:
            yn = ynodes[n]
            init = {"handle": n, "model": self.handle, "_commit": self._commit}
            if 'Desc' in yn and yn['Desc']:
                init['desc'] = yn['Desc']
            if 'NanoID' in yn and yn['NanoID']:
                init['nanoid'] = yn['NanoID']
            node = self._model.add_node(init)
            if "Tags" in yn:
                for t in yn["Tags"]:
                    node.tags[t] = Tag({"key": t,
                                        "value": yn["Tags"][t],
                                        "_commit": self._commit})
            if "Term" in yn:
                if not self.annotate_entity_from_mdf(node, yn["Term"]):
                    success = False
                
        # create edges (relationships)
        for e in yedges:
            ye = yedges[e]
            for ends in ye["Ends"]:
                if ends["Src"] not in self._model.nodes:
                    self.logger.warning(
                        "No node '{src}' defined for edge "
                        "spec '{ename}' from '{src}' to '{dst}'"
                        .format(src=ends["Src"], dst=ends["Dst"],
                                ename=e)
                        )
                    continue
                if ends["Dst"] not in self._model.nodes:
                    self.logger.warning(
                        "No node '{dst}' defined for edge "
                        "spec '{ename}' from '{src}' to '{dst}'"
                        .format(src=ends["Src"], dst=ends["Dst"],
                                ename=e)
                        )
                    continue
                init = {
                    "handle": e,
                    "model": self.handle,
                    "src": self._model.nodes[ends["Src"]],
                    "dst": self._model.nodes[ends["Dst"]],
                    "multiplicity": ends.get("Mul")
                    or ye.get("Mul"),
                    "desc": ends.get("Desc") or ye.get("Desc"),
                    "_commit": self._commit
                }
                if not init["multiplicity"]:
                    self.logger.warning("edge '{ename}' from '{src}' to '{dst}' "
                                        "does not specify a multiplicity".
                                        format(ename=e, src=ends["Src"],
                                               dst=ends["Dst"]))
                    init["multiplicity"] = Edge.default("multiplicity")
                if init["multiplicity"] not in ('many_to_many', 'many_to_one',
                                                'one_to_many', 'one_to_one'):
                    self.logger.warning("edge '{ename}' from '{src}' to '{dst}'"
                                        " has non-standard multiplicity '{mult}'".
                                        format(ename=e, src=ends["Src"],
                                               dst=ends["Dst"], mult=init["multiplicity"]
                                   )
                    )
                edge = self._model.add_edge(init)
                Tags = ye.get("Tags") or ends.get("Tags")
                if Tags:
                    # tags = CollValue({}, owner=edge, owner_key="tags")
                    for t in Tags:
                        edge.tags[t] = Tag({"key": t,
                                            "value": Tags[t],
                                            "_commit": self._commit})
                yterm = ends.get("Term") or ye.get("Term")
                if yterm:
                    if not self.annotate_entity_from_mdf(edge, yterm):
                        success = False

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
                    self.logger.warning("edge '{ename}' has more than one Ends pair Src:'{src}',"
                                        "Dst:'{dst}'".format(ename=hdl, src=src, dst=dst))
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
                key = ent.handle+"."+pname
                ypdef = ypropdefs.get(key)
                if not ypdef:
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
                init = {"handle": pname,
                        "model": self.handle,
                        "_commit": self._commit}
                if 'Desc' in ypdef and ypdef['Desc']:
                    init['desc'] = ypdef['Desc']
                if 'NanoID' in ypdef and ypdef['NanoID']:
                    init['nanoid'] = ypdef['NanoID']
                if 'Type' in ypdef:
                    init.update(self.calc_value_domain(ypdef["Type"], pname))
                elif 'Enum' in ypdef:
                    init.update(self.calc_value_domain(ypdef["Enum"], pname))
                else:
                    self.logger.warning(
                        "property '{pname}' on entity '{handle}' does not "
                        "specify a data type".format(pname=pname,
                                                     handle=ent.handle)
                    )
                    init["value_domain"] = Property.default("value_domain")
                prop = self._model.add_prop(ent, init)
                ent.props[prop.handle] = prop
                if "Tags" in ypdef:
                    for t in ypdef["Tags"]:
                        prop.tags[t] = Tag({"key": t,
                                            "value": ypdef["Tags"][t],
                                            "_commit": self._commit})
                if "Term" in ypdef:
                    if not self.annotate_entity_from_mdf(prop, ypdef["Term"]):
                        success = False

        if defns_for:
            self.logger.warning(
                "No properties in model corresponding to the following "
                "PropDefintions: {}".format(defns_for))
        if raiseError and not success:
            raise RuntimeError("MDF errors found; see log output.")
        return self._model

    def create_term_from_mdf(self, ytm, t_hdl=None):
        if not "Value" in ytm:
            self.logger.error(
                "Term specs must have a Value key and a non-null string value"
            )
            return False
        tm = {}
        tm["_commit"] = self._commit
        if 'Origin' in ytm:
            tm["origin_name"] = ytm["Origin"]
        else:
            self.logger.warning(
                "No Origin provided for term '{term}'".format(term=t_hdl)
            )
            tm["origin_name"] = self.handle
        tm["value"] = ytm["Value"]
        if 'Definition' in ytm and ytm['Definition']:
            tm["origin_definition"] = unquote(ytm["Definition"])
        if 'Code' in ytm:
            tm["origin_id"] = ytm["Code"]
        if 'Version' in ytm:
            tm["origin_version"] = ytm["Version"]
        if 'Handle' in ytm:
            tm["handle"] = ytm["Handle"]
        if 'NanoID' in ytm:
            tm["nanoid"] = ytm["NanoID"]
        return Term(tm)

    def annotate_entity_from_mdf(self, ent, yterm_list):
        success = True
        for yterm in yterm_list:
            tm = self.create_term_from_mdf(yterm)
            if not tm:
                success = False
            else:
                self._model.annotate(ent, tm)
                self._terms[yterm.get("Handle") or yterm["Value"] ] = tm
                self._terms[tm.value] = tm
        return success
        

    def calc_value_domain(self, typedef, pname=None):
        if isinstance(typedef, dict):
            if typedef.get("pattern"):
                return {"value_domain": "regexp",
                        "pattern": typedef["pattern"]}
            elif typedef.get("units"):
                return {
                    "value_domain": typedef.get("value_type"),
                    "units": ";".join(typedef.get("units")),
                }
            elif typedef.get("item_type"):
                if (typedef["value_type"] == 'list'):
                    i_domain = self.calc_value_domain(typedef["item_type"])
                    ret = {"value_domain": "list",
                           "item_domain": i_domain["value_domain"]}
                    if i_domain.get("pattern"):
                        ret["pattern"] = i_domain["pattern"]
                    if i_domain.get("units"):
                        ret["units"] = i_domain["units"]
                    if i_domain.get("value_set"):
                        ret["value_set"] = i_domain["value_set"]
                    return ret
                else:
                    self.logger.warning(
                        "MDF type descriptor defines item_type, but value_type"
                        " is {}, not 'list' (property '{}')".format(typedef["value_type"],pname))
            elif not typedef:
                self.logger.warning("MDF type descriptor is null for property '{}'".format(pname))
            else:
                # punt
                self.logger.warning(
                    "MDF type descriptor unrecognized: json looks like {} (property '{}')".
                    format(json.dumps(typedef),pname)
                    )
                return {"value_domain": json.dumps(typedef)}
        elif isinstance(typedef, list):  # a valueset: create value set and term objs
            vs = ValueSet({"nanoid": make_nano(), "_commit": self._commit})
            vs.handle = self.handle + vs.nanoid
            # interpret boolean values as strings
            if (isinstance(typedef[0], str) and
                re.match("^(?:https?|bolt)://", typedef[0])):  # looks like url
                vs.url = typedef[0]
            else:  # an enum
                for t in typedef:
                    if isinstance(t, bool):  # stringify booleans in term context
                        t = "True" if t else "False"
                    if t not in self._terms:
                        self._terms[t] = Term({
                            "value": t,
                            "origin_name": self.handle,
                            "_commit": self._commit
                        })
                    vs.terms[self._terms[t].value] = self._terms[t]
            return {"value_domain": "value_set", "value_set": vs}
        elif isinstance(typedef, str):
            return {"value_domain": typedef}
        else:
            self.logger.warning("Applying default value domain to property '{}'".format(pname))
            return {"value_domain": Property.default("value_domain")}

    def write_mdf(self, model=None, file=None):
        """Write a :class:`Model` to a model description file (MDF)
        :param :class:`Model` model: Model to convert (if None, use the model attribute of the MDF object)
        :param str|file file: File name or object to write to (default is None; just return the MDF as dict)
        :returns: MDF as dict"""
        if not model:
            model = self.model
        mdf = {"Nodes":{},
               "Relationships":{},
               "PropDefinitions":{},
               "Terms":{},
               "Handle":model.handle}
        for nd in sorted(model.nodes):
            node = model.nodes[nd]
            mdf_node = {}
            mdf["Nodes"][nd] = mdf_node
            if node.tags:
                mdf_node["Tags"] = {}
                for t in node.tags:
                    mdf_node["Tags"][t] = node.tags[t].value
            if node.concept:
                if not node.concept.terms:
                    self.logger.warning("Node '{}' has associated concept but with no terms defined".format(node.handle))
                else:
                    mdf_node["Term"] = [{
                        "Value": tm.value,
                        "Definition": tm.origin_definition,
                        "Origin": tm.origin,
                        "Code": tm.origin_id,
                        } for tm in node.concept.terms.values()]

            mdf_node["Props"] = [prop for prop in sorted(node.props)]

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
            ends = {"Src": edge.src.handle,
                    "Dst": edge.dst.handle}
            if "Ends" in mdf_edge:
                mdf_edge["Ends"].append(ends)
            else:
                mdf_edge["Ends"] = [ends]
            if not "Mul" in mdf_edge:
                mdf_edge["Mul"] = edge.multiplicity or Edge.default("multiplicity")
            else:
                if mdf_edge["Mul"] != edge.multiplicity:
                    ends["Mul"] = edge.multiplicity
            if edge.tags:
                mdf_edge["Tags"] = {}
                for t in edge.tags:
                    mdf_edge["Tags"][t] = edge.tags[t].value
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
            if edge.concept:
                if not edge.concept.terms:
                    self.logger.warning("Edge '{}' has associated concept but with no terms defined".format(node.handle))
                else:
                    mdf_edge["Term"] = [
                        {
                            "Value": tm.value,
                            "Definition": tm.origin_definition,
                            "Origin": tm.origin,
                            "Code": tm.origin_id,
                        } for tm in edge.concept.terms.values()]
        prnames = []
        props = {}
        for pr in model.props:
            prname = pr[len(pr)-1]
            prnames.append(prname)
            # if props.get(prname):
            #    self.logger.warning("Property name collision at {}".format(pr))
            if not prname in props:
                props[prname] = model.props[pr]
        for prname in sorted(prnames):
            prop = props[prname]
            mdf_prop = {}
            mdf["PropDefinitions"][prname] = mdf_prop
            if prop.tags:
                mdf_prop["Tags"] = {}
                for t in prop.tags:
                    mdf_prop["Tags"][t] = prop.tags[t].value
            if prop.value_domain == "value_set":
                mdf_prop["Enum"] = self.calc_prop_type(prop)
                for t in prop.terms:
                    # if t in mdf["Terms"]:
                    #    self.logger.warning("Term collision at {} (property {})".format(t, prop.handle))
                    if not t in mdf["Terms"]:
                        mdf["Terms"][t] = {
                            "Value": prop.terms[t].value,
                            "Definition": prop.terms[t].origin_definition,
                            "Origin": prop.terms[t].origin,
                            "Code": prop.terms[t].origin_id,
                        }
            else:
                mdf_prop["Type"] = self.calc_prop_type(prop)
            if prop.is_required:
                mdf_prop["Req"] = True
            if prop.nanoid:
                mdf_prop["NanoID"] = prop.nanoid
            if prop.desc:
                mdf_prop["Desc"] = prop.desc
            if prop.concept:
                if not prop.concept.terms:
                    self.logger.warning("Property '{}' has associated concept but with no terms defined".format(node.handle))
                else:
                    mdf_prop["Term"] = [{
                        "Value": tm.value,
                        "Definition": tm.origin_definition,
                        "Origin": tm.origin,
                        "Code": tm.origin_id,
                    } for tm in prop.concept.terms.values()]
        if file:
            fh = file
            if isinstance(file,str):
                fh = open(file, "w")
            yaml.dump(mdf, stream=fh, indent=4)
            
        return mdf

    def calc_prop_type(self,prop):
        if not prop.value_domain:
            return Property.default("value_domain")
        if prop.value_domain == "regexp":
            if not prop.pattern:
                self.logger.warning("Property {} has 'regexp' value domain, but no pattern specified".format(prop.handle))
                return {"pattern":"^.*$"}
            else:
                return {"pattern":prop.pattern}
        if prop.units:
            return {"value_type":prop.value_domain, "units":prop.units.split(';')}
        if prop.value_domain == "value_set":
            if not prop.value_set:
                self.logger.warning("Property {} has 'value_set' value domain, but value_set attribute is None".format(prop.handle))
                return "string"
            values = []
            for trm in sorted(prop.terms):
                values.append(trm)
            return values
        # otherwise 
        return prop.value_domain
