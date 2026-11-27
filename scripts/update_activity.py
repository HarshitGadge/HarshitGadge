"""Rewrite the "Latest work" block of README.md from public GitHub activity.

Runs daily in .github/workflows/activity.yml. Reads the user's public events,
keeps merged pull requests, pull requests opened in other people's repos,
releases and new repositories (pushes alone are noise), and replaces everything
between the ACTIVITY markers.

The events API trims pull-request payloads to {url, id, number, head, base} and
reports a merge as action "merged", so titles and links are fetched from the
pull request itself. Titles that are team ticket slugs ("HelpersTask1462_...")
are swapped for the title of the issue they name.

The STATS block gets one sentence counting the pull requests merged and the
releases published over the last 30 days, all from the API, so the numbers
are never typed in by hand.

It also rewrites the RELEASES block with the newest release of each of the
user's own repos; the block stays empty, so the section doesn't show, until
the first release exists.

    GITHUB_TOKEN=... python scripts/update_activity.py
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USER = "HarshitGadge"
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!--ACTIVITY:START-->", "<!--ACTIVITY:END-->"
LIMIT = 6
SKIP_REPOS = {f"{USER}/{USER}"}
REL_START, REL_END = "<!--RELEASES:START-->", "<!--RELEASES:END-->"
RELEASE_LIMIT = 4
STATS_START, STATS_END = "<!--STATS:START-->", "<!--STATS:END-->"
STATS_DAYS = 30
# Team branches are named like "HelpersTask1462_Process_Fix_the_examples_in_text_rules_md":
# a prefix, "Task", the issue number, then the issue title with its punctuation lost.
SLUG = re.compile(r"^[A-Za-z]+Task(\d+)_(.+)$")


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
    return readable(title, repo, fetch) or f"#{number}", html or f"https://github.com/{repo}/pull/{number}"


def readable(title: str | None, repo: str, fetch=get) -> str | None:
    """Swap a ticket-slug title for the title of the issue it names.

    Falls back to the slug with underscores turned into spaces if the issue
    can't be read. Ordinary titles pass through untouched.
    """
    m = SLUG.match(title or "")
    if not m:
        return title
    try:
        issue = fetch(f"https://api.github.com/repos/{repo}/issues/{m.group(1)}")
        if issue.get("title"):
            return issue["title"]
    except Exception:
        pass
    return m.group(2).replace("_", " ")


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


def latest_releases(fetch=get) -> list[dict]:
    """The newest published release of each of the user's own public repos."""
    found = []
    for repo in own_repos(fetch):
        try:
            rel = fetch(f"https://api.github.com/repos/{repo['full_name']}/releases/latest")
        except Exception:  # 404 when a repo has no release yet
            continue
        if rel.get("published_at") and not rel.get("draft"):
            found.append({**rel, "repo": repo["name"]})
    return sorted(found, key=lambda r: r["published_at"], reverse=True)


def render_releases(releases: list[dict]) -> str:
    """A "Releases" section, or nothing at all until the first release exists."""
    if not releases:
        return ""
    lines = ["## Releases", ""]
    for r in releases[:RELEASE_LIMIT]:
        day = datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")).strftime("%b %d, %Y")
        lines.append(f"- [**{r['repo']}** {r['tag_name']}]({r['html_url']}) · `{day}`")
    return "\n".join(lines)


def own_repos(fetch=get) -> list[dict]:
    return [r for r in fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
            if not (r.get("fork") or r.get("archived") or r["full_name"] in SKIP_REPOS)]


def recent_stats(now: datetime, fetch=get) -> dict:
    """Merged pull requests (any public repo) and releases (own repos) in the window."""
    since = now - timedelta(days=STATS_DAYS)
    q = f"author:{USER}+type:pr+is:merged+merged:>={since:%Y-%m-%d}"
    prs = fetch(f"https://api.github.com/search/issues?q={q}&per_page=100")
    repos = {item["repository_url"] for item in prs.get("items", [])}
    releases = 0
    for repo in own_repos(fetch):
        try:
            rels = fetch(f"https://api.github.com/repos/{repo['full_name']}/releases?per_page=100")
        except Exception:
            continue
        releases += sum(
            1 for r in rels
            if r.get("published_at") and not r.get("draft")
            and datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) >= since
        )
    return {"prs": prs.get("total_count", 0), "repos": len(repos), "releases": releases}


def plural(n: int, word: str) -> str:
    return f"**{n}** {word}" + ("" if n == 1 else "s")


def render_stats(stats: dict, now: datetime) -> str:
    """One plain sentence, or nothing if there was no merged work in the window."""
    if not stats["prs"]:
        return ""
    sentence = (f"In the last {STATS_DAYS} days I merged {plural(stats['prs'], 'pull request')} "
                f"across {plural(stats['repos'], 'repository').replace('repositorys', 'repositories')}")
    if stats["releases"]:
        sentence += f" and published {plural(stats['releases'], 'release')}"
    return f"{sentence}. <sub>Counted from the GitHub API on {now:%b %d, %Y}.</sub>"


def replace_block(text: str, start: str, end: str, body: str) -> str:
    block = f"{start}\n{body}\n{end}" if body else f"{start}\n{end}"
    return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, flags=re.S)


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    updated = replace_block(readme, START, END, render(fetch_events()))
    updated = replace_block(updated, REL_START, REL_END, render_releases(latest_releases()))
    now = datetime.now(timezone.utc)
    updated = replace_block(updated, STATS_START, STATS_END, render_stats(recent_stats(now), now))
    if updated != readme:
        README.write_text(updated, encoding="utf-8")
        print("README updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
