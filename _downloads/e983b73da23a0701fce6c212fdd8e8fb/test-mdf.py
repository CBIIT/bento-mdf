#!/usr/bin/env python
# from pdb import set_trace
from sys import exit
import logging
from argparse import ArgumentParser, FileType
from bento_mdf.mdf import MDF
from bento_mdf.validator import MDFValidator

ap = ArgumentParser(description="Validate MDF against JSONSchema")
ap.add_argument('--schema',
                  help="MDF JSONschema file", type=FileType('r'),
                  dest="schema")
ap.add_argument('--quiet',
                  help="Suppress output; return only exit value",
                  action="store_true",
                  dest="quiet")
ap.add_argument('mdf_files',nargs='+',
                  metavar='mdf-file',
                  type=FileType('r'),
                  help="MDF yaml files for validation")
ap.add_argument("--log-file",
                help="Log file name")

def test(args, logger):
    retval = 0
    v = MDFValidator(args.schema, *args.mdf_files, logger=logger)
    if not v.load_and_validate_schema():
        retval += 1
    if not v.load_and_validate_yaml():
        retval += 1
    if not v.validate_instance_with_schema():
        retval += 1
    if not retval:
        for f in args.mdf_files:
            f.seek(0)
        if not MDF(*args.mdf_files, handle="test", logger=logger):
            retval += 1
    return retval


if __name__ == '__main__':
    args = ap.parse_args()
    logger = logging.getLogger("test-mdf")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(fmt="%(asctime)s:%(name)s (%(levelname)s) - %(message)s")
    shdl = logging.StreamHandler()
    shdl.setLevel(logging.INFO)
    shdl.setFormatter(fmt)
    logger.addHandler(shdl)
    if args.quiet:
        shdl.setLevel(logging.CRITICAL)
    if args.log_file:
        fhdl = logging.FileHandler(args.log_file)
        fhdl.setLevel(logging.DEBUG)
        fhdl.setFormatter(fmt)
        logger.addHandler(fhdl)
    exit(test(args, logger))  # emit return val (0 = good) to os
