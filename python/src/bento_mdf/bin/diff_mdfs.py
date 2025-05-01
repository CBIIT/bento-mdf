#!/usr/bin/env python
"""Generate, view, and save model diff."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import click
from bento_mdf.diff import diff_models
from bento_mdf.mdf.reader import MDFReader

logger = logging.getLogger("__name__")


@click.command()
@click.option(
    "--model_handle",
    required=True,
    type=str,
    prompt=True,
    help="CRDC Model Handle (e.g. 'GDC')",
)
@click.option(
    "--old_mdfs",
    required=True,
    type=str,
    prompt=True,
    multiple=True,
    help=(
        "Older version of MDF file(s). "
        "If MDF split into multiple files, provide url or path to each file."
    ),
)
@click.option(
    "--new_mdfs",
    required=True,
    type=str,
    prompt=True,
    multiple=True,
    help=(
        "Newer version of MDF file(s). "
        "If MDF split into multiple files, provide url or path to each file."
    ),
)
@click.option(
    "--old_version",
    required=False,
    type=str,
    help="Older version of MDF file(s) if not included in MDF",
)
@click.option(
    "--new_version",
    required=False,
    type=str,
    help="Newer version of MDF file(s)",
)
@click.option(
    "--output_path",
    required=False,
    type=str,
    prompt=False,
    help="File path for output diff. If not provided, diff will be save to cwd.",
)
@click.option(
    "--include_summary",
    required=False,
    type=bool,
    default=True,
    help="Include a summary of the diff in the result",
)
@click.option(
    "--objects_as_dicts",
    required=False,
    type=bool,
    default=False,
    help="Return dictionaries with entity attributes instead of bento_meta objects",
)
@click.option(
    "--summary_only",
    required=False,
    type=bool,
    default=False,
    help="Only include the diff summary in the result",
)
def main(  # noqa: PLR0913
    model_handle: str,
    old_mdfs: str | Path | list[str | Path],
    new_mdfs: str | Path | list[str | Path],
    old_version: str | None = None,
    new_version: str | None = None,
    *,
    include_summary: bool = True,
    objects_as_dicts: bool = True,
    output_path: Path | str | None,
    summary_only: bool = False,
) -> None:
    """Diff two versions of MDF files for a model."""
    old_mdf = MDFReader(*old_mdfs, handle=model_handle)
    new_mdf = MDFReader(*new_mdfs, handle=model_handle)

    if old_version:
        old_mdf.model.version = old_version
    if new_version:
        new_mdf.model.version = new_version

    summary = include_summary or summary_only

    diff = diff_models(
        mdl_a=old_mdf.model,
        mdl_b=new_mdf.model,
        objects_as_dicts=objects_as_dicts,
        include_summary=summary,
    )

    result = diff.get("summary") if summary_only else diff
    output_file_extension = "txt" if summary_only else "py"

    if output_path is None:
        output_path = (
            Path.cwd() / f"{model_handle}_diff_"
            f"{old_mdf.model.version}_{new_mdf.model.version}.{output_file_extension}"
        )
    dict_as_str = repr(result)
    with Path(output_path).open("w+", encoding="utf-8") as f:
        f.write(f"diff = {dict_as_str}")
    try:
        os.startfile(output_path)  # noqa: S606
    except OSError as e:
        msg = f"Error opening the file: {e}"
        logger.exception(msg)


if __name__ == "__main__":
    main()
