"""The title rule."""

import pytest

from job_watcher.roles import in_role


@pytest.mark.parametrize("title", [
    "Financial Analyst",
    "Senior Financial Analyst, Corporate Finance & Strategy",
    "FP&A Analyst",
    "Finance (FP & A) Senior Analyst",
    "Manager, Financial Planning & Analysis",
    "Financial Planning and Analysis Associate",
    "Associate, Strategic Finance",
    "Finance Associate",
    "Senior Analyst - Finance Business Partner",
    "Treasury Analyst",
    "Credit Analyst II",
    "2027 Investment Analyst Summer Internship",
    "Analyst, Corporate Finance",
    "Principal Associate, Financial Analysis",
])
def test_in_role(title):
    assert in_role(title)


@pytest.mark.parametrize("title", [
    "Software Engineer",
    "Financial Planning Consultant - Westlake, TX",  # advisor job, not FP&A
    "Financial Consultant",
    "Director, FP&A",                                 # too senior
    "Vice President, Financial Analysis",
    "Head of Strategic Finance",
    "Chief Financial Officer",
    "Accountant",
    "Maintenance Generalist- FP- D shift",            # 'FP' alone is not FP&A
    "",
])
def test_not_in_role(title):
    assert not in_role(title)


def test_case_insensitive():
    assert in_role("FINANCIAL ANALYST") and in_role("fp&a analyst")
