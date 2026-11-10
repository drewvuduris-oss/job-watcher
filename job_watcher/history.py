"""Build data/history.csv from the raw files in data/raw, day by day.

The build reads nothing but the raw files, so running it again gives the same
file, and a change to a normalizer or to the title rule applies to every day.

    uv run python -m job_watcher.history
"""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

from .roles import in_role
from .sources import COMMON_COLUMNS, normalize

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
HISTORY_PATH = DATA_DIR / "history.csv"

HISTORY_COLUMNS = COMMON_COLUMNS + [
    "in_role",
    "first_run",
    "first_seen",
    "last_seen",
    "status",
    "removed_date",
]


# --------------------------------------------------------------------------- raw files

def raw_path(raw_dir: Path, date: str, source: str) -> Path:
    return raw_dir / date / f"{source}.json.gz"


def write_raw(raw_dir: Path, date: str, envelope: dict) -> Path:
    path = raw_path(raw_dir, date, envelope["source"])
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(envelope, ensure_ascii=False, sort_keys=True).encode("utf-8")
    # mtime=0 keeps the gzip bytes identical for identical content
    with open(path, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(data)
    return path


def read_raw(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def raw_index(raw_dir: Path) -> dict[str, dict[str, Path]]:
    """{date: {source: path}} for every raw file, dates in order."""
    index: dict[str, dict[str, Path]] = {}
    if not raw_dir.exists():
        return index
    for day in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        files = {f.name.removesuffix(".json.gz"): f for f in sorted(day.glob("*.json.gz"))}
        if files:
            index[day.name] = files
    return index


# --------------------------------------------------------------------------- history rules

def apply_day(history: dict[str, dict], date: str, source: str, rows: list[dict], first_file: bool) -> None:
    """Fold one source's postings for one day into ``history`` (posting_id -> row).

    * a posting seen for the first time gets ``date`` as first_seen
    * every posting listed today gets ``date`` as last_seen
    * an open posting of this source that is not listed today is removed today
    * a removed posting that is listed again re-opens; first_seen is kept
    """
    listed = set()
    for row in rows:
        pid = row["posting_id"]
        listed.add(pid)
        rec = history.get(pid)
        if rec is None:
            rec = {**row, "first_run": first_file, "first_seen": date, "status": "open", "removed_date": ""}
            history[pid] = rec
        else:
            rec.update(row)  # keep the latest title, location, url, ...
            if rec["status"] == "removed":
                rec["status"] = "open"
                rec["removed_date"] = ""
        rec["last_seen"] = date

    for pid, rec in history.items():
        if rec["source"] == source and rec["status"] == "open" and pid not in listed:
            rec["status"] = "removed"
            rec["removed_date"] = date


def build_history(raw_dir: Path = RAW_DIR) -> list[dict]:
    history: dict[str, dict] = {}
    seen_sources: set[str] = set()
    for date, files in raw_index(raw_dir).items():
        for source, path in files.items():
            envelope = read_raw(path)
            rows = normalize(envelope["config"], envelope["payload"])
            apply_day(history, date, source, rows, first_file=source not in seen_sources)
            seen_sources.add(source)

    out = []
    for pid in sorted(history):
        rec = history[pid]
        rec["in_role"] = in_role(rec["title"])
        out.append(rec)
    return out


# --------------------------------------------------------------------------- csv

def _cell(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)


def write_history(rows: list[dict], path: Path = HISTORY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(HISTORY_COLUMNS)
        for rec in rows:
            writer.writerow([_cell(rec.get(col)) for col in HISTORY_COLUMNS])


def read_history(path: Path = HISTORY_PATH) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    rows = build_history()
    write_history(rows)
    print(f"history: {len(rows)} postings -> {HISTORY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
