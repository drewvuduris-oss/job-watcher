# Job Watcher

[![Tests](https://github.com/drewvuduris-oss/job-watcher/actions/workflows/tests.yml/badge.svg)](https://github.com/drewvuduris-oss/job-watcher/actions/workflows/tests.yml)
[![Daily run](https://github.com/drewvuduris-oss/job-watcher/actions/workflows/daily.yml/badge.svg)](https://github.com/drewvuduris-oss/job-watcher/actions/workflows/daily.yml)

A tool that watches the job market for **finance-analyst roles** (financial analyst, FP&A,
strategic/corporate finance, treasury, investment and credit analyst). Once a day GitHub
Actions pulls every open posting from 21 employers' job boards, compares them with the day
before, records what is new and what is gone, opens a GitHub Issue with the changes, and
publishes the result to a website.

**Site:** https://drewvuduris-oss.github.io/job-watcher/

## Sources

Every board is read through the public JSON API of the applicant tracking system (ATS) that
hosts it — no login, no HTML scraping. All postings are kept, not only those in the role.

| Source | Employer | ATS | Endpoint |
|---|---|---|---|
| `tyson` | Tyson Foods | Workday | `tysonfoods.wd5.myworkdayjobs.com/wday/cxs/tysonfoods/TSN/jobs` |
| `blackstone` | Blackstone | Workday | `blackstone.wd1.myworkdayjobs.com/wday/cxs/blackstone/Blackstone_Careers/jobs` |
| `capitalone` | Capital One | Workday | `capitalone.wd12.myworkdayjobs.com/wday/cxs/capitalone/Capital_One/jobs` |
| `fidelity` | Fidelity Investments | Workday | `fmr.wd1.myworkdayjobs.com/wday/cxs/fmr/FidelityCareers/jobs` |
| `mastercard` | Mastercard | Workday | `mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs` |
| `statestreet` | State Street | Workday | `statestreet.wd1.myworkdayjobs.com/wday/cxs/statestreet/Global/jobs` |
| `affirm` | Affirm | Greenhouse | `boards-api.greenhouse.io/v1/boards/affirm/jobs` |
| `brex` | Brex | Greenhouse | `boards-api.greenhouse.io/v1/boards/brex/jobs` |
| `carta` | Carta | Greenhouse | `boards-api.greenhouse.io/v1/boards/carta/jobs` |
| `coinbase` | Coinbase | Greenhouse | `boards-api.greenhouse.io/v1/boards/coinbase/jobs` |
| `janestreet` | Jane Street | Greenhouse | `boards-api.greenhouse.io/v1/boards/janestreet/jobs` |
| `point72` | Point72 | Greenhouse | `boards-api.greenhouse.io/v1/boards/point72/jobs` |
| `robinhood` | Robinhood | Greenhouse | `boards-api.greenhouse.io/v1/boards/robinhood/jobs` |
| `sofi` | SoFi | Greenhouse | `boards-api.greenhouse.io/v1/boards/sofi/jobs` |
| `stripe` | Stripe | Greenhouse | `boards-api.greenhouse.io/v1/boards/stripe/jobs` |
| `toast` | Toast | Greenhouse | `boards-api.greenhouse.io/v1/boards/toast/jobs` |
| `palantir` | Palantir | Lever | `api.lever.co/v0/postings/palantir?mode=json` |
| `plaid` | Plaid | Ashby | `api.ashbyhq.com/posting-api/job-board/plaid` |
| `ramp` | Ramp | Ashby | `api.ashbyhq.com/posting-api/job-board/ramp` |
| `servicenow` | ServiceNow | SmartRecruiters | `api.smartrecruiters.com/v1/companies/ServiceNow/postings` |
| `wise` | Wise | SmartRecruiters | `api.smartrecruiters.com/v1/companies/Wise/postings` |

**Search terms:** no board currently returns more than 5,000 postings, so every board is
requested in full with no search term. (A board over the limit would get a `search` key in
`job_watcher/sources.py`, sent as Workday's `searchText` or SmartRecruiters' `q`, and listed here.)

Walmart, J.B. Hunt, Dillard's and Wells Fargo were tried first; their Workday boards reject
anonymous requests (HTTP 422), so they were replaced.

What each source provides: Workday gives no department or absolute posted date (only
"Posted 3 Days Ago"), so those columns are empty for Workday rows. Greenhouse department
comes from the "Job Post Department" metadata field when the board sets it.

## Title rule

A posting is **in the role** (`in_role = true`) when its title matches the include pattern
and does not match the exclude pattern (case-insensitive; see `job_watcher/roles.py`):

* **Include** any of: `FP&A` / `FP & A` / `FPA`; "financial planning & analysis";
  "financial analyst" / "financial analysis"; "finance analyst"; "strategic finance" /
  "corporate finance"; "finance associate" / "finance business partner"; "treasury",
  "investment", "credit", "budget", "valuation" or "pricing" followed by "analyst"; or
  "analyst" followed later by "finance" (e.g. "Analyst, Corporate Finance").
* **Exclude** senior leadership: director, vice president, VP/SVP/EVP, head of, chief,
  managing director.

## How it works

Each daily run (`.github/workflows/daily.yml`):

1. Runs the tests, then calls every source and saves its response, gzip-compressed, to
   `data/raw/<date>/<source>.json.gz`. A source that fails (error, timeout, empty board)
   writes no raw file; every source's result is recorded in `data/runs/<date>.json` and in
   `data/status.json`. One failure never stops the run.
2. Rebuilds `data/history.csv` from **all** raw files, day by day (and checks that a second
   build is byte-identical).
3. Writes `data/status.json`.
4. Opens a GitHub Issue titled with the date (label `daily-report`) listing new and removed
   postings with links, and closes the previous day's issue. It is opened even when nothing
   changed.
5. Commits the data, then redeploys the site to GitHub Pages.

A second run on the same day deletes and replaces that day's raw files, rebuilds the history
and updates that day's issue, so each day counts once. A backup schedule at 19:47 UTC runs
only if the 11:23 UTC run did not produce a raw folder for the day.

History rules, applied day by day, per source: a posting seen for the first time gets that
day as `first_seen`; every posting listed that day gets it as `last_seen`; an open posting is
marked `removed` with that day's `removed_date` when its source has a raw file that day and
no longer lists it; a removed posting that is listed again re-opens with `removed_date`
cleared and `first_seen` kept. `first_run` is true for postings in a source's first raw file.

### Build the history from the raw files

```sh
uv run python -m job_watcher.history
```

Other commands:

```sh
uv sync                                 # install dependencies
uv run python -m job_watcher.run        # full pipeline: fetch, build, status, issue
uv run python -m job_watcher.run --no-fetch --no-issue   # rebuild history + status only
uv run pytest                           # tests
```

Preview the site locally:

```sh
mkdir -p _site/data && cp -r site/* _site/ && cp data/history.csv data/status.json _site/data/
uv run python -m http.server 8000 -d _site   # open http://localhost:8000
```

## Data files

* **`data/history.csv`** — one row per posting, sorted by `posting_id`: `posting_id`
  (`<source>:<source_id>`), `source`, `source_id`, `employer`, `title`, `location`,
  `department`, `posted_date`, `url`, `in_role`, `first_run`, `first_seen`, `last_seen`,
  `status` (`open`/`removed`), `removed_date`. Dates are UTC `YYYY-MM-DD`.
* **`data/status.json`** — the latest run: `run_time` (UTC), `run_date`, `first_run_date`,
  `days_with_success`, `open`, `new_today`, `removed_today` and `sources` (`name`,
  `employer`, `ats`, `ok`, `count`, `error`).

## Site

* **Today** (`index.html`) — last run time, status of every source, the four counts and the
  lists of new and removed postings.
* **Browse** (`browse.html`) — open postings: role/all switch (role is the default), filters
  for employer, location and days open, title search, sort by first seen, apply links, and a
  ★ shortlist saved in the browser's `localStorage`.
* **Market** (`market.html`) — six findings computed in the browser from `history.csv`:
  new postings per day (all and in role), removed per day, open postings per employer,
  median days open, share removed within seven days, and top locations.

The site is an installable app (web manifest + service worker). The service worker fetches
pages and data from the network when online and serves the last saved copies when offline.

## Files

| Path | What it does |
|---|---|
| `job_watcher/sources.py` | Watch list; fetch and normalize functions for Workday, Greenhouse, Lever, Ashby and SmartRecruiters |
| `job_watcher/roles.py` | The title rule (`in_role`) |
| `job_watcher/history.py` | Reads/writes raw files; builds `data/history.csv` from them (`python -m job_watcher.history`) |
| `job_watcher/issues.py` | Writes the daily issue and opens/updates/closes issues via the GitHub API |
| `job_watcher/run.py` | The daily pipeline (fetch → raw files → history → status → issue) |
| `tests/test_sources.py` | Conversion of each ATS to the common columns |
| `tests/test_roles.py` | The title rule |
| `tests/test_history.py` | First-seen, last-seen, removed and re-open logic; build from raw files is reproducible |
| `.github/workflows/daily.yml` | Scheduled daily run: tests, pipeline, commit, deploy |
| `.github/workflows/tests.yml` | Runs pytest on every push |
| `.github/workflows/pages.yml` | Assembles `site/` + data files and deploys to GitHub Pages |
| `data/raw/<date>/<source>.json.gz` | Raw responses, one file per successful source per day |
| `data/runs/<date>.json` | Every source's result (ok, count, error) for each run |
| `data/history.csv` | The history file |
| `data/status.json` | The status file |
| `site/index.html`, `site/today.js` | Today page |
| `site/browse.html`, `site/browse.js` | Browse page |
| `site/market.html`, `site/market.js` | Market page |
| `site/common.js` | Shared navigation bar, data loading, date helpers, shortlist, service-worker registration |
| `site/styles.css` | Shared fonts and colors (light and dark) |
| `site/sw.js` | Service worker (network first, cache fallback) |
| `site/manifest.webmanifest`, `site/icons/` | Web app manifest and icons |
| `site/vendor/` | Chart.js 4.4.1 and PapaParse 5.4.1, kept locally so the site works offline |
| `pyproject.toml`, `uv.lock`, `.python-version` | Python project and locked dependencies (managed by uv) |
| `.gitattributes`, `.gitignore` | LF line endings (so builds match across systems); ignored files |
