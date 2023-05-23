#!/usr/bin/env python
import sys
sys.path.insert(0, '..')
import os
import getpass
import argparse
from bento_mdf.mdf import MDF
from bento_meta.mdb import (
    WriteableMDB, make_nanoid, load_mdf, load_model_statements
    )
from sys import stderr

parser = argparse.ArgumentParser(description="Load model in MDF into an MDB")
parser.add_argument('files', nargs="*",
                    metavar="MDF-FILE", help="MDF file(s)/url(s)")
parser.add_argument('--commit', default='',
                    help="commit SHA1 for MDF instance (if any)",
                    required=True)
parser.add_argument('--handle', help="model handle")
parser.add_argument('--user', help="MDB username")
parser.add_argument('--passw', help="MDB password")
parser.add_argument('--bolt', metavar="BoltURL",
                    help="MDB Bolt url endpoint (specify as 'bolt://...')")
parser.add_argument('--put', action='store_true',
                    help="Load model to database")
parser.add_argument('--make-nanoids', action='store_true',
                    help="Add new nanoids to graph nodes")
# example:
# args = parser.parse_args([
#     "https://raw.githubusercontent.com/CBIIT/icdc-model-tool/master/model-desc/icdc-model.yml",
#     "https://raw.githubusercontent.com/CBIIT/icdc-model-tool/master/model-desc/icdc-model-props.yml",
#     "--commit",
#     "a4aa9a43b9ad2087638ceaeef50d4a22a4b9b959",
#     "--handle",
#     "ICDC",
#     "--bolt",
#     "bolt://localhost:7687",
#     "--user",
#     "neo4j",
#     "--passw",
#     getpass.getpass()
#     ])

args = parser.parse_args()

if not args.files:
    parser.print_help(file=stderr)
    parser.exit(1)

if args.put and not args.bolt:
    print("error: --bolt and --user args required to put to database",file=stderr)
    parser.exit(2)
    
if args.put and not args.passw:
    args.passw = getpass.getpass()

print("load model from MDFs", file=stderr)
mdf = MDF(*args.files, handle=args.handle,
          _commit=args.commit, raiseError=True)
model = mdf.model

if args.put:
    print("Put model to DB",file=stderr)
    mdb = WriteableMDB(uri=args.bolt, user=args.user, password=args.passw)
    model.mdb = mdb
    load_mdf(mdf, model.mdb)
    if args.make_nanoids:
        print("Add nanoids to nodes",file=stderr)
        with mdb.driver.session() as s:
            result = s.run(
                "match (n {_commit:$commit}) where not exists(n.nanoid) "
                "with n limit 1 set n.nanoid=$nanoid return n",
                {"commit": args.commit, "nanoid": make_nanoid()}
            )
            while (result.peek()):
                result = s.run(
                    "match (n {_commit:$commit}) where not exists(n.nanoid) "
                    "with n limit 1 set n.nanoid=$nanoid return n",
                    {"commit": args.commit, "nanoid": make_nanoid()}
                    )
else:
    for s in load_model_statements(model, args.commit):
        print(s)

