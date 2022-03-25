import delfick_project.option_merge as om
import yaml
import logging
import requests
from jsonschema import (
  validate, ValidationError, SchemaError, RefResolutionError
  )
from jsonschema import Draft6Validator as d6
from yaml.parser import ParserError, ScannerError
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode, SequenceNode
from pdb import set_trace

MDFSCHEMA_URL = "https://github.com/CBIIT/bento-mdf/raw/master/schema/mdf-schema.yaml"

def construct_mapping(self, node, deep=False):
    if not isinstance(node, MappingNode):
        raise ConstructorError(
            None, None, "expected a mapping node, but found %s" % node.id,
            node.start_mark)
    mapping = {}

    for key_node, value_node in node.value:
        key = self.construct_object(key_node, deep=deep)
        try:
            hash(key)
        except TypeError as exc:
            raise ConstructorError("while constructing a mapping",
                                   node.start_mark,
                                   "found unacceptable key (%s)" %
                                   exc, key_node.start_mark)
        value = self.construct_object(value_node, deep=deep)
        if key in mapping:
            raise ConstructorError("while constructing a mapping",
                                   node.start_mark,
                                   "found duplicated key (%s)" %
                                   key, key_node.start_mark)
        mapping[key] = value
    return mapping


def construct_sequence(self, node, deep=False):
    if not isinstance(node, SequenceNode):
        raise ConstructorError(None, None,
                               "expected a sequence node, but found %s" %
                               node.id, node.start_mark)
    elts = set()
    for c in node.value:
        if isinstance(c.value, str):  # just check lists of strings
            if c.value in elts:
                raise ConstructorError("while constructing a sequence",
                                       node.start_mark,
                                       "found duplicated element (%s)" %
                                       c.value)
            else:
                elts.add(c.value)
    return [self.construct_object(child, deep=deep) for child in node.value]


class MDFValidator:
    """Class that encapsulates schema and YAML instance validation for the
    Bento Model Description Format. Use to check and load MDF YAML into 
    a python dict (see load_and_validate)."""
    def __init__(self, sch_file, *inst_files, raiseError=False,
                 logger=logging.getLogger(__name__)):
        self.schema = None
        self.instance = om.MergedOptions()
        self.sch_file = sch_file
        self.inst_files = inst_files
        self.yloader = yaml.loader.Loader
        self.yaml_valid = False
        self.logger = logger
        self.raiseError = raiseError

        # monkey patches to detect dup keys, elts
        self.yloader.construct_mapping = construct_mapping
        self.yloader.construct_sequence = construct_sequence
        
    def load_and_validate_schema(self):
        if self.schema:
            return self.schema
        if not self.sch_file:
            try:
                sch = requests.get(MDFSCHEMA_URL)
                sch.raise_for_status()
                self.sch_file = sch.text
            except Exception as e:
                self.logger.error("Error in fetching mdf-schema.yml: \n{e}".format(e=e))
                if self.raiseError:
                    raise e
                return
        elif isinstance(self.sch_file, str):
            try:
                self.sch_file = open(self. sch_file, "r")
            except IOError as e:
                self.logger.error(e)
                if self.raiseError:
                    raise e
                return
        else:
            pass
        try:
            self.logger.info("Checking schema YAML =====")
            self.schema = yaml.load(self.sch_file, Loader=self.yloader)
        except ConstructorError as ce:
            self.logger.error("YAML error in MDF Schema '{fn}':\n{e}".format(
                fn=self.sch_file.name, e=ce))
            if self.raiseError:
                raise
            return
                
        except ParserError as e:
            self.logger.error("YAML error in MDF Schema '{fn}':\n{e}".format(
                  fn=self.sch_file.name, e=e))
            if self.raiseError:
                raise e
            return
        except Exception as e:
            self.logger.error("Exception in loading MDF Schema yaml: {}".format(e))
            if self.raiseError:
                raise e
            return
        self.logger.info("Checking as a JSON schema =====")
        try:
            d6.check_schema(self.schema)
        except SchemaError as se:
            self.logger.error("MDF Schema error: {}".format(se))
            if self.raiseError:
                raise se
            return
        except Exception as e:
            self.logger.error("Exception in checking MDF Schema: {}".format(e))
            if self.raiseError:
                raise e
            return
        return self.schema

    def load_and_validate_yaml(self):
        if self.instance:
            return self.instance
        if (self.inst_files):
            self.logger.info("Checking instance YAML =====")
            for inst_file in self.inst_files:
                if isinstance(inst_file, str):
                    inst_file = open(inst_file, "r")
                try:
                    inst_yaml = yaml.load(inst_file, Loader=self.yloader)
                    self.instance.update(inst_yaml)
                except ConstructorError as ce:
                    self.logger.error("YAML error in '{fn}':\n{e}".format(
                        fn=inst_file.name, e=str(ce)))
                    if self.raiseError:
                        raise ce
                    return
                except ParserError as e:
                    self.logger.error("YAML error in '{fn}':\n{e}".format(fn=inst_file.name,e=e))
                    if self.raiseError:
                        raise e
                    return
                except ScannerError as e:
                    self.logger.error("YAML error in '{fn}':\n{e}".format(fn=inst_file.name,e=e))
                    if self.raiseError:
                        raise e
                    return
                except Exception as e:
                    self.logger.error("Exception in loading yaml (instance): {}".format(e))
                    if self.raiseError:
                        raise e
                    return
        return self.instance
        self.logger.error("No instance yaml(s) specified")
        return None
    
    def validate_instance_with_schema(self):
        if not self.schema:
            self.logger.warning("No valid schema; skipping this validation")
            return
        if not self.instance:
            self.logger.warning("No valid yaml instance; skipping this validation")
            return
        if (self.instance):
            self.logger.info("Checking instance against schema =====")
            try:
                validate(instance=self.instance.as_dict(), schema=self.schema)
            except ConstructorError as ce:
                self.logger.error(ce)
                if self.raiseError:
                    raise ce
                return
            except RefResolutionError as re:
                self.logger.error(re)
                if self.raiseError:
                    raise re
                return
            except ValidationError as ve:
                for e in d6(self.schema).iter_errors(self.instance.as_dict()):
                    self.logger.error(e)
                if self.raiseError:
                    raise ve
                return
            except Exception as e:
                self.logger.error("Exception during validation: {}".format(e))
                if self.raiseError:
                    raise e
                return
        return self.instance
