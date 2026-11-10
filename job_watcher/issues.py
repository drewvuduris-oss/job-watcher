"""Open (or update) the GitHub Issue for a run date and close the earlier ones.

Uses the REST API with the GITHUB_TOKEN that GitHub Actions provides. Without a
token (a local run) the issue step is skipped.
"""

from __future__ import annotations

import os

import requests

LABEL = "daily-report"
API = "https://api.github.com"
MAX_BODY = 60000  # GitHub rejects issue bodies over 65,536 characters


def _line(rec: dict) -> str:
    star = "⭐ " if str(rec.get("in_role")).lower() == "true" else ""
    where = " · ".join(x for x in (rec.get("employer"), rec.get("location")) if x)
    title = (rec.get("title") or "(untitled)").replace("[", "(").replace("]", ")")
    return f"- {star}[{title}]({rec.get('url')}) — {where}"


def _section(heading: str, recs: list[dict]) -> list[str]:
    # postings in the role first, then by employer and title
    recs = sorted(recs, key=lambda r: (str(r.get("in_role")).lower() != "true", r.get("employer", ""), r.get("title", "")))
    lines = [f"## {heading} ({len(recs)})", ""]
    lines += [_line(r) for r in recs] if recs else ["_None today._"]
    return lines + [""]


def issue_body(date: str, status: dict, new: list[dict], removed: list[dict], site_url: str = "") -> str:
    failed = [s["name"] for s in status["sources"] if not s["ok"]]
    head = [
        f"Job Watcher report for **{date}** (UTC).",
        "",
        f"- Open postings: **{status['open']}**",
        f"- New today: **{status['new_today']}**",
        f"- Removed today: **{status['removed_today']}**",
        f"- Sources OK: **{sum(s['ok'] for s in status['sources'])} / {len(status['sources'])}**"
        + (f" (failed: {', '.join(failed)})" if failed else ""),
    ]
    if site_url:
        head.append(f"- Site: {site_url}")
    head += ["", "⭐ = in the watched role (finance analyst).", ""]

    lines = head + _section("New postings", new) + _section("Removed postings", removed)
    body = "\n".join(lines)
    if len(body) > MAX_BODY:
        cut = body[:MAX_BODY].rsplit("\n", 1)[0]
        body = cut + f"\n\n…list truncated; the full lists are on the site{': ' + site_url if site_url else ''}."
    return body


class GitHub:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _call(self, method: str, path: str, **kw):
        resp = self.session.request(method, f"{API}/repos/{self.repo}{path}", timeout=30, **kw)
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def report_issues(self) -> list[dict]:
        issues, page = [], 1
        while True:
            batch = self._call("GET", "/issues", params={"labels": LABEL, "state": "all", "per_page": 100, "page": page})
            issues += [i for i in batch if "pull_request" not in i]
            if len(batch) < 100:
                return issues
            page += 1

    def publish(self, title: str, body: str) -> int:
        try:
            self._call("POST", "/labels", json={"name": LABEL, "color": "1f6feb", "description": "Daily Job Watcher report"})
        except requests.HTTPError:
            pass  # label already exists

        issues = self.report_issues()
        today = next((i for i in issues if i["title"] == title), None)
        if today:
            self._call("PATCH", f"/issues/{today['number']}", json={"body": body, "state": "open"})
            number = today["number"]
        else:
            number = self._call("POST", "/issues", json={"title": title, "body": body, "labels": [LABEL]})["number"]

        for issue in issues:
            if issue["state"] == "open" and issue["number"] != number:
                self._call("PATCH", f"/issues/{issue['number']}", json={"state": "closed", "state_reason": "completed"})
        return number


def publish_issue(date: str, body: str) -> int | None:
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("issue: GITHUB_TOKEN / GITHUB_REPOSITORY not set, skipping")
        return None
    number = GitHub(repo, token).publish(date, body)
    print(f"issue: #{number} '{date}'")
    return number


def site_url() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repo:
        return ""
    owner, name = repo.split("/", 1)
    return f"https://{owner.lower()}.github.io/{name}/"
