"""First-seen, last-seen and removed logic, and the build from raw files."""

import csv

from job_watcher.history import (
    HISTORY_COLUMNS,
    apply_day,
    build_history,
    write_history,
    write_raw,
)

CFG = {"name": "acme", "employer": "Acme", "ats": "greenhouse", "board": "acme"}
OTHER = {"name": "beta", "employer": "Beta", "ats": "ashby", "board": "beta"}


def row(pid, title="Financial Analyst", source="acme"):
    return {"posting_id": f"{source}:{pid}", "source": source, "source_id": str(pid), "employer": "Acme",
            "title": title, "location": "", "department": "", "posted_date": "", "url": f"https://x/{pid}"}


def test_first_seen_and_last_seen():
    h = {}
    apply_day(h, "2026-11-01", "acme", [row(1), row(2)], first_file=True)
    apply_day(h, "2026-11-02", "acme", [row(1), row(2), row(3)], first_file=False)
    assert h["acme:1"]["first_seen"] == "2026-11-01" and h["acme:1"]["last_seen"] == "2026-11-02"
    assert h["acme:3"]["first_seen"] == "2026-11-02" and h["acme:3"]["last_seen"] == "2026-11-02"
    assert h["acme:1"]["first_run"] is True and h["acme:3"]["first_run"] is False
    assert all(r["status"] == "open" and r["removed_date"] == "" for r in h.values())


def test_removed_when_missing():
    h = {}
    apply_day(h, "2026-11-01", "acme", [row(1), row(2)], first_file=True)
    apply_day(h, "2026-11-02", "acme", [row(1)], first_file=False)
    assert h["acme:2"]["status"] == "removed"
    assert h["acme:2"]["removed_date"] == "2026-11-02"
    assert h["acme:2"]["last_seen"] == "2026-11-01"
    # stays removed with the original date on later days
    apply_day(h, "2026-11-03", "acme", [row(1)], first_file=False)
    assert h["acme:2"]["removed_date"] == "2026-11-02"


def test_reopen_keeps_first_seen():
    h = {}
    apply_day(h, "2026-11-01", "acme", [row(1)], first_file=True)
    apply_day(h, "2026-11-02", "acme", [], first_file=False)
    assert h["acme:1"]["status"] == "removed"
    apply_day(h, "2026-11-04", "acme", [row(1)], first_file=False)
    assert h["acme:1"]["status"] == "open"
    assert h["acme:1"]["removed_date"] == ""
    assert h["acme:1"]["first_seen"] == "2026-11-01"
    assert h["acme:1"]["last_seen"] == "2026-11-04"


def test_other_sources_untouched():
    h = {}
    apply_day(h, "2026-11-01", "acme", [row(1)], first_file=True)
    apply_day(h, "2026-11-01", "beta", [row(9, source="beta")], first_file=True)
    apply_day(h, "2026-11-02", "beta", [], first_file=False)
    assert h["acme:1"]["status"] == "open"
    assert h["beta:9"]["status"] == "removed"


def test_latest_attributes_win():
    h = {}
    apply_day(h, "2026-11-01", "acme", [row(1, title="Analyst")], first_file=True)
    apply_day(h, "2026-11-02", "acme", [row(1, title="Senior Analyst")], first_file=False)
    assert h["acme:1"]["title"] == "Senior Analyst"


def gh_envelope(cfg, ids):
    jobs = [{"id": i, "title": "FP&A Analyst" if i == 1 else "Engineer", "absolute_url": f"https://x/{i}",
             "location": {"name": "Remote"}} for i in ids]
    return {"source": cfg["name"], "config": cfg, "fetched_at": "", "payload": {"jobs": jobs}}


def ab_envelope(cfg, ids):
    jobs = [{"id": f"b{i}", "title": "Treasury Analyst", "jobUrl": f"https://y/{i}"} for i in ids]
    return {"source": cfg["name"], "config": cfg, "fetched_at": "", "payload": {"jobs": jobs}}


def test_build_from_raw_files(tmp_path):
    raw = tmp_path / "raw"
    write_raw(raw, "2026-11-01", gh_envelope(CFG, [1, 2]))
    write_raw(raw, "2026-11-02", gh_envelope(CFG, [1, 3]))
    write_raw(raw, "2026-11-02", ab_envelope(OTHER, [7]))   # beta starts a day later
    # 2026-11-03: acme failed (no raw file) -> its postings are not removed
    write_raw(raw, "2026-11-03", ab_envelope(OTHER, []))

    rows = {r["posting_id"]: r for r in build_history(raw)}
    assert list(rows) == sorted(rows)  # sorted by posting_id

    assert rows["acme:1"]["in_role"] is True and rows["acme:2"]["in_role"] is False
    assert rows["acme:1"]["first_run"] is True and rows["acme:3"]["first_run"] is False
    assert rows["acme:2"]["status"] == "removed" and rows["acme:2"]["removed_date"] == "2026-11-02"
    assert rows["acme:3"]["status"] == "open" and rows["acme:3"]["last_seen"] == "2026-11-02"
    assert rows["beta:b7"]["first_run"] is True  # in beta's first raw file
    assert rows["beta:b7"]["status"] == "removed" and rows["beta:b7"]["removed_date"] == "2026-11-03"


def test_build_is_reproducible(tmp_path):
    raw = tmp_path / "raw"
    write_raw(raw, "2026-11-01", gh_envelope(CFG, [1, 2]))
    write_raw(raw, "2026-11-02", gh_envelope(CFG, [2, 3]))
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_history(build_history(raw), a)
    write_history(build_history(raw), b)
    assert a.read_bytes() == b.read_bytes()
    with open(a, newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == HISTORY_COLUMNS
        first = next(reader)
    assert first["in_role"] in ("true", "false") and first["first_run"] in ("true", "false")
