"""Rewrite the "Latest work" block of README.md from public GitHub activity.

Runs daily in .github/workflows/activity.yml. Reads the user's public events,
keeps merged pull requests, releases and new repositories (pushes alone are
noise), and replaces everything between the ACTIVITY markers.

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


def fetch_events() -> list[dict]:
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/events/public?per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": f"{USER}-profile"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def describe(event: dict) -> str | None:
    repo = event["repo"]["name"]
    if repo in SKIP_REPOS:
        return None
    short = repo.split("/", 1)[1]
    p = event.get("payload", {})
    kind = event["type"]
    if kind == "PullRequestEvent" and p.get("action") == "closed" and p["pull_request"].get("merged"):
        pr = p["pull_request"]
        return f"merged [{pr['title']}]({pr['html_url']}) in **{short}**"
    if kind == "ReleaseEvent" and p.get("action") == "published":
        rel = p["release"]
        return f"released [{rel.get('name') or rel['tag_name']}]({rel['html_url']}) of **{short}**"
    if kind == "CreateEvent" and p.get("ref_type") == "repository":
        return f"started [**{short}**](https://github.com/{repo})"
    return None


def render(events: list[dict]) -> str:
    lines, seen = [], set()
    for e in events:
        text = describe(e)
        if not text or text in seen:
            continue
        seen.add(text)
        day = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")).strftime("%b %d")
        lines.append(f"- `{day}` {text}")
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
