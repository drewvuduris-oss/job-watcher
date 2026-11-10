# Job Watcher

[![Tests](https://github.com/drewvuduris-oss/job-watcher/actions/workflows/tests.yml/badge.svg)](https://github.com/drewvuduris-oss/job-watcher/actions/workflows/tests.yml)
[![Daily run](https://github.com/drewvuduris-oss/job-watcher/actions/workflows/daily.yml/badge.svg)](https://github.com/drewvuduris-oss/job-watcher/actions/workflows/daily.yml)

A tool that watches the job market for **finance-analyst roles** (financial analyst, FP&A,
strategic/corporate finance, treasury, investment and credit analyst), with a focus on the
**Dallas/Fort Worth Metroplex**. Once a day GitHub Actions pulls every open posting from 36
employers' job boards (15 of them headquartered in DFW), compares them with the day
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
| `att` | AT&T (Dallas) | Workday | `att.wd1.myworkdayjobs.com/wday/cxs/att/ATTGeneral/jobs` |
| `alcon` | Alcon (Fort Worth) | Workday | `alcon.wd5.myworkdayjobs.com/wday/cxs/alcon/careers_alcon/jobs` |
| `alkami` | Alkami Technology (Plano) | Workday | `alkami.wd12.myworkdayjobs.com/wday/cxs/alkami/Alkami/jobs` |
| `atmos` | Atmos Energy (Dallas) | Workday | `atmosenergy.wd108.myworkdayjobs.com/wday/cxs/atmosenergy/External_Career_Site/jobs` |
| `goosehead` | Goosehead Insurance (Westlake) | Workday | `goosehead.wd503.myworkdayjobs.com/wday/cxs/goosehead/Careers/jobs` |
| `kimberlyclark` | Kimberly-Clark (Irving) | Workday | `kimberlyclark.wd1.myworkdayjobs.com/wday/cxs/kimberlyclark/GLOBAL/jobs` |
| `mckesson` | McKesson (Irving) | Workday | `mckesson.wd3.myworkdayjobs.com/wday/cxs/mckesson/External_Careers/jobs` |
| `sabre` | Sabre (Southlake) | Workday | `sabre.wd1.myworkdayjobs.com/wday/cxs/sabre/SabreJobs/jobs` |
| `texascapital` | Texas Capital (Dallas) | Workday | `texascapitalbank.wd12.myworkdayjobs.com/wday/cxs/texascapitalbank/Careers/jobs` |
| `toyota` | Toyota North America (Plano) | Workday | `toyota.wd503.myworkdayjobs.com/wday/cxs/toyota/TMNA/jobs` |
| `vistra` | Vistra (Irving) | Workday | `vst.wd5.myworkdayjobs.com/wday/cxs/vst/vistra_careers/jobs` |
| `vizient` | Vizient (Irving) | Workday | `vizient.wd1.myworkdayjobs.com/wday/cxs/vizient/vizient_careers/jobs` |
| `ti` | Texas Instruments (Dallas) | Oracle Recruiting Cloud | `edbz.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions` (site `CX`) |
| `tenet` | Tenet Healthcare (Dallas) | Oracle Recruiting Cloud | `eodr.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions` (site `CX_1001`) |
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
| `matchgroup` | Match Group (Dallas) | Lever | `api.lever.co/v0/postings/matchgroup?mode=json` |
| `plaid` | Plaid | Ashby | `api.ashbyhq.com/posting-api/job-board/plaid` |
| `ramp` | Ramp | Ashby | `api.ashbyhq.com/posting-api/job-board/ramp` |
| `servicenow` | ServiceNow | SmartRecruiters | `api.smartrecruiters.com/v1/companies/ServiceNow/postings` |
| `wise` | Wise | SmartRecruiters | `api.smartrecruiters.com/v1/companies/Wise/postings` |

**Search terms:** no board currently returns more than 5,000 postings, so every board is
requested in full with no search term. (A board over the limit would get a `search` key in
`job_watcher/sources.py`, sent as Workday's `searchText`, SmartRecruiters' `q` or Oracle's
`keyword`, and listed here.) The largest board is Tenet Healthcare at about 3,000 postings.

Walmart, J.B. Hunt, Dillard's and Wells Fargo were tried first; their Workday boards reject
anonymous requests (HTTP 422), so they were replaced. DFW employers on systems with no public
JSON board (American Airlines, Southwest, Charles Schwab on iCIMS, D.R. Horton on Taleo, Keurig
Dr Pepper on Eightfold, among others) are left out.

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

## DFW rule

A posting is in the **Dallas/Fort Worth Metroplex** when its location names a Metroplex city
(Dallas, Fort Worth, Arlington, Plano, Irving, Frisco, McKinney, Richardson, Westlake, Southlake
and ~80 more) together with `TX` or `Texas`, or names a place that is unambiguous on its own
("Fort Worth", "DFW", "Dallas-Fort Worth", "Las Colinas", "North Dallas", "Southlake"). The list
is `site/dfw.json`; the browser and `job_watcher/regions.py` both apply it, so the site and the
daily issue agree. "Dallas" with no state is not counted (there is a Dallas, GA), nor are
postings listed only as "2 Locations" or "Remote". The rule is a view on the data: it does not
change `history.csv`, whose columns are fixed.

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
   postings with links (⭐ in role, 📍 in DFW, both listed first), and closes the previous day's issue. It is opened even when nothing
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

* **Today** (`index.html`) — last run time, status of every source, the four counts plus open
  postings in DFW, and the lists of new and removed postings (filterable to role and DFW).
* **Browse** (`browse.html`) — open postings: role/all switch (role is the default), a
  DFW Metroplex / anywhere switch (DFW is the default), filters
  for employer, location and days open, title search, sort by first seen, apply links, and a
  ★ shortlist saved in the browser's `localStorage`.
* **Market** (`market.html`) — six findings computed in the browser from `history.csv`:
  new postings per day (all and in role), removed per day, open postings per employer,
  median days open, share removed within seven days, top locations, and a seventh section on
  the DFW Metroplex (open postings by employer and by city).

The site is an installable app (web manifest + service worker). The service worker fetches
pages and data from the network when online and serves the last saved copies when offline.

## Files

| Path | What it does |
|---|---|
| `job_watcher/sources.py` | Watch list; fetch and normalize functions for Workday, Oracle Recruiting Cloud, Greenhouse, Lever, Ashby and SmartRecruiters |
| `job_watcher/roles.py` | The title rule (`in_role`) |
| `job_watcher/regions.py` | The DFW location rule (used to mark DFW postings in the daily issue) |
| `job_watcher/history.py` | Reads/writes raw files; builds `data/history.csv` from them (`python -m job_watcher.history`) |
| `job_watcher/issues.py` | Writes the daily issue and opens/updates/closes issues via the GitHub API |
| `job_watcher/run.py` | The daily pipeline (fetch → raw files → history → status → issue) |
| `tests/test_sources.py` | Conversion of each ATS to the common columns |
| `tests/test_roles.py` | The title rule |
| `tests/test_regions.py` | The DFW location rule |
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
| `site/dfw.json` | The DFW city list, shared by the site and `regions.py` |
| `site/sw.js` | Service worker (network first, cache fallback) |
| `site/manifest.webmanifest`, `site/icons/` | Web app manifest and icons |
| `site/vendor/` | Chart.js 4.4.1 and PapaParse 5.4.1, kept locally so the site works offline |
| `pyproject.toml`, `uv.lock`, `.python-version` | Python project and locked dependencies (managed by uv) |
| `.gitattributes`, `.gitignore` | LF line endings (so builds match across systems); ignored files |
