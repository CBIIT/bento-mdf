import re
from typing import Annotated
from typing_extensions import TypeAliasType
from annotated_types import Predicate, Unit
from pydantic import WithJsonSchema


def MatchedStrTypeAlias(name : str, pat : str):
    return TypeAliasType(name, MatchedStrType(pat))


def MatchedStrType(pat : str):
    return Annotated[str,
                     Predicate(re.compile(pat).fullmatch),
                     WithJsonSchema({"pattern":pat})]


def URIType():
    return MatchedStrType("^https?://.*")


def NumberWithUnitsType(valtype: type(int) | type(float), units : str):
    return Annotated[valtype, Unit(x)]


