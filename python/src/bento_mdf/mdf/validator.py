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
from typing import Any, List, NoReturn, Literal  # , TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, TypeAdapter, ValidationError, AnyUrl
from pydantic.json_schema import GenerateJsonSchema
from pdb import set_trace
import keyword

jenv = Environment(
    loader=PackageLoader("bento_mdf", package_path="mdf/templates"),
    trim_blocks=True,
)


# jinja helpers
def toCamelCase(val: str) -> str:
    return "".join([x.capitalize() for x in val.split("_")])


def normalize_operators(val: str) -> str:
    """Given a string, replace common operator characters with word equivalents.

    Args:
        val (str): input string

    Returns:
        str: normalized string
    """
    return (
        val.replace("+", " plus ")
        .replace("-", " minus ")
        .replace("/", " per ")
        .replace("#", " number ")
        .replace("%", " percent ")
        .replace("&", " and ")
        .replace("*", " asterisk ")
        .replace(",", " comma ")
        .replace(".", " dot ")
        .replace(";", " semicolon ")
        .replace(":", " colon ")
        .replace("!", " exclamation ")
        .replace("?", " question ")
        .replace("=", " equals ")
        .replace("<", " less_than ")
        .replace(">", " greater_than ")
    )


def to_snakecase(
    val: str, prefix_if_digit: str = "digit", empty_fallback: str = "unspecified"
) -> str:
    name = normalize_operators(val)
    name = re.sub(r"\W+", "_", name).lower()
    # Trim underscores at ends (prevents sunder-ish shapes and ugliness)
    name = name.strip("_")
    # Handle leading digit
    if name and name[0].isdigit():
        name = f"{prefix_if_digit}_{name}"
    # Handle Python keywords
    if keyword.iskeyword(name):
        name = name + "_"
    # Handle empty str
    if name == "":
        name = empty_fallback
    return name


def to_unit_types(unitstr: str, typ: type(int) | type(float)) -> List[str]:
    return [f"Annotated[{typ.__name__}, Unit('{u}')]" for u in unitstr.split(";")]


def maybe_optional(val: str, prop: Property):
    if prop.is_required:
        return val
    else:
        # the field is still required in pydantic unless we set a default None value
        return f"Optional[{val}] = None"


def maybe_list(val: str, prop: Property):
    if prop.value_domain == "list":
        return f"List[{val}]"
    else:
        return val


def pv_enum_fail(msg: str) -> NoReturn:
    raise ValueError(msg)


# register jinja filters and globals
jenv.filters["toCamelCase"] = toCamelCase
jenv.filters["to_snakecase"] = to_snakecase
jenv.filters["to_unit_types"] = to_unit_types
jenv.filters["maybe_optional"] = maybe_optional
jenv.filters["maybe_list"] = maybe_list
jenv.filters["pyrepr"] = repr
jenv.globals["pv_enum_fail"] = pv_enum_fail

AllowedValLevel = Literal["model", "node"]


