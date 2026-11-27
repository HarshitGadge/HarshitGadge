"""Rewrite the "Latest work" block of README.md from public GitHub activity.

Runs daily in .github/workflows/activity.yml. Reads the user's public events,
keeps merged pull requests, pull requests opened in other people's repos,
releases and new repositories (pushes alone are noise), and replaces everything
between the ACTIVITY markers.

The events API trims pull-request payloads to {url, id, number, head, base} and
reports a merge as action "merged", so titles and links are fetched from the
pull request itself.

    GITHUB_TOKEN=... python scripts/update_activity.py
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

USER = "HarshitGadge"
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!--ACTIVITY:START-->", "<!--ACTIVITY:END-->"
LIMIT = 6
SKIP_REPOS = {f"{USER}/{USER}"}


def get(url: str) -> dict | list:
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json", "User-Agent": f"{USER}-profile"}
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_events() -> list[dict]:
    return get(f"https://api.github.com/users/{USER}/events/public?per_page=100")


def pull_request(event: dict, fetch=get) -> tuple[str, str]:
    """(title, html_url) for the pull request an event refers to."""
    pr = event["payload"].get("pull_request") or {}
    repo, number = event["repo"]["name"], event["payload"].get("number") or pr.get("number")
    title, html = pr.get("title"), pr.get("html_url")
    if not (title and html) and pr.get("url"):
        try:
            full = fetch(pr["url"])
            title, html = full.get("title"), full.get("html_url")
        except Exception:  # keep the line, just without a title
            pass
    return title or f"#{number}", html or f"https://github.com/{repo}/pull/{number}"


def describe(event: dict, fetch=get) -> tuple[str, str | None] | None:
    """(dedupe key, markdown or None to suppress that key) for events worth showing."""
    repo = event["repo"]["name"]
    if repo in SKIP_REPOS:
        return None
    own = repo.startswith(f"{USER}/")
    name = repo.split("/", 1)[1] if own else repo
    p = event.get("payload", {})
    kind, action = event["type"], p.get("action")
    if kind == "PullRequestEvent":
        key = f"pr:{repo}#{p.get('number') or (p.get('pull_request') or {}).get('number')}"
        merged = action == "merged" or (action == "closed" and (p.get("pull_request") or {}).get("merged"))
        if merged or (action == "opened" and not own):
            title, html = pull_request(event, fetch)
            verb = "merged" if merged else "opened"
            return key, f"{verb} [{title}]({html}) in **{name}**"
        if action == "closed":  # closed unmerged: hide it, including its earlier "opened"
            return key, None
        return None
    if kind == "ReleaseEvent" and action == "published":
        rel = p["release"]
        return f"rel:{rel['html_url']}", f"released [{rel.get('name') or rel['tag_name']}]({rel['html_url']}) of **{name}**"
    if kind == "CreateEvent" and p.get("ref_type") == "repository":
        return f"repo:{repo}", f"started [**{name}**](https://github.com/{repo})"
    return None


def render(events: list[dict], fetch=get) -> str:
    """Newest first; one line per pull request (a merge wins over the earlier open)."""
    lines, seen = [], set()
    for e in events:
        found = describe(e, fetch)
        if not found or found[0] in seen:
            continue
        seen.add(found[0])
        if found[1] is None:
            continue
        day = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")).strftime("%b %d")
        lines.append(f"- `{day}` {found[1]}")
        if len(lines) == LIMIT:
            break
    return "\n".join(lines) if lines else "- _Nothing public this week._"


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    block = f"{START}\n{render(fetch_events())}\n{END}"
    updated = re.sub(re.escape(START) + r".*?" + re.escape(END), block, readme, flags=re.S)
    if updated != readme:
        README.write_text(updated, encoding="utf-8")
        print("README updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
