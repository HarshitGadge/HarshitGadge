"""Offline tests for scripts/update_ledger.py: no network, fake fetch."""
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update_ledger as ul  # noqa: E402

API = "https://api.github.com"
SCIFACT = {"queries": 300, "configs": [
    {"config": "vector", "ndcg@10": 0.7274, "latency_p95_ms": 25.15},
    {"config": "service, new defaults (no MMR)", "ndcg@10": 0.713, "latency_p95_ms": 27.94}]}


def fake(routes):
    def fetch(url):
        if url not in routes:
            raise OSError(f"404 {url}")
        return routes[url]
    return fetch


def eval_routes(result=SCIFACT):
    return {
        f"{API}/repos/HarshitGadge/agentic-rag-service/contents/eval/results/scifact.json":
            {"content": base64.b64encode(json.dumps(result).encode()).decode()},
        f"{API}/repos/HarshitGadge/agentic-rag-service/commits?path=eval/results/scifact.json&per_page=1":
            [{"sha": "abc123", "commit": {"committer": {"date": "2026-11-20T10:00:00Z"}}}],
    }


def test_eval_row_reads_the_served_config_and_commit_date():
    [(when, row)] = ul.eval_rows(fake(eval_routes()))
    assert when == "2026-11-20T10:00:00Z"
    assert row == ("| **agentic-rag-service** | BEIR SciFact retrieval eval | nDCG@10 **0.713**, p95 27.9 ms over 300 queries "
                   "| [`Nov 20, 2026`](https://github.com/HarshitGadge/agentic-rag-service/blob/abc123/eval/results/scifact.json) |")


def test_eval_row_is_dropped_when_the_format_changes():
    assert ul.eval_rows(fake(eval_routes({"queries": 300, "configs": []}))) == []


def test_ci_rows_show_passes_and_failures_and_skip_repos_without_runs():
    routes = {
        f"{API}/users/HarshitGadge/repos?per_page=100&type=owner": [
            {"full_name": "HarshitGadge/a", "name": "a", "default_branch": "main"},
            {"full_name": "HarshitGadge/b", "name": "b", "default_branch": "master"},
            {"full_name": "HarshitGadge/c", "name": "c", "default_branch": "main"},
            {"full_name": "HarshitGadge/f", "name": "f", "fork": True}],
        f"{API}/repos/HarshitGadge/a/actions/runs?branch=main&status=completed&per_page=1": {"workflow_runs": [
            {"name": "tests", "conclusion": "success", "updated_at": "2026-11-27T01:00:00Z", "html_url": "https://github.com/HarshitGadge/a/actions/runs/1"}]},
        f"{API}/repos/HarshitGadge/b/actions/runs?branch=master&status=completed&per_page=1": {"workflow_runs": [
            {"name": "ci", "conclusion": "failure", "updated_at": "2026-11-26T01:00:00Z", "html_url": "https://github.com/HarshitGadge/b/actions/runs/2"}]},
        f"{API}/repos/HarshitGadge/c/actions/runs?branch=main&status=completed&per_page=1": {"workflow_runs": []},
    }
    rows = [r for _, r in ul.ci_rows(fake(routes))]
    assert rows == [
        "| **a** | CI: tests on `main` | passed | [`Nov 27, 2026`](https://github.com/HarshitGadge/a/actions/runs/1) |",
        "| **b** | CI: ci on `master` | **failure** | [`Nov 26, 2026`](https://github.com/HarshitGadge/b/actions/runs/2) |",
    ]


def test_nothing_readable_means_no_section():
    assert ul.render(fake({f"{API}/users/HarshitGadge/repos?per_page=100&type=owner": []})) == ""
