import delfick_project.option_merge as om
import yaml
import logging
from logging import debug, info, warning, error
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

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

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
    def __init__(self, sch_file, *inst_files, verbose=0):
        self.schema = None
        if verbose > 0:
            logger.setLevel(logging.INFO)
        elif verbose < 0:
            logger.setLevel(logging.NOTSET)
        else:
            logger.setLevel(logging.WARNING)
        self.instance = om.MergedOptions()
        self.sch_file = sch_file
        self.inst_files = inst_files
        self.yloader = yaml.loader.Loader
        self.yaml_valid = False

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
                logger.error("Error in fetching mdf-schema.yml: \n{e}".format(e=e))
                return
        elif isinstance(self.sch_file, str):
            try:
                self.sch_file = open(self. sch_file, "r")
            except IOError as e:
                logger.error(e)
                return
        else:
            pass
        try:
            logger.info("Checking schema YAML =====")
            self.schema = yaml.load(self.sch_file, Loader=self.yloader)
        except ConstructorError as ce:
            logger.error("YAML error in MDF Schema '{fn}':\n{e}".format(
                fn=self.sch_file.name, e=ce))
            return
                
        except ParserError as e:
            logger.error("YAML error in MDF Schema '{fn}':\n{e}".format(
                  fn=self.sch_file.name, e=e))
            return
        except Exception as e:
            logger.error("Exception in loading MDF Schema yaml: {}".format(e))
            return
        logger.info("Checking as a JSON schema =====")
        try:
            d6.check_schema(self.schema)
        except SchemaError as se:
            logger.error("MDF Schema error: {}".format(se))
            return
        except Exception as e:
            logger.error("Exception in checking MDF Schema: {}".format(e))
            return
        return self.schema

    def load_and_validate_yaml(self):
        if self.instance:
            return self.instance
        if (self.inst_files):
            logger.info("Checking instance YAML =====")
            for inst_file in self.inst_files:
                if isinstance(inst_file, str):
                    inst_file = open(inst_file, "r")
                try:
                    inst_yaml = yaml.load(inst_file, Loader=self.yloader)
                    self.instance.update(inst_yaml)
                except ConstructorError as ce:
                    logger.error("YAML error in '{fn}':\n{e}".format(
                        fn=inst_file.name, e=str(ce)))
                    return
                except ParserError as e:
                    logger.error("YAML error in '{fn}':\n{e}".format(fn=inst_file.name,e=e))
                    return
                except ScannerError as e:
                    logger.error("YAML error in '{fn}':\n{e}".format(fn=inst_file.name,e=e))
                    return
                except Exception as e:
                    logger.error("Exception in loading yaml (instance): {}".format(e))
                    return
        return self.instance
        logger.error("No instance yaml(s) specified")
        return None
    
    def validate_instance_with_schema(self):
        if not self.schema:
            logger.warning("No valid schema; skipping this validation")
            return
        if not self.instance:
            logger.warning("No valid yaml instance; skipping this validation")
            return
        if (self.instance):
            logger.info("Checking instance against schema =====")
            try:
                validate(instance=self.instance.as_dict(), schema=self.schema)
            except ConstructorError as ce:
                logger.error(ce)
                return
            except RefResolutionError as re:
                logger.error(re)
                return
            except ValidationError as ve:
                for e in d6(self.schema).iter_errors(self.instance.as_dict()):
                    logger.error(e)
                return
            except Exception as e:
                logger.error("Exception during validation: {}".format(e))
                return
        return True
