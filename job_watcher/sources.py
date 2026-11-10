"""The watch list and the code that reads each applicant tracking system (ATS).

Each ATS has two functions:

* ``fetch_<ats>(cfg)`` calls the employer's public JSON job board and returns the
  payload exactly as received (a list of pages for boards that paginate).
* ``normalize_<ats>(cfg, payload)`` converts that payload into rows with the
  common columns in ``COMMON_COLUMNS``.

The history build only ever calls the ``normalize_*`` functions, on payloads read
back from ``data/raw``, so the history depends on the raw files alone.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import requests

COMMON_COLUMNS = [
    "posting_id",
    "source",
    "source_id",
    "employer",
    "title",
    "location",
    "department",
    "posted_date",
    "url",
]

# A board that returns more than this many postings must be requested with a
# search term (the `search` key below); the README lists any term in use.
MAX_POSTINGS = 5000

SOURCES: list[dict] = [
    # Workday
    {"name": "tyson", "employer": "Tyson Foods", "ats": "workday", "tenant": "tysonfoods", "host": "wd5", "site": "TSN"},
    {"name": "blackstone", "employer": "Blackstone", "ats": "workday", "tenant": "blackstone", "host": "wd1", "site": "Blackstone_Careers"},
    {"name": "capitalone", "employer": "Capital One", "ats": "workday", "tenant": "capitalone", "host": "wd12", "site": "Capital_One"},
    {"name": "fidelity", "employer": "Fidelity Investments", "ats": "workday", "tenant": "fmr", "host": "wd1", "site": "FidelityCareers"},
    {"name": "mastercard", "employer": "Mastercard", "ats": "workday", "tenant": "mastercard", "host": "wd1", "site": "CorporateCareers"},
    {"name": "statestreet", "employer": "State Street", "ats": "workday", "tenant": "statestreet", "host": "wd1", "site": "Global"},
    # Greenhouse
    {"name": "affirm", "employer": "Affirm", "ats": "greenhouse", "board": "affirm"},
    {"name": "brex", "employer": "Brex", "ats": "greenhouse", "board": "brex"},
    {"name": "carta", "employer": "Carta", "ats": "greenhouse", "board": "carta"},
    {"name": "coinbase", "employer": "Coinbase", "ats": "greenhouse", "board": "coinbase"},
    {"name": "janestreet", "employer": "Jane Street", "ats": "greenhouse", "board": "janestreet"},
    {"name": "point72", "employer": "Point72", "ats": "greenhouse", "board": "point72"},
    {"name": "robinhood", "employer": "Robinhood", "ats": "greenhouse", "board": "robinhood"},
    {"name": "sofi", "employer": "SoFi", "ats": "greenhouse", "board": "sofi"},
    {"name": "stripe", "employer": "Stripe", "ats": "greenhouse", "board": "stripe"},
    {"name": "toast", "employer": "Toast", "ats": "greenhouse", "board": "toast"},
    # Lever
    {"name": "palantir", "employer": "Palantir", "ats": "lever", "board": "palantir"},
    # Ashby
    {"name": "plaid", "employer": "Plaid", "ats": "ashby", "board": "plaid"},
    {"name": "ramp", "employer": "Ramp", "ats": "ashby", "board": "ramp"},
    # SmartRecruiters
    {"name": "servicenow", "employer": "ServiceNow", "ats": "smartrecruiters", "company": "ServiceNow"},
    {"name": "wise", "employer": "Wise", "ats": "smartrecruiters", "company": "Wise"},
]

HEADERS = {
    "User-Agent": "job-watcher/0.1 (course project; daily read of public job boards)",
    "Accept": "application/json",
}
TIMEOUT = 45


class SourceError(Exception):
    """A source could not be read or returned something unusable."""


# --------------------------------------------------------------------------- helpers

def _request(method: str, url: str, *, json_body=None, params=None, tries: int = 3):
    last = None
    for attempt in range(tries):
        try:
            resp = requests.request(method, url, json=json_body, params=params, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 429 or resp.status_code >= 500:
                raise SourceError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError, SourceError) as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise SourceError(f"{method} {url} failed: {last}")


def iso_to_utc_date(value) -> str:
    """ISO-8601 timestamp (any offset) or epoch milliseconds -> 'YYYY-MM-DD' in UTC."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _clean(value) -> str:
    return " ".join(str(value or "").split())


def _row(cfg: dict, source_id, title, location="", department="", posted_date="", url="") -> dict:
    source_id = _clean(source_id)
    return {
        "posting_id": f"{cfg['name']}:{source_id}",
        "source": cfg["name"],
        "source_id": source_id,
        "employer": cfg["employer"],
        "title": _clean(title),
        "location": _clean(location),
        "department": _clean(department),
        "posted_date": posted_date,
        "url": url or "",
    }


# --------------------------------------------------------------------------- Workday

WORKDAY_PAGE = 20  # Workday's public endpoint rejects larger pages


def workday_base(cfg: dict) -> str:
    return f"https://{cfg['tenant']}.{cfg['host']}.myworkdayjobs.com"


def fetch_workday(cfg: dict) -> dict:
    url = f"{workday_base(cfg)}/wday/cxs/{cfg['tenant']}/{cfg['site']}/jobs"
    pages, offset, total = [], 0, None
    while True:
        body = {"appliedFacets": {}, "limit": WORKDAY_PAGE, "offset": offset, "searchText": cfg.get("search", "")}
        page = _request("POST", url, json_body=body)
        if total is None:  # Workday only reports the total on the first page
            total = int(page.get("total") or 0)
        pages.append(page)
        got = len(page.get("jobPostings") or [])
        offset += WORKDAY_PAGE
        if got == 0 or offset >= total:
            break
        time.sleep(0.25)
    return {"total": total, "pages": pages}


