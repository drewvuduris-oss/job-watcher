"""The DFW rule: is a posting's location in the Dallas/Fort Worth Metroplex?

The city list lives in site/dfw.json so the website applies the exact same rule.
A location is in DFW when it names a listed city together with "TX"/"Texas",
or names a standalone place such as "Fort Worth" or "DFW".
"""

import json
import re
from functools import lru_cache
from pathlib import Path

DFW_FILE = Path(__file__).resolve().parent.parent / "site" / "dfw.json"


def _alternation(names: list[str]) -> str:
    return "|".join(re.escape(n).replace(r"\ ", r"[\s\-]+") for n in sorted(names, key=len, reverse=True))


@lru_cache(maxsize=1)
def _patterns():
    spec = json.loads(DFW_FILE.read_text(encoding="utf-8"))
    city = re.compile(rf"(?<![A-Za-z])({_alternation(spec['cities'])})(?![A-Za-z])", re.IGNORECASE)
    standalone = re.compile(rf"(?<![A-Za-z])({_alternation(spec['standalone'])})(?![A-Za-z])", re.IGNORECASE)
    texas = re.compile(r"(?<![A-Za-z])(TX|(?i:texas))(?![A-Za-z])")  # "TX" must be upper case
    return city, standalone, texas


def in_dfw(location: str) -> bool:
    location = location or ""
    city, standalone, texas = _patterns()
    return bool(standalone.search(location) or (city.search(location) and texas.search(location)))