class GenerateQualJsonSchema(GenerateJsonSchema):
    # override to add $schema tag
    def generate(self, schema, mode="validation"):
        json_schema = super().generate(schema, mode=mode)
        json_schema["$schema"] = self.schema_dialect
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
        self._validation_warnings = None  # warnings separate from errors
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
        model_class_name = toCamelCase(
            self.model.handle.replace("-", "").replace("_", "")
        )
        return self.module and f"{model_class_name}Data"

    @property
    def node_classes(self) -> List:
        return self._node_classes

    @property
    def enum_classes(self) -> List:
        return self._enum_classes

    @property
    def last_validation_errors(self) -> dict | None:
        return self._validation_errors

    @property
    def last_validation_warnings(self) -> dict | None:
        return self._validation_warnings

    def generate_data_model(self) -> NoReturn:
        """
        Generates Pydantic classes for each node in the MDF model.
        """
        # write down classes to be generated
        for node in self.model.nodes.values():
            self._node_classes.append(toCamelCase(node.handle))
            for pr in node.props.values():
                if pr.value_domain == "value_set" or pr.item_domain == "value_set":
                    if pr.value_set.url:
                        self._enum_classes.append(
                            "{}EnumURL".format(toCamelCase(pr.handle))
                        )
                    elif pr.value_set.path:
                        self._enum_classes.append(
                            "{}EnumPath".format(toCamelCase(pr.handle))
                        )
                    else:
                        self._enum_classes.append(
                            "{}Enum".format(toCamelCase(pr.handle))
                        )
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
            # print(self.data_model)
            modf.close()
            spec = importlib.util.spec_from_file_location(modname, modf.name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[modname] = module
            spec.loader.exec_module(module)
            self._module = module
            Path(modf.name).unlink()

    @cache
    def model_of(self, clsname: str):
        if (
            clsname != self.model_class
            and clsname not in self.node_classes
            and clsname not in self.enum_classes
        ):
            raise RuntimeError(f"Validation model does not contain class '{clsname}'")
        return eval("self.module.{}".format(clsname))

    @cache
    def fields_of(self, clsname: str) -> List[str]:
        if clsname != self.model_class and clsname not in self.node_classes:
            raise RuntimeError(
                f"Validation model does not contain node class '{clsname}'"
            )
        return [x for x in self.model_of(clsname).model_fields]

    def props_of(self, clsname: str) -> List[str]:
        return self.fields_of(clsname)

    @cache
    def validator(self, clsname: str):
        """
        Return a validator function appropriate to the class named 'clsname'
        """
        model = self.model_of(clsname)
        if issubclass(model, BaseModel):
            return model.model_validate
        else:
            return TypeAdapter(model).validate_python

    def json_schema(self, clsname: str) -> dict | list:
        """
        Return a jsonable object representing a JSONSchema that can validate
        the given model class.
        """

        model = self.model_of(clsname)
        if issubclass(model, BaseModel):
            return model.model_json_schema(schema_generator=GenerateQualJsonSchema)
        else:
            return TypeAdapter(model).json_schema(
                schema_generator=GenerateQualJsonSchema
            )

    def validate(
        self,
        handle_name: str,
        data: dict | List[dict],
        validate_level: AllowedValLevel = "node",
        strict: bool = False,
        verbose: bool = False,
    ) -> bool:
        """
        Validate a dict or list of dicts against a given model class.
        Returns true if all items are valid, false otherwise.
        If items fail validation, The attribute 'last_validation_errors' will contain
        a dict whose keys are the index of the item in the submitted data list, and values
        which are lists of specific errors found in the item.
        ('last_validation_errors' is reset to None if validation succeeds.)

        Arguments:
            handle_name: the handle of the model/node to validate against
            data: a dict or list of dicts to validate
            validate_level: the level of validation to perform. If 'model', validates at the model scope; if 'node', validates properties of the specified node. Default is 'node'.
            strict: if True, enforce strict validation on all fields/properties. Default is False.
            verbose: if True, print validation errors to stderr. Default is False.
        """
        dta = []
        if isinstance(data, dict):
            dta = [data]
        else:
            dta = data
        result = True
        self._validation_errors = {}
        self._validation_warnings = {}
        # validate at model level
        if handle_name == self.model.handle and validate_level == "model":
            clsname = self.model_class
        else:
            # validate at node level
            clsname = toCamelCase(handle_name)
        valf = self.validator(clsname)
        for i, rec in enumerate(dta):
            try:
                valf(rec, strict=strict)
            except ValidationError as e:
                result = False
                if verbose:
                    print(e.title, file=sys.stderr)
                warnings = []
                errs = []
                for err in e.errors():
                    # handle enum violations if the enum is non-strict, treat as warning instead of error
                    if err["type"] == "enum":
                        if validate_level == "model":
                            node_name = err["loc"][0]
                            prop_name = err["loc"][1]
                        else:
                            node_name = handle_name
                            prop_name = err["loc"][0]
                        prop_instance = self.model.nodes[node_name].props[prop_name]
                        if not prop_instance.is_strict:
                            # non-strict enum violation, treat as warning
                            # add level key
                            err = {"level": "warning", **err}
                            warnings.append(err)
                        else:
                            err = {"level": "error", **err}
                            errs.append(err)
                    else:
                        err = {"level": "error", **err}
                        errs.append(err)
                self._validation_errors[i] = errs
                if len(warnings) > 0:
                    self._validation_warnings[i] = warnings
        if result:
            self._validation_errors = None
            self._validation_warnings = None
        return result
