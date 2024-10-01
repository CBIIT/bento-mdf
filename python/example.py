"""bento-mdf example."""  # noqa: INP001

from pathlib import Path

from bento_mdf.mdf import MDF
from icecream import ic

MDF_FILE_DIR = Path("C:/Users/nelso/Downloads/ccdi-model-1.9.1/model-desc")
MDF_FILES = [
    MDF_FILE_DIR / "ccdi-model.yml",
    MDF_FILE_DIR / "ccdi-model-props.yml",
    MDF_FILE_DIR / "terms.yml",
]


def main() -> None:
    """Load MDF and access parts of it."""
    mdf = MDF(*MDF_FILES)
    node = mdf.model.nodes["sample"]
    prop = node.props["anatomic_site"]
    term = prop.concept.terms[("disease_anatomic_site_icd-o-3_label_text", "caDSR")]
    ic(term.get_attr_dict())


if __name__ == "__main__":
    main()
