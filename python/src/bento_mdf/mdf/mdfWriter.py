import logging
import yaml
from bento_meta.entity import ArgError, Entity
from bento_meta.model import Model
from bento_meta.objects import Edge, Node, Property, Term
from .convert import entity_to_spec

class MDFWriter(object):
    def __init__(self, model=None):
        self.mdf = {
            "Nodes": {},
            "Relationships": {},
            "PropDefinitions": {},
            "Terms": {},
            "Handle": None,
            "Version": None,
            "URI": None,
        }
        self.logger = logging.getLogger(__name__)
        self.model = model
        if model:
            self.write_mdf()
        pass
    
    def write_mdf(self, file=None):
        """
        Use a :class:`Model` to create model description file (MDF) formatted dict
        :param :class:`Model` model: Model to convert 
        :param str|file file: File name or object to write to (default is None; just return the MDF as dict)
        :returns: MDF as dict
        """
        self.mdf["Handle"] = self.model.handle or "NEED_MODEL_HANDLE"
        self.mdf["Version"] = self.model.version or "NEED_MODEL_VERSION"
        if self.model.uri:
            self.mdf["URI"] = self.model.uri

        for nd in sorted(self.model.nodes):
            node = self.model.nodes[nd]
            self.mdf["Nodes"][nd] = entity_to_spec(node)

        for pr in sorted(self.model.props):
            prop = self.model.props[pr]
            self.mdf["PropDefinitions"][pr] = entity_to_spec(prop)

        # note that the former possibility of src-dst pair-specific properties is
        # removed for now - this is not currently (at commit 9ead2e3) specified
        # in the mdf schema

        for rl in sorted(self.model.edges):
            edge = self.model.edges[rl]
            spec = entity_to_spec(edge)
            if edge.handle not in self.mdf["Relationships"]:
                if not spec.get("Mul"):
                    spec["Mul"] = Edge.default("multiplicity")
                self.mdf["Relationships"][edge.handle] = spec
            else:
                mdf_edge = self.mdf["Relationships"][edge.handle]
                ends = spec["Ends"]
                if spec.get("Mul") and spec["Mul"] != mdf_edge["Mul"]:
                    ends["Mul"] = spec["Mul"]
                if spec.get("Tags"):
                    ends["Tags"] = spec["Tags"]
                mdf_edge["Ends"].append(ends)

        # collect Terms?

        if file:
            fh = file
            if isinstance(file, str):
                fh = open(file, "w")
            yaml.dump(self.mdf, stream=fh, indent=4)

        return self.mdf


