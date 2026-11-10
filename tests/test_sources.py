"""Conversion of each ATS payload to the common columns."""

from job_watcher.sources import COMMON_COLUMNS, iso_to_utc_date, normalize, workday_id

WD = {"name": "tyson", "employer": "Tyson Foods", "ats": "workday", "tenant": "tysonfoods", "host": "wd5", "site": "TSN"}
GH = {"name": "brex", "employer": "Brex", "ats": "greenhouse", "board": "brex"}
LV = {"name": "palantir", "employer": "Palantir", "ats": "lever", "board": "palantir"}
AB = {"name": "ramp", "employer": "Ramp", "ats": "ashby", "board": "ramp"}
SR = {"name": "wise", "employer": "Wise", "ats": "smartrecruiters", "company": "Wise"}


def check_columns(rows):
    for row in rows:
        assert list(row) == COMMON_COLUMNS


def test_workday():
    payload = {"total": 3, "pages": [
        {"total": 3, "jobPostings": [
            {"title": "Financial Analyst ", "externalPath": "/job/Springdale-AR/Financial-Analyst_R0491576-2",
             "locationsText": "Springdale, Arkansas", "postedOn": "Posted Today", "bulletFields": ["R0491576"]},
            {"title": "Plant Manager", "externalPath": "/job/Dakota-City/Plant-Manager_R0400001",
             "locationsText": "2 Locations", "postedOn": "Posted 30+ Days Ago"},
        ]},
        {"total": 0, "jobPostings": [
            # repeated across pages: kept once
            {"title": "Plant Manager", "externalPath": "/job/Dakota-City/Plant-Manager_R0400001", "locationsText": "2 Locations"},
        ]},
    ]}
    rows = normalize(WD, payload)
    check_columns(rows)
    assert len(rows) == 2
    first = rows[0]
    assert first == {
        "posting_id": "tyson:R0491576-2",
        "source": "tyson",
        "source_id": "R0491576-2",
        "employer": "Tyson Foods",
        "title": "Financial Analyst",
        "location": "Springdale, Arkansas",
        "department": "",
        "posted_date": "",  # Workday gives only "Posted Today"-style text
        "url": "https://tysonfoods.wd5.myworkdayjobs.com/en-US/TSN/job/Springdale-AR/Financial-Analyst_R0491576-2",
    }


def test_workday_id():
    assert workday_id("/job/A/B_R123") == "R123"
    assert workday_id("/job/A/B_C_JR-55-1") == "JR-55-1"
    assert workday_id("/job/A/NoUnderscore") == "/job/A/NoUnderscore"


def test_greenhouse():
    payload = {"jobs": [{
        "id": 8912603002, "title": "FP&A Analyst", "absolute_url": "https://www.brex.com/careers/8912603002",
        "location": {"name": "New York, New York, United States"},
        "metadata": [{"name": "Job Post Department", "value": "Finance", "value_type": "single_select"}],
        "first_published": "2026-10-23T22:03:40-04:00",
    }, {
        "id": 5, "title": "Engineer", "absolute_url": "https://x/5", "location": None, "metadata": None,
    }]}
    rows = normalize(GH, payload)
    check_columns(rows)
    assert rows[0]["posting_id"] == "brex:8912603002"
    assert rows[0]["department"] == "Finance"
    assert rows[0]["location"] == "New York, New York, United States"
    assert rows[0]["posted_date"] == "2026-10-24"  # converted to UTC
    assert rows[1]["location"] == "" and rows[1]["department"] == "" and rows[1]["posted_date"] == ""


def test_lever():
    payload = [{
        "id": "6ed76ce8", "text": "Strategic Finance Associate", "createdAt": 1786469891368,
        "categories": {"location": "Denver, CO", "team": "Finance", "commitment": "Full-time"},
        "hostedUrl": "https://jobs.lever.co/palantir/6ed76ce8",
    }]
    (row,) = normalize(LV, payload)
    check_columns([row])
    assert row["posting_id"] == "palantir:6ed76ce8"
    assert row["title"] == "Strategic Finance Associate"
    assert row["location"] == "Denver, CO"
    assert row["department"] == "Finance"
    assert row["posted_date"] == "2026-08-11"
    assert row["url"] == "https://jobs.lever.co/palantir/6ed76ce8"


def test_ashby():
    payload = {"jobs": [{
        "id": "34413f8d", "title": " Finance Analyst", "department": "Finance", "location": "New York, NY (HQ)",
        "publishedAt": "2026-04-07T17:12:35.753+00:00", "jobUrl": "https://jobs.ashbyhq.com/ramp/34413f8d",
    }]}
    (row,) = normalize(AB, payload)
    check_columns([row])
    assert row["posting_id"] == "ramp:34413f8d"
    assert row["title"] == "Finance Analyst"
    assert row["posted_date"] == "2026-04-07"
    assert row["url"] == "https://jobs.ashbyhq.com/ramp/34413f8d"


def test_smartrecruiters():
    payload = {"pages": [
        {"totalFound": 2, "content": [
            {"id": "744000160927829", "name": "Treasury Analyst", "releasedDate": "2026-11-10T16:51:40.735Z",
             "location": {"city": "London", "country": "gb", "fullLocation": "London, , United Kingdom"},
             "department": {}},
            {"id": "744000160927830", "name": "Engineer", "releasedDate": "2026-11-09T01:00:00Z",
             "location": {"city": "Austin", "region": "TX", "country": "us"}, "department": {"label": "Engineering"}},
        ]},
    ]}
    rows = normalize(SR, payload)
    check_columns(rows)
    assert rows[0]["location"] == "London, United Kingdom"
    assert rows[0]["department"] == ""
    assert rows[0]["url"] == "https://jobs.smartrecruiters.com/Wise/744000160927829"
    assert rows[1]["location"] == "Austin, TX, US"
    assert rows[1]["department"] == "Engineering"
    assert rows[1]["posted_date"] == "2026-11-09"


def test_iso_to_utc_date():
    assert iso_to_utc_date("2026-01-01T23:30:00-05:00") == "2026-01-02"
    assert iso_to_utc_date("2026-01-01") == "2026-01-01"
    assert iso_to_utc_date(None) == ""
    assert iso_to_utc_date("not a date") == ""


OR = {"name": "ti", "employer": "Texas Instruments", "ats": "oracle", "host": "edbz.fa.us2.oraclecloud.com", "site": "CX"}


def test_oracle():
    payload = {"pages": [
        {"items": [{"TotalJobsCount": 2, "requisitionList": [
            {"Id": "25019826", "Title": "Financial Analyst", "PostedDate": "2026-11-10",
             "PrimaryLocation": "Dallas, TX, United States", "Department": None, "Organization": "Finance"},
            {"Id": "25010729", "Title": "Field Applications Engineer", "PostedDate": "2026-06-16",
             "PrimaryLocation": "Shenzhen, Guangdong, China"},
        ]}]},
        {"items": [{"TotalJobsCount": 2, "requisitionList": []}]},
    ]}
    rows = normalize(OR, payload)
    check_columns(rows)
    assert len(rows) == 2
    assert rows[0] == {
        "posting_id": "ti:25019826",
        "source": "ti",
        "source_id": "25019826",
        "employer": "Texas Instruments",
        "title": "Financial Analyst",
        "location": "Dallas, TX, United States",
        "department": "Finance",
        "posted_date": "2026-11-10",
        "url": "https://edbz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/25019826",
    }
    assert rows[1]["department"] == ""
