from __future__ import annotations
import re
import sys
import importlib.util
from functools import cache
from pathlib import Path
from .reader import MDFReader
from bento_meta.objects import Property
from tempfile import NamedTemporaryFile
from jinja2 import Environment, PackageLoader
from typing import Any, List, NoReturn #, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, TypeAdapter, ValidationError, AnyUrl
from pydantic.json_schema import GenerateJsonSchema
from pdb import set_trace

jenv = Environment(
    loader=PackageLoader("bento_mdf", package_path="mdf/templates"),
    trim_blocks=True,
)

# jinja helpers    

def toCamelCase(val : str) -> str:
    return "".join([x.capitalize() for x in val.split("_")])


def to_snakecase(val : str) -> str:
    return re.sub("\\W", "_", val).lower()


def to_unit_types(unitstr : str, typ : type(int) | type(float)) -> List[str]:
    return [f"Annotated[{typ.__name__}, Unit('{u}')]" for u in unitstr.split(';')]


def maybe_optional(val : str, prop : Property):
    if prop.is_required:
        return val
    else:
        return f"Optional[{val}]"

def maybe_list(val : str, prop : PropertyO):
    if prop.value_domain == "list":
        return f"List[{val}]"
    else:
        return val


jenv.filters['toCamelCase'] = toCamelCase
jenv.filters['to_snakecase'] = to_snakecase
jenv.filters['to_unit_types'] = to_unit_types
jenv.filters['maybe_optional'] = maybe_optional
jenv.filters['maybe_list'] = maybe_list

class GenerateQualJsonSchema(GenerateJsonSchema):
    # override to add $schema tag
    def generate(self, schema, mode='validation'):
        json_schema = super().generate(schema, mode=mode)
        json_schema['$schema'] = self.schema_dialect
        return self.sort(json_schema)


class MDFDataValidator:
    typemap = {
        "boolean": bool,
        "datetime": datetime,
        "integer": int,
        "number": float,
        "string": str,
        "regexp": str,
        "url": AnyUrl,
        "TBD": Any,
        }

    def __init__(self, mdf: MDFReader):
        self.model = mdf.model
        self._pymodel = None
        self._module = None
        self._node_classes = []
        self._enum_classes = []
        self._validation_errors = None
        self.generate_data_model()
        self.import_data_model()
        
    @property
    def data_model(self) -> str:
        return self._pymodel

    @property
    def module(self):
        return self._module

    @property
    def model_class(self) -> str:
        return self.module and self.module.__name__

    @property
    def node_classes(self) -> List:
        return self._node_classes

    @property
    def enum_classes(self) -> List:
        return self._enum_classes

    @property
    def last_validation_errors(self) -> dict | None:
        return self._validation_errors
    
    def generate_data_model(self) -> NoReturn:
        """
        Generates Pydantic classes for each node in the MDF model.
        """
        # write down classes to be generated
        for node in self.model.nodes.values():
            self._node_classes.append(toCamelCase(node.handle))
            for pr in node.props.values():
                if pr.value_domain == 'value_set' or pr.item_domain == 'value_set':
                    if pr.value_set.url:
                        self._enum_classes.append("{}EnumURL".format(toCamelCase(pr.handle)))
                    elif pr.value_set.path:
                        self._enum_classes.append("{}EnumPath".format(toCamelCase(pr.handle)))
                    else:
                        self._enum_classes.append("{}Enum".format(toCamelCase(pr.handle)))
        self._node_classes.sort()
        self._enum_classes.sort()
        template = jenv.get_template("pymodel.py.jinja2")
        self._pymodel = template.render(model=self.model, typemap=self.typemap)

    def import_data_model(self) -> NoReturn:
        """
        Imports model classes as a module '<model handle>Data'
        :returns: module object
        """
        if not self.data_model:
            return
        with NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as modf:
            modname = "{}Data".format(self.model.handle)
            print(self.data_model, file=modf)
            modf.close()
            spec = importlib.util.spec_from_file_location(modname, modf.name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[modname] = module
            spec.loader.exec_module(module)
            self._module = module
            Path(modf.name).unlink()

    @cache
    def model_of(self, clsname : str):
        if clsname != self.model_class and clsname not in self.node_classes and clsname not in self.enum_classes:
            raise RuntimeError(f"Validation model does not contain class '{clsname}'")
        return eval("self.module.{}".format(clsname))

    @cache
    def fields_of(self, clsname : str) -> List[str]:
        if clsname != self.model_class and clsname not in self.node_classes:
            raise RuntimeError(f"Validation model does not contain node class '{clsname}'")
        return [x for x in self.model_of(clsname).model_fields]

    def props_of(self, clsname : str) -> List[str]:
        return self.fields_of(clsname)
    
    @cache
    def validator(self, clsname : str):
        """
        Return a validator function appropriate to the class named 'clsname'
        """
        model = self.model_of(clsname)
        if issubclass(model, BaseModel):
            return model.model_validate
        else:
            return TypeAdapter(model).validate_python
        
    def json_schema(self, clsname : str) -> dict | list:
        """
        Return a jsonable object representing a JSONSchema that can validate
        the given model class.
        """

        model = self.model_of(clsname)
        if issubclass(model, BaseModel):
            return model.model_json_schema(
                schema_generator=GenerateQualJsonSchema)
        else:
            return TypeAdapter(model).json_schema(
                schema_generator=GenerateQualJsonSchema)
        
    def validate(self, clsname : str, data : dict | List[dict], strict : bool = False,
                 verbose : bool = False) -> bool:
        """
        Validate a dict or list of dicts against a given model class.
        Returns true if all items are valid, false otherwise.
        If items fail validation, The attribute 'last_validation_errors' will contain
        a dict whose keys are the index of the item in the submitted data list, and values
        which are lists of specific errors found in the item.
        ('last_validation_errors' is reset to None if validation succeeds.)
        """
        dta = []
        result = True
        self._validation_errors = {}
        if isinstance(data, dict):
            dta = [data]
        else:
            dta = data
        valf = self.validator(clsname)
        for i, rec in enumerate(dta):
            try:
                valf(rec, strict=strict)
            except ValidationError as e:
                result = False
                if verbose:
                    print(e.title, file=sys.stderr)
                self._validation_errors[i] = e.errors()
        if result:
            self._validation_errors = None
        return result

