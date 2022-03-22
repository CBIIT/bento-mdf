#!/usr/bin/env python
# from pdb import set_trace
import requests
from sys import exit
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


def test(v):
    retval = 0
    if not v.load_and_validate_schema():
        retval+=1;
    if not v.load_and_validate_yaml():
        retval+=1;
    if not v.validate_instance_with_schema():
        retval+=1;
    return retval


if __name__ == '__main__':
    args = ap.parse_args()
    v = MDFValidator(args.schema, verbose=(-1 if args.quiet else 2),
                     *args.mdf_files)
    exit(test(v))  # emit return val (0 = good) to os
