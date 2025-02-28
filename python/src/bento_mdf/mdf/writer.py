import logging
import yaml
from collections import Counter
from functools import reduce
from typing import TYPE_CHECKING
from bento_meta.entity import ArgError, Entity
from bento_meta.model import Model
from .reader import MDFReader
from bento_meta.objects import Edge, Node, Property, Term
from .convert import entity_to_spec
from pdb import set_trace


class MDFWriter(object):
    def __init__(self, model : MDFReader | Model = None):
        self._mdf = {
            "Nodes": {},
            "Relationships": {},
            "PropDefinitions": {},
            "Terms": {},
            "Handle": None,
            "Version": None,
            "URI": None,
        }
        self.logger = logging.getLogger(__name__)
        if isinstance(model, Model):
            self.model = model
        elif isinstance(model, MDFReader):
            self.model = model.model
        else:
            self.logger.error("MDFWriter arg1 must be Model or MDFReader")
            raise RuntimeError("MDFWriter arg1 must be Model or MDFReader")
    
    @property
    def mdf(self):
        if not self._mdf['Handle']:
            self.write_mdf()
        return self._mdf
    
    def write_mdf(self, file=None):
        """
        Use a :class:`Model` to create model description file (MDF) formatted dict
        :param :class:`Model` model: Model to convert 
        :param str|file file: File name or object to write to (default is None; just return the MDF as dict)
        :returns: MDF as dict
        """
        self._mdf["Handle"] = self.model.handle or "NEED_MODEL_HANDLE"
        self._mdf["Version"] = self.model.version or "NEED_MODEL_VERSION"
        if self.model.uri:
            self._mdf["URI"] = self.model.uri
        else:
            del self._mdf["URI"]

        for nd in sorted(self.model.nodes):
            node = self.model.nodes[nd]
            self._mdf["Nodes"][nd] = entity_to_spec(node)

        for pr in sorted(self.model.props):
            prop = self.model.props[pr]
            self._mdf["PropDefinitions"][prop.handle] = entity_to_spec(prop)

        edge_specs = {}
        for rl in self.model.edges.values():
            if rl.handle in edge_specs:
                edge_specs[rl.handle].append(entity_to_spec(rl))
            else:
                edge_specs[rl.handle] = [entity_to_spec(rl)]

        for hdl in edge_specs:
            top = {}
            # determine default Mul 
            muls = Counter([x.get("Mul") for x in edge_specs[hdl]])
            dfMul = muls.most_common(1)[0][0]
            top["Mul"] = dfMul or Edge.default("multiplicity")
            # raise common Desc
            top["Desc"] = None
            descs = Counter([x.get("Desc") for x in edge_specs[hdl] if x.get("Desc")])
            if descs.total() == len(edge_specs[hdl]):
                dfDesc = descs.most_common(1)[0][0]
                top["Desc"] = dfDesc
            if not top["Desc"]:
                del top["Desc"]
            # merge props - this logic raises all Props specified in
            # Ends members to the Relationship[<handle>] level
            # (MDF schema does not currently allow Props to be specified
            #  at the End level)
            propsets = [set(x.get("Props")) for x in edge_specs[hdl] if x.get("Props")]
            if not any([len(s) > 0 for s in propsets]):
                top["Props"] = None
            else:
                mrgd = list(reduce(lambda x, y: x | y, propsets))
                top["Props"] = mrgd
            top["Ends"] = []
            for spec in edge_specs[hdl]:
                if spec.get("Mul") and spec.get("Mul") == top.get("Mul"):
                    del spec["Mul"]
                if spec.get("Desc") and top.get("Desc"):
                    if spec["Desc"] == top["Desc"]:
                        del spec["Desc"]
                if spec.get("Props"):
                    del spec["Props"]
                top["Ends"].append(spec)
            self._mdf["Relationships"][hdl] = top

        # collect Terms?
        for tm in sorted(self.model.terms):
            term = self.model.terms[tm]
            self._mdf["Terms"][term.handle] = entity_to_spec(term)
        
        if file:
            fh = file
            if isinstance(file, str):
                fh = open(file, "w")
            yaml.dump(self._mdf, stream=fh, indent=4)

        return self._mdf


