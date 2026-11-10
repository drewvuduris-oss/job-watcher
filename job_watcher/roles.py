"""The title rule: decides whether a posting is in the watched role.

Role: finance analyst - financial analyst, FP&A, strategic/corporate finance,
treasury, investment and credit analyst roles.

A title is in the role when it matches INCLUDE and does not match EXCLUDE.
Matching ignores case.
"""

import re

INCLUDE = re.compile(
    r"""
    \bfp\s*&\s*a\b                       # FP&A, FP & A
    | \bfpa\b
    | financial\s+planning\s*(&|and)\s*analy   # spelled-out FP&A, not "Financial Planning Consultant"
    | \bfinancial\s+analy(st|sis)
    | \bfinance\s+analyst
    | \b(strategic|corporate)\s+finance
    | \bfinance\s+(associate|business\s+partner)
    | \b(treasury|investment|credit|budget|valuation|pricing)\s+analyst
    | \banalyst\b.*\bfinance\b            # "Analyst, Finance" / "Analyst - Corporate Finance"
    """,
    re.IGNORECASE | re.VERBOSE,
)

EXCLUDE = re.compile(
    r"\b(director|vice\s+president|vp|svp|evp|head\s+of|chief|managing\s+director)\b",
    re.IGNORECASE,
)


def in_role(title: str) -> bool:
    title = title or ""
    return bool(INCLUDE.search(title)) and not EXCLUDE.search(title)
