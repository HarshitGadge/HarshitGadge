"""Rewrite the "Latest runs" block of README.md from real runs in each project.

Runs daily in .github/workflows/activity.yml, after update_activity.py. Every
value in the table is read from GitHub at run time, never typed in:

* EVALS lists committed evaluation result files. The row shows the headline
  metric from the file and the date of the commit that last changed it.
* Every other public repo of the user's that has GitHub Actions gets a row
  for the newest completed run on its default branch, passed or failed.

A failed run shows as failed. GitHub already emails the owner about a failed
run on their own repo, so this doesn't open issues.

    GITHUB_TOKEN=... python scripts/update_ledger.py
"""
from __future__ import annotations

import base64
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from update_activity import README, USER, get, own_repos, replace_block  # noqa: E402

START, END = "<!--LEDGER:START-->", "<!--LEDGER:END-->"
API = "https://api.github.com"


def scifact(result: dict) -> str:
    served = next(c for c in result["configs"] if c["config"].startswith("service, new defaults"))
    return (f"nDCG@10 **{served['ndcg@10']:.3f}**, p95 {served['latency_p95_ms']:.1f} ms "
            f"over {result['queries']} queries")


# (repo, path to a committed result file, what was run, how to read the headline)
EVALS = [
    ("agentic-rag-service", "eval/results/scifact.json", "BEIR SciFact retrieval eval", scifact),
]


def day(iso: str) -> str:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %d, %Y")


def eval_rows(fetch=get) -> list[tuple[str, str]]:
    """(iso date, markdown row) for each eval result file that can be read."""
    rows = []
    for repo, path, what, headline in EVALS:
        full = f"{USER}/{repo}"
        try:
            blob = fetch(f"{API}/repos/{full}/contents/{path}")
            result = json.loads(base64.b64decode(blob["content"]))
            commit = fetch(f"{API}/repos/{full}/commits?path={path}&per_page=1")[0]
            when = commit["commit"]["committer"]["date"]
            text = headline(result)
        except Exception:  # missing file or a changed format: leave the row out, not a wrong number
            continue
        link = f"https://github.com/{full}/blob/{commit['sha']}/{path}"
        rows.append((when, f"| **{repo}** | {what} | {text} | [`{day(when)}`]({link}) |"))
    return rows


def ci_rows(fetch=get) -> list[tuple[str, str]]:
    """(iso date, markdown row) for the newest completed Actions run of each repo."""
    rows = []
    for repo in own_repos(fetch):
        branch = repo.get("default_branch") or "main"
        try:
            runs = fetch(f"{API}/repos/{repo['full_name']}/actions/runs?branch={branch}&status=completed&per_page=1")
        except Exception:
            continue
        if not runs.get("workflow_runs"):
            continue
        run = runs["workflow_runs"][0]
        ok = run.get("conclusion") == "success"
        result = "passed" if ok else f"**{run.get('conclusion') or 'did not finish'}**"
        when = run.get("updated_at") or run["created_at"]
        rows.append((when, f"| **{repo['name']}** | CI: {run['name']} on `{branch}` | {result} | [`{day(when)}`]({run['html_url']}) |"))
    return rows


def render(fetch=get) -> str:
    rows = sorted(eval_rows(fetch), reverse=True) + sorted(ci_rows(fetch), reverse=True)
    if not rows:
        return ""
    head = ["## Latest runs", "",
            "Evaluations first, then the newest CI run of each project. A GitHub Action rebuilds this table every morning.", "",
            "| Project | Run | Result | When |", "|---|---|---|---|"]
    return "\n".join(head + [r for _, r in rows])


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    updated = replace_block(readme, START, END, render())
    if updated != readme:
        README.write_text(updated, encoding="utf-8")
        print("README updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
