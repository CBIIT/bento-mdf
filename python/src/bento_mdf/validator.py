"""MDFValidator class for schema and YAML instance validation."""

from __future__ import annotations

import logging
from io import BufferedRandom, TextIOWrapper
from pathlib import Path
from tempfile import _TemporaryFileWrapper
from typing import TYPE_CHECKING

import requests
import yaml
from delfick_project.option_merge.merge import MergedOptions
from jsonschema import Draft6Validator, SchemaError, ValidationError, validate
from referencing.exceptions import Unresolvable
from yaml.constructor import ConstructorError
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from bento_mdf.loader import MDFLoader

if TYPE_CHECKING:
    from referencing.jsonschema import ObjectSchema


MDFSCHEMA_URL = "https://github.com/CBIIT/bento-mdf/raw/main/schema/mdf-schema.yaml"


class MDFValidator:
    """
    Schema and YAML instance validation for the Bento Model Description Format.

    Use to check and load MDF YAML into a python dict (see load_and_validate).
    """

    def __init__(
        self,
        sch_file: str | Path | TextIOWrapper | None,
        *inst_files: str | Path | TextIOWrapper | _TemporaryFileWrapper | None,
        raise_error: bool = False,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the MDFValidator object.

        Args:
            sch_file: The schema file.
            *inst_files: Variable number of instance files.
            raise_error: Whether to raise an error on validation failure. Default False.
            logger: The logger object. Defaults to logging.getLogger(__name__).
        """
        self.schema: ObjectSchema | None = None
        self.instance = MergedOptions()
        self.sch_file = sch_file
        self.inst_files = inst_files
        self.yloader = MDFLoader
        self.yaml_valid = False
        self.logger = logger or logging.getLogger(__name__)
        self.raise_error = raise_error

    def load_schema_from_url(self, url: str) -> str:
        """Load the schema from a URL."""
        try:
            sch = requests.get(url, timeout=10)
            sch.raise_for_status()
        except Exception:
            self.logger.exception("Error in fetching mdf-schema.yml")
            if self.raise_error:
                raise
            return ""
        else:
            return sch.text

    def load_schema_from_file(self, file: str | Path) -> str:
        """Load the contents of an MDF schema given its file path."""
        try:
            with Path(file).open() as f:
                return f.read()
        except OSError:
            self.logger.exception("Error in reading MDF Schema file")
            if self.raise_error:
                raise
            return ""

    def load_schema_from_yaml(self) -> ObjectSchema | None:
        """Load object schema from the schema file YAML."""
        try:
            self.logger.info("Checking schema YAML =====")
            return yaml.load(self.sch_file, Loader=self.yloader)  # noqa: S506
        except ConstructorError:
            self.logger.exception(
                "YAML error in MDF Schema '%s'",
                self.schema.get("name"),
            )
            if self.raise_error:
                raise
            return None
        except ParserError:
            self.logger.exception(
                "YAML error in MDF Schema '%s'",
                self.schema.get("name"),
            )
            if self.raise_error:
                raise
            return None
        except Exception:
            self.logger.exception("Exception in loading MDF Schema yaml")
            if self.raise_error:
                raise
            return None

    def check_schema_as_json(self) -> None:
        """Validate self.schema as a JSON schema."""
        self.logger.info("Checking as a JSON schema =====")
        if not self.schema:
            self.logger.error("No schema found")
            return
        try:
            Draft6Validator.check_schema(self.schema)
        except SchemaError:
            self.logger.exception("MDF Schema error")
            if self.raise_error:
                raise
            return
        except Exception:
            self.logger.exception("Exception in checking MDF Schema")
            if self.raise_error:
                raise
            return

    def load_and_validate_schema(self) -> ObjectSchema | None:
        """Load schema object from file or URL and validate it as YAML and JSON."""
        if self.schema:
            return self.schema
        if not self.sch_file:
            self.sch_file = self.load_schema_from_url(MDFSCHEMA_URL)
        elif isinstance(self.sch_file, (str, Path)):
            sch_file_str = self.sch_file
            self.sch_file = self.load_schema_from_file(sch_file_str)
        self.schema = self.load_schema_from_yaml()
        self.check_schema_as_json()

        return self.schema

    def update_instance_from_yaml_file(
        self,
        file: TextIOWrapper | _TemporaryFileWrapper | BufferedRandom,
    ) -> None:
        """Update self.instance with the contents of the YAML file object."""
        inst_yaml = yaml.load(file, Loader=self.yloader)  # noqa: S506
        self.instance.update(inst_yaml)

    def load_yaml_from_inst_file(
        self,
        inst_file: str
        | Path
        | TextIOWrapper
        | _TemporaryFileWrapper
        | BufferedRandom
        | None,
    ) -> None:
        """Load the YAML instance from files."""
        # inst_file is a file path
        if isinstance(inst_file, (str, Path)):
            with Path(inst_file).open(encoding="UTF-8") as f:
                self.update_instance_from_yaml_file(f)
        # inst_file is a file object
        elif isinstance(
            inst_file,
            (TextIOWrapper, _TemporaryFileWrapper, BufferedRandom),
        ):
            self.update_instance_from_yaml_file(inst_file)
        else:
            self.logger.error(
                "Invalid instance file type: %s",
                type(inst_file),
            )

    def load_and_validate_yaml(self) -> MergedOptions | None:
        """Load and validate the YAML instance."""
        if self.instance:
            return self.instance
        if not self.inst_files:
            msg = "No instance yaml(s) specified"
            self.logger.exception(msg)
            if self.raise_error:
                raise ValueError(msg)
        self.logger.info("Checking instance YAML =====")
        try:
            for inst_file in self.inst_files:
                self.load_yaml_from_inst_file(inst_file)
        except (ConstructorError, ParserError, ScannerError):
            self.logger.exception("YAML error in '%s'", inst_file)
            if self.raise_error:
                raise
            return None
        except Exception:
            self.logger.exception(
                "Exception in loading yaml (instance) %s",
                inst_file,
            )
            if self.raise_error:
                raise
            return None
        return self.instance

    def validate_instance_with_schema(self) -> MergedOptions | None:
        """Validate the instance with the schema."""
        if not self.schema:
            self.logger.warning("No valid schema; skipping this validation")
            return None
        if not self.instance:
            self.logger.warning("No valid yaml instance; skipping this validation")
            return None
        self.logger.info("Checking instance against schema =====")
        try:
            validate(instance=self.instance.as_dict(), schema=self.schema)
        except ValidationError:
            for e in Draft6Validator(self.schema).iter_errors(self.instance.as_dict()):
                self.logger.exception(e)
            if self.raise_error:
                raise
            return None
        except (ConstructorError, Unresolvable, Exception):
            self.logger.exception("Exception during validation")
            if self.raise_error:
                raise
            return None
        return self.instance
