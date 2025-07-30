"""Tests of the MDF syntax validator."""

import logging
from argparse import Namespace
from pathlib import Path

from bento_mdf.bin.val_mdf import test

TDIR = Path("tests/").resolve() if Path("tests").exists() else Path().resolve()
TEST_MODEL_BB_FILE = TDIR / "samples" / "test-model-bb.yml"
TEST_ERR_MODEL_FILE = TDIR / "samples" / "test-missing-prop-defn.yml"


def test_missing_defn() -> None:
    args = Namespace()
    args.schema = None
    args.mdf_files = [open(TEST_MODEL_BB_FILE)]
    logger = logging.getLogger("test-mdf")
    assert test(args, logger) == 0
    args.mdf_files = [open(TEST_ERR_MODEL_FILE)]
    assert test(args, logger) > 0
