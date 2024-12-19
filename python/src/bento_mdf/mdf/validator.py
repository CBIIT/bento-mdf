from typing import Any, Dict, List, Literal, Optional

import requests
import yaml
from pydantic import BaseModel, Field


class ConfigUri(BaseModel):
    """Defines the URI configuration for the schema."""

    model_file_path: str = Field(
        title="MDF Model File Path",
        description="The path to the MDF model file.",
    )

    props_file_path: str = Field(
        title="MDF Props File Path",
        description="The path to the MDF props file.",
    )

    base_schema_uri: str = Field(
        title="Base Schema URI",
        description="The base URI for the schema files.",
    )


class ConfigMeta(BaseModel):
    """Defines the metadata configuration for the schema."""

    schema_ref: str = Field(
        title="Schema Reference",
        description="The reference to the schema.",
    )

    title: str = Field(
        title="Schema Title",
        description="The title of the project schema.",
    )

    description: str = Field(
        title="Schema Description",
        description="The description of the schema.",
    )


class Config(BaseModel):
    """Defines the configuration for the MDF Processor."""

    uri: ConfigUri = Field(
        title="URI Configuration",
        description="Configuration for the URI paths.",
    )

    meta: ConfigMeta = Field(
        title="Metadata Configuration",
        description="Configuration for the schema metadata.",
    )


class MdfToJsonSchema:
    def __init__(self, config: Config):

        self.cfg = config

        # MDF Data Structures
        self.mdf_model: Dict[str, Any] = self.load_mdf(self.cfg.uri.model_file_path)
        self.mdf_props: Dict[str, Any] = self.load_mdf(self.cfg.uri.props_file_path)
        self.mdf_nodes: List[str] = self.mdf_model["Nodes"].keys()

        # JSON Schema
        self.node_schemas: List[Dict[str, Any]] = []
        self.main_schema = Dict[str, Any]

    def load_mdf(self, uri: str) -> Dict[str, Any]:
        """
        Loads an MDF file from a URI and returns the data as a dictionary.
        Args:
            uri (str): The URI to the MDF file.

        Returns:
            Dict[str, Any]: The MDF data as a dictionary.
        """
        data = requests.get(uri, timeout=10)
        return yaml.safe_load(data.text)

    def initialize_schema(
        self,
        title: str,
        desc: Optional[str] = None,
        data_type: Literal["array", "object"] = "object",
    ) -> Dict[str, Any]:
        """
        Initializes a JSON Schema Object with provided metadata.
        Args:
            title (str): The title of the schema.
            desc (str, optional): The description of the schema. Defaults to None.
            data_type (Literal["array", "object"], optional): The type of data structure.
                Defaults to "object".
        Returns:
            Dict: The initialized JSON Schema Object.
        """
        props: Dict[str, Any] | List[Any] = {} if data_type == "object" else []
        description = f"A model for the {title} node." if not desc else desc
        return {
            "$schema": self.cfg.meta.schema_ref,
            "$id": f"{self.cfg.uri.base_schema_uri}/{title}.json",
            "title": title,
            "description": description,
            "type": "array",
            "properties": props,
            "required": [],
        }

    def generate_node_schemas(self):
        """
        Generates JSON Schema Objects for each node in the MDF model.
        """

        for name in self.mdf_nodes:
            node = self.mdf_model["Nodes"].get(name, {})
            schema = self.initialize_schema(name)

            for prop_name in node.get("Props", []):
                prop = self.mdf_props["PropDefinitions"].get(prop_name, {})
                prop_key = f"_{prop_name}" if prop.get("Private", True) else prop_name
                prop_enum = prop.get("Enum", [])
                prop_req = prop.get("Req", False)
                prop_def = {
                    "description": prop.get("Desc", ""),
                    "type": prop.get("Type", "string"),
                }

                if prop_enum:
                    prop_def["enum"] = prop_enum

                if prop_req:
                    schema["required"].append(prop_key)

                schema["properties"][prop_key] = prop_def

            self.node_schemas.append(schema)

    def generate_main_schema(self) -> None:
        """
        Generates the main JSON Schema Object for the MDF model, which references the node schemas.
        """
        schema = self.initialize_schema(
            title=self.cfg.meta.title, desc=self.cfg.meta.description, data_type="array"
        )

        schema["properties"] = {
            ns["title"]: {"$ref": ns["$id"]} for ns in self.node_schemas
        }
        schema["required"] = [ns["title"] for ns in self.node_schemas]

        self.main_schema = schema