def workday_id(external_path: str) -> str:
    """'/job/City/Title_R0491576-2' -> 'R0491576-2' (falls back to the whole path)."""
    last = external_path.rstrip("/").rsplit("/", 1)[-1]
    return last.rsplit("_", 1)[-1] if "_" in last else external_path


def normalize_workday(cfg: dict, payload: dict) -> list[dict]:
    rows = []
    for page in payload.get("pages", []):
        for job in page.get("jobPostings") or []:
            path = job.get("externalPath")
            if not path:
                continue
            rows.append(_row(
                cfg,
                source_id=workday_id(path),
                title=job.get("title"),
                location=job.get("locationsText"),
                url=f"{workday_base(cfg)}/en-US/{cfg['site']}{path}",
            ))
    return rows


# --------------------------------------------------------------------------- Greenhouse

def fetch_greenhouse(cfg: dict) -> dict:
    return _request("GET", f"https://boards-api.greenhouse.io/v1/boards/{cfg['board']}/jobs")


def normalize_greenhouse(cfg: dict, payload: dict) -> list[dict]:
    rows = []
    for job in payload.get("jobs", []):
        department = ""
        for meta in job.get("metadata") or []:
            if (meta.get("name") or "").lower() in ("job post department", "department") and isinstance(meta.get("value"), str):
                department = meta["value"]
                break
        rows.append(_row(
            cfg,
            source_id=job.get("id"),
            title=job.get("title"),
            location=(job.get("location") or {}).get("name"),
            department=department,
            posted_date=iso_to_utc_date(job.get("first_published")),
            url=job.get("absolute_url"),
        ))
    return rows


# --------------------------------------------------------------------------- Lever

def fetch_lever(cfg: dict) -> list:
    return _request("GET", f"https://api.lever.co/v0/postings/{cfg['board']}", params={"mode": "json"})


def normalize_lever(cfg: dict, payload: list) -> list[dict]:
    rows = []
    for job in payload:
        cats = job.get("categories") or {}
        rows.append(_row(
            cfg,
            source_id=job.get("id"),
            title=job.get("text"),
            location=cats.get("location"),
            department=cats.get("department") or cats.get("team"),
            posted_date=iso_to_utc_date(job.get("createdAt")),
            url=job.get("hostedUrl"),
        ))
    return rows


# --------------------------------------------------------------------------- Ashby

def fetch_ashby(cfg: dict) -> dict:
    return _request("GET", f"https://api.ashbyhq.com/posting-api/job-board/{cfg['board']}")


def normalize_ashby(cfg: dict, payload: dict) -> list[dict]:
    return [
        _row(
            cfg,
            source_id=job.get("id"),
            title=job.get("title"),
            location=job.get("location"),
            department=job.get("department"),
            posted_date=iso_to_utc_date(job.get("publishedAt")),
            url=job.get("jobUrl"),
        )
        for job in payload.get("jobs", [])
    ]


# --------------------------------------------------------------------------- SmartRecruiters

SR_PAGE = 100


def fetch_smartrecruiters(cfg: dict) -> dict:
    url = f"https://api.smartrecruiters.com/v1/companies/{cfg['company']}/postings"
    pages, offset = [], 0
    while True:
        params = {"limit": SR_PAGE, "offset": offset}
        if cfg.get("search"):
            params["q"] = cfg["search"]
        page = _request("GET", url, params=params)
        pages.append(page)
        offset += SR_PAGE
        if not page.get("content") or offset >= int(page.get("totalFound") or 0):
            break
        time.sleep(0.25)
    return {"pages": pages}


def _sr_location(loc: dict) -> str:
    parts = [p.strip() for p in (loc.get("fullLocation") or "").split(",") if p.strip()]
    if not parts:
        parts = [p for p in (loc.get("city"), loc.get("region"), (loc.get("country") or "").upper()) if p]
    return ", ".join(parts)


def normalize_smartrecruiters(cfg: dict, payload: dict) -> list[dict]:
    rows = []
    for page in payload.get("pages", []):
        for job in page.get("content") or []:
            rows.append(_row(
                cfg,
                source_id=job.get("id"),
                title=job.get("name"),
                location=_sr_location(job.get("location") or {}),
                department=(job.get("department") or {}).get("label"),
                posted_date=iso_to_utc_date(job.get("releasedDate")),
                url=f"https://jobs.smartrecruiters.com/{cfg['company']}/{job.get('id')}",
            ))
    return rows


# --------------------------------------------------------------------------- dispatch

FETCHERS = {
    "workday": fetch_workday,
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
}
NORMALIZERS = {
    "workday": normalize_workday,
    "greenhouse": normalize_greenhouse,
    "lever": normalize_lever,
    "ashby": normalize_ashby,
    "smartrecruiters": normalize_smartrecruiters,
}


def normalize(cfg: dict, payload) -> list[dict]:
    """Common-column rows for one source's payload, de-duplicated by posting_id."""
    rows = NORMALIZERS[cfg["ats"]](cfg, payload)
    unique = {}
    for row in rows:
        if row["source_id"]:
            unique[row["posting_id"]] = row
    return list(unique.values())
