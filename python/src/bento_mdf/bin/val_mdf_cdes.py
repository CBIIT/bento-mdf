#!/usr/bin/env python
"""CDE checks for models from MDFs."""

from __future__ import annotations

import logging
import re
from json import JSONDecodeError
from typing import TYPE_CHECKING

import click
import requests
import stamina
from bento_mdf.mdf.reader import MDFReader

if TYPE_CHECKING:
    from bento_meta.model import Model
    from bento_meta.objects import Property
from packaging.version import Version

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_pvs_from_cde_json(json: dict) -> list[str]:
    """Get CDE PVs from a CDE JSON response."""
    try:
        vs = []
        de = json.get("DataElement", {})
        if not de:
            return vs
        cde_pvs = de.get("ValueDomain", {}).get("PermissibleValues", [])
        if not cde_pvs:
            return vs
        vs.extend([pv["value"] for pv in cde_pvs])
    except Exception as e:
        msg = f"Exception occurred when getting value set from JSON: {e}"
        logger.exception(msg)
        return []
    else:
        return vs


def check_cde_version(
    prop: Property,
    cde_id: str,
    current_version: str | None,
) -> None:
    """Check for new CDE versions for CDE-annotated properties."""
    url = f"https://cadsrapi.cancer.gov/rad/NCIAPI/1.0/api/DataElement/{cde_id}"
    headers = {"accept": "application/json"}
    try:
        response = requests.get(
            url,
            timeout=DEFAULT_TIMEOUT,
            headers=headers,
        )
        response.raise_for_status()
        de = response.json().get("DataElement", {})
        if not de:
            print(f"No response from {url}")
            return
        latest_version = de.get("version", "")
        if not current_version:
            print(
                f"No CDE version specified for '{prop.handle}'. "
                f"Latest version is '{latest_version}'",
            )
        elif Version(str(current_version)) != Version(latest_version):
            print(
                f"CDE annotation for prop: '{prop.handle}' with id: '{cde_id}' "
                f"and version: '{current_version}' doesn't match "
                f"latest version: '{latest_version}'",
            )
    except JSONDecodeError:
        msg = (
            f"Failed to parse JSON response for entity {prop.handle} "
            f"annotated with CDE {cde_id}v{current_version}"
        )
        logger.exception(msg)
        return


@stamina.retry(on=requests.RequestException, attempts=DEFAULT_RETRIES)
def fetch_cde_pvs(
    prop: Property,
    cde_id: str,
    cde_version: str | None = None,
) -> list[str]:
    """Fetch CDE PVs for a given CDE version."""
    version_str = (
        f"?version={cde_version}"
        if cde_version and re.match(r"^v?\d{1,3}(\.\d{1,3}){0,2}$", cde_version)
        else ""
    )
    cde_param = f"{cde_id}{version_str}"
    url = f"https://cadsrapi.cancer.gov/rad/NCIAPI/1.0/api/DataElement/{cde_param}"
    headers = {"accept": "application/json"}
    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT, headers=headers)
        response.raise_for_status()
        if not response:
            print(f"No response from {url}")
            return []
        json_response = response.json()
        value_set = get_pvs_from_cde_json(json_response)
    except JSONDecodeError as e:
        msg = f"Failed to parse JSON response for entity {prop.handle}: {e}\nurl: {url}"
        logger.exception(msg)
        return []
    else:
        return value_set


def check_enum_against_cde_pvs(model: Model) -> None:
    """Compare enumerated value sets to CDE PVs for CDE-annotated properties."""
    already_checked = set()
    for prop in model.props.values():
        prop_annotations = prop.annotations
        if not prop_annotations:
            continue
        annotations = prop_annotations.values()
        if not any("cadsr" in t.origin_name.lower() for t in annotations):
            continue
        for term in annotations:
            if "cadsr" not in term.origin_name.lower():
                continue
            cde_id = term.origin_id
            cde_version = term.origin_version
        key = (prop.handle, cde_id, cde_version)
        if key in already_checked:
            continue
        print(
            f"Checking CDE '{cde_id}' 'v{cde_version}' for prop '{prop.handle}'",
        )
        already_checked.add(key)
        check_cde_version(prop, cde_id, cde_version)
        cde_pvs = fetch_cde_pvs(prop, cde_id, cde_version)
        if not cde_pvs:
            continue
        model_terms = prop.values
        if not model_terms:
            continue
        pvs_not_in_enum = [pv for pv in cde_pvs if pv not in model_terms]
        if pvs_not_in_enum:
            print(
                f"CDE '{cde_id}' 'v{cde_version}' has {len(pvs_not_in_enum)} "
                f"PVs not in enumerated value set for '{prop.handle}':\n\t"
                f"{', '.join(sorted(f"'{pv}'" for pv in pvs_not_in_enum))}",
            )
        vals_not_in_cde_pvs = [v for v in model_terms if v not in cde_pvs]
        if vals_not_in_cde_pvs:
            print(
                f"Enumerated value set for '{prop.handle}' has "
                f"{len(vals_not_in_cde_pvs)} values not in CDE '{cde_id}' "
                f"'v{cde_version}':\n\t"
                f"{', '.join(sorted(f"'{v}'" for v in vals_not_in_cde_pvs))}",
            )
        already_checked.add(key)


@click.command()
@click.option(
    "-f",
    "--mdf-files",
    help="MDF file(s) to compare. If you have multiple, use this for each file.",
    required=True,
    type=str,
    prompt=True,
    multiple=True,
)
def main(mdf_files: str | list[str]) -> None:
    """Compare enum from MDFs to CDE PVs from caDSR for CDE-annotated properties."""
    mdf = MDFReader(*mdf_files, raise_error=True)
    model = mdf.model
    check_enum_against_cde_pvs(model)


if __name__ == "__main__":
    main()  # type: ignore reportCallIssue
