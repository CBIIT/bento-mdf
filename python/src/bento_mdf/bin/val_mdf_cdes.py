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

DEFAULT_TIMEOUT = 60
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
MAX_LINE_WIDTH = 80
INDENT = "    "

logger = logging.getLogger(__name__)


def format_value_list(values: list[str], indent_level: int = 0) -> str:
    """Format a list of values with proper wrapping and indentation."""
    if not values:
        return ""

    indent = INDENT * indent_level
    lines = []
    current_line = []
    current_length = len(indent)

    for i, value in enumerate(values):
        # Add quotes around the value and comma if not last
        formatted_value = f"'{value}'"
        if i < len(values) - 1:
            formatted_value += ","

        # Check if adding this value would exceed line width
        if current_line and current_length + len(formatted_value) + 1 > MAX_LINE_WIDTH:
            # Join current line and add to lines
            lines.append(indent + " ".join(current_line))
            current_line = [formatted_value]
            current_length = len(indent) + len(formatted_value)
        else:
            current_line.append(formatted_value)
            current_length += (
                len(formatted_value) + 1 if current_line else len(formatted_value)
            )

    # Add the last line
    if current_line:
        lines.append(indent + " ".join(current_line))

    return "\n".join(lines)


def print_formatted_output(message: str, indent_level: int = 0):
    """Print message with proper indentation."""
    indent = INDENT * indent_level
    print(f"{indent}{message}")


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
            print(f"{INDENT}No response from {url}")
            return
        latest_version = de.get("version", "")
        if not current_version:
            print(
                f"{INDENT}No CDE version specified for '{prop.handle}'. "
                f"Latest version is '{latest_version}'",
            )
        elif Version(str(current_version)) != Version(latest_version):
            print(
                f"{INDENT}CDE annotation for prop: '{prop.handle}' with id: '{cde_id}' "
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
            print(f"{INDENT}No response from {url}")
            return []
        json_response = response.json()
        value_set = get_pvs_from_cde_json(json_response)
    except JSONDecodeError as e:
        msg = f"Failed to parse JSON response for entity {prop.handle}: {e}\nurl: {url}"
        logger.exception(msg)
        return []
    else:
        return value_set


def check_enum_against_cde_pvs(model: Model, output_format: str = "text") -> None:
    """Compare enumerated value sets to CDE PVs for CDE-annotated properties."""
    already_checked = set()
    results = []  # For table format

    # Add section header
    if output_format == "text":
        print("\n##################################")
        print("#                                #")
        print("#        CDE Validation          #")
        print("#                                #")
        print("##################################")
        print("\nChecking CDE annotations against caDSR for CDE-annotated properties:")
        print("----------\n")

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

        logger.info(
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
            if output_format == "text":
                print(
                    f"{INDENT}CDE '{cde_id}' 'v{cde_version}' has {len(pvs_not_in_enum)} "
                    f"PVs not in enumerated value set for '{prop.handle}':",
                )
                print(format_value_list(sorted(pvs_not_in_enum)))
            else:
                results.append(
                    {
                        "Property": prop.handle,
                        "CDE ID": cde_id,
                        "CDE Version": cde_version or "",
                        "Issue Type": "CDE PVs not in Model",
                        "Count": len(pvs_not_in_enum),
                        "Values": ", ".join(sorted(pvs_not_in_enum)),
                    },
                )

        vals_not_in_cde_pvs = [v for v in model_terms if v not in cde_pvs]
        if vals_not_in_cde_pvs:
            if output_format == "text":
                print(
                    f"{INDENT}Enumerated value set for '{prop.handle}' has "
                    f"{len(vals_not_in_cde_pvs)} values not in CDE '{cde_id}' "
                    f"'v{cde_version}':",
                )
                print(format_value_list(sorted(vals_not_in_cde_pvs)))
            else:
                results.append(
                    {
                        "Property": prop.handle,
                        "CDE ID": cde_id,
                        "CDE Version": cde_version or "",
                        "Issue Type": "Model values not in CDE",
                        "Count": len(vals_not_in_cde_pvs),
                        "Values": ", ".join(sorted(vals_not_in_cde_pvs)),
                    },
                )

        already_checked.add(key)

    # If table format requested, print the table
    if output_format == "table" and results:
        print_table(results)


def print_table(results: list[dict]) -> None:
    """Print results in a simple table format."""
    # Group results by property
    property_groups = {}
    for result in results:
        prop = result["Property"]
        if prop not in property_groups:
            property_groups[prop] = []
        property_groups[prop].append(result)

    print("\n\tCDE Validation Results")
    print("\t----------")
    print(
        "\t+--------------------+-------------+----------+--------------------------+---------------+",
    )
    print(
        "\t| property           | cde_id      | version  | check                    | error count   |",
    )
    print(
        "\t+--------------------+-------------+----------+--------------------------+---------------+",
    )

    for prop, results_list in property_groups.items():
        for i, result in enumerate(results_list):
            if i == 0:
                prop_display = prop[:18] + ".." if len(prop) > 20 else prop
            else:
                prop_display = ""

            issue_display = (
                result["Issue Type"][:24] + ".."
                if len(result["Issue Type"]) > 26
                else result["Issue Type"]
            )

            print(
                f"\t| {prop_display:<18} | {result['CDE ID']:<11} | {result['CDE Version']:<8} | {issue_display:<24} | {result['Count']!s:<13} |",
            )

    print(
        "\t+--------------------+-------------+----------+--------------------------+---------------+",
    )

    # Print detailed values below the table
    print("\n\tDetailed error values:")
    print("\t----------")
    for prop, results_list in property_groups.items():
        if any(r["Count"] > 0 for r in results_list):
            print(f"\n\t{prop}:")
            for result in results_list:
                if result["Count"] > 0:
                    print(f"\t  {result['Issue Type']} ({result['Count']} values):")
                    # Get full list of values from the result
                    print(f"\t    {result['Values']}")


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
@click.option(
    "--output_format",
    type=click.Choice(["text", "table"]),
    default="text",
    help="Output format: text (default) or table",
)
def main(mdf_files: str | list[str], output_format: str) -> None:
    """Compare enum from MDFs to CDE PVs from caDSR for CDE-annotated properties."""
    mdf = MDFReader(*mdf_files, raise_error=True)
    model = mdf.model
    check_enum_against_cde_pvs(model, output_format=output_format)


if __name__ == "__main__":
    main()  # type: ignore reportCallIssue
