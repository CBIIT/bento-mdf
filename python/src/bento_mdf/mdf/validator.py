from __future__ import annotations
import re
import importlib.util
import sys
from .reader import MDFReader
from tempfile import NamedTemporaryFile
from jinja2 import Environment, PackageLoader
from typing import Any, Dict, List, Literal, Optional, Annotated, TYPE_CHECKING
from annotated_types import Predicate
from datetime import datetime
from enum import Enum, IntEnum
from pydantic import BaseModel, Field, TypeAdapter
from pdb import set_trace

# custom validator for regex-checked strings:
# use a custom Annotated type with Predicate, res

# want to dynamically create a pydantic model Class that can validate data that
# is submitted under the conditions laid out in the MDF for Properties
# Reasonable structure is: one (sub)Class per defined Node, with classname equal to node name
# (possibly camel-cased)
# The subClass would contain named typed attributes, with names derived from the Properties
# defined for the Node. Types of attribute values are derived from MDF PropDefinitions.
#

  # treatment:
  #   Props:
  #     - treatment_id
  #     - age_at_treatment_start
  #     - age_at_treatment_end
  #     - treatment_type
  #     - treatment_agent
  #     - id

# class TreatmentTypeEnum(str, Enum):
#     <snakecase_normalized_values> = <values>

# class TreatmentAgentEnum(str, Enum):
#     <snakecase_normalized_values> = <values>
    
# class Treatment(BaseModel):
#     treatment_id: str
#     age_at_treatment_start: int
#     age_at_treatment_end: int
#     treatment_type: TreatmentTypeEnum
#     treatment_agent: TreatmentAgentEnum
#     id: str

jenv = Environment(
    loader=PackageLoader("bento_mdf", package_path="mdf/templates"),
    trim_blocks=True,
)


def toCamelCase(val):
    return "".join([x.capitalize() for x in val.split("_")])


def to_snakecase(val):
    return re.sub("\W", "_", val).lower()


def to_unit_types(unitstr : str, typ : type(int) | type(float)) -> List[str]:
    return [f"Annotated[{typ.__name__}, Unit('{u}')]" for u in unitstr.split(';')]


def maybe_optional(val, prop):
    if prop.is_required:
        return val
    else:
        return f"Optional[{val}]"

    
jenv.filters['toCamelCase'] = toCamelCase
jenv.filters['to_snakecase'] = to_snakecase
jenv.filters['to_unit_types'] = to_unit_types
jenv.filters['maybe_optional'] = maybe_optional


class MDFDataValidator:
    typemap = {
        "boolean": bool,
        "datetime": datetime,
        "integer": int,
        "number": float,
        "string": str,
        "regexp": str,
        "url": str,
        "TBD": None,
        }

    def __init__(self, mdf: MDFReader):
        self.model = mdf.model
        self._pymodel = None
        self._module = None
        self._node_classes = []
        self._enum_classes = []
        self.generate_data_model()
        self.import_data_model()

    @property
    def data_model(self):
        return self._pymodel or None

    @property
    def data_module(self):
        return self._module or None

    @property
    def module_name(self):
        return self.data_module and self.data_module.__name__

    @property
    def node_classes(self):
        return self._node_classes

    @property
    def enum_classes(self):
        return self._enum_classes
    
    def generate_data_model(self):
        """
        Generates Pydantic classes for each node in the MDF model.
        """
        # write down classes to be generated
        for node in self.model.nodes.values():
            self._node_classes.append(toCamelCase(node.handle))
            for pr in node.props.values():
                if pr.value_domain == 'value_set':
                    self._enum_classes.append("{}Enum".format(toCamelCase(pr.handle)))
        self._node_classes.sort()
        self._enum_classes.sort()
        template = jenv.get_template("pymodel.py.jinja2")
        self._pymodel = template.render(model=self.model, typemap=self.typemap)
        pass

    def import_data_model(self):
        """
        Imports model classes as a module '<model handle>Data'
        :returns: module object
        """
        if not self.data_model:
            return
        with NamedTemporaryFile(mode="w+", suffix=".py", delete_on_close=False) as modf:
            modname = "{}Data".format(self.model.handle)
            print(self.data_model, file=modf)
            modf.close()
            spec = importlib.util.spec_from_file_location(modname, modf.name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[modname] = module
            spec.loader.exec_module(module)
            self._module = module

    def adapter(self, clsname):
        cls = eval("self.data_module.{}".format(clsname))
        return TypeAdapter(cls)
