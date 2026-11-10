"""The daily pipeline.

    uv run python -m job_watcher.run            # fetch, build, status, issue
    uv run python -m job_watcher.run --no-fetch # rebuild + status from existing raw files

Steps: call every source and save its raw JSON (gzip) under data/raw/<date>/,
record every source's result, rebuild data/history.csv from all raw files,
write data/status.json, then open/update the day's GitHub Issue. The workflow
commits the data afterwards.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import history as H
from .issues import issue_body, publish_issue, site_url
from .sources import FETCHERS, MAX_POSTINGS, SOURCES, SourceError, normalize

STATUS_PATH = H.DATA_DIR / "status.json"
RUNS_DIR = H.DATA_DIR / "runs"


def fetch_source(cfg: dict, date: str) -> dict:
    """Fetch one source and write its raw file. Never raises: returns the result."""
    result = {"name": cfg["name"], "employer": cfg["employer"], "ats": cfg["ats"], "ok": False, "count": 0, "error": ""}
    try:
        payload = FETCHERS[cfg["ats"]](cfg)
        rows = normalize(cfg, payload)  # proves the payload is usable before it is saved
        if not rows:
            raise SourceError("board returned no postings")
        if len(rows) > MAX_POSTINGS and not cfg.get("search"):
            print(f"warning: {cfg['name']} returned {len(rows)} postings; give it a search term", file=sys.stderr)
        envelope = {
            "source": cfg["name"],
            "config": cfg,
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "payload": payload,
        }
        H.write_raw(H.RAW_DIR, date, envelope)
        result.update(ok=True, count=len(rows))
    except Exception as exc:  # one source failing must not stop the run
        result["error"] = f"{type(exc).__name__}: {exc}"[:300]
        traceback.print_exc()
    print(f"{'ok  ' if result['ok'] else 'FAIL'} {cfg['name']:<12} {result['count']:>5}  {result['error']}")
    return result


def fetch_all(date: str) -> list[dict]:
    day_dir = H.RAW_DIR / date
    if day_dir.exists():  # a second run on the same day replaces that day's raw files
        shutil.rmtree(day_dir)
    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(lambda cfg: fetch_source(cfg, date), SOURCES))


def make_status(rows: list[dict], results: list[dict], run_time: str, date: str) -> dict:
    dates = list(H.raw_index(H.RAW_DIR))
    return {
        "run_time": run_time,
        "run_date": date,
        "first_run_date": dates[0] if dates else None,
        "days_with_success": len(dates),
        "open": sum(r["status"] == "open" for r in rows),
        "new_today": sum(r["first_seen"] == date and not r["first_run"] for r in rows),
        "removed_today": sum(r["removed_date"] == date for r in rows),
        "sources": [{k: res[k] for k in ("name", "employer", "ats", "ok", "count", "error")} for res in results],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-fetch", action="store_true", help="skip fetching; use the last run's source results")
    parser.add_argument("--no-issue", action="store_true", help="do not open a GitHub Issue")
    parser.add_argument("--if-missing", action="store_true", help="do nothing if today already has raw files (backup run)")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    run_time, date = now.strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y-%m-%d")
    if args.if_missing and (H.RAW_DIR / date).exists():
        print(f"{date} already has a run; nothing to do")
        return 0

    if args.no_fetch:
        prev = json.loads(STATUS_PATH.read_text()) if STATUS_PATH.exists() else {}
        results = prev.get("sources", [])
        date = prev.get("run_date", date)
    else:
        results = fetch_all(date)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        (RUNS_DIR / f"{date}.json").write_text(json.dumps({"run_time": run_time, "sources": results}, indent=2) + "\n")

    rows = H.build_history()
    H.write_history(rows)
    status = make_status(rows, results, run_time, date)
    STATUS_PATH.write_text(json.dumps(status, indent=2) + "\n")
    print(f"status: open={status['open']} new={status['new_today']} removed={status['removed_today']} "
          f"days={status['days_with_success']}")

    if not args.no_issue:
        new = [r for r in rows if r["first_seen"] == date and not r["first_run"]]
        removed = [r for r in rows if r["removed_date"] == date]
        try:
            publish_issue(date, issue_body(date, status, new, removed, site_url()))
        except Exception:
            traceback.print_exc()  # the issue failing should not lose the day's data
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
