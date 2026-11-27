"""Offline tests for scripts/update_activity.py: no network, fake fetch."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update_activity as ua  # noqa: E402


def fake(routes):
    def fetch(url):
        if url not in routes:
            raise OSError(f"404 {url}")
        return routes[url]
    return fetch


def test_slug_title_becomes_issue_title():
    f = fake({"https://api.github.com/repos/gpsaggese/helpers/issues/1462": {"title": "Process: Fix the examples in text.rules.md"}})
    assert ua.readable("HelpersTask1462_Process_Fix_the_examples_in_text_rules_md", "gpsaggese/helpers", f) == "Process: Fix the examples in text.rules.md"


def test_slug_falls_back_to_spaces_when_issue_unreadable():
    assert ua.readable("UmdTask803_Review_and_automate_GH_project_1", "gpsaggese/gpsaggese.github.io", fake({})) == "Review and automate GH project 1"


def test_ordinary_title_untouched():
    assert ua.readable("Prepare the dashboard for Streamlit Community Cloud", "HarshitGadge/x", fake({})) == "Prepare the dashboard for Streamlit Community Cloud"


def test_merged_slug_pr_renders_readable_line():
    event = {
        "type": "PullRequestEvent", "created_at": "2026-11-25T14:17:00Z",
        "repo": {"name": "gpsaggese/helpers"},
        "payload": {"action": "merged", "number": 1463, "pull_request": {
            "title": "HelpersTask1462_Process_Fix_the_examples_in_text_rules_md",
            "html_url": "https://github.com/gpsaggese/helpers/pull/1463"}},
    }
    f = fake({"https://api.github.com/repos/gpsaggese/helpers/issues/1462": {"title": "Process: Fix the examples in text.rules.md"}})
    assert ua.render([event], f) == "- `Nov 25` merged [Process: Fix the examples in text.rules.md](https://github.com/gpsaggese/helpers/pull/1463) in **gpsaggese/helpers**"


REPOS = "https://api.github.com/users/HarshitGadge/repos?per_page=100&type=owner"


def test_no_releases_means_no_section():
    f = fake({REPOS: [{"full_name": "HarshitGadge/ragbench", "name": "ragbench"}]})
    assert ua.render_releases(ua.latest_releases(f)) == ""
    readme = "a\n<!--RELEASES:START-->\nold\n<!--RELEASES:END-->\nb"
    assert ua.replace_block(readme, ua.REL_START, ua.REL_END, "") == "a\n<!--RELEASES:START-->\n<!--RELEASES:END-->\nb"


def test_releases_newest_first_skipping_forks_and_drafts():
    f = fake({
        REPOS: [
            {"full_name": "HarshitGadge/ragbench", "name": "ragbench"},
            {"full_name": "HarshitGadge/agentic-rag-service", "name": "agentic-rag-service"},
            {"full_name": "HarshitGadge/helpers", "name": "helpers", "fork": True},
            {"full_name": "HarshitGadge/draft-only", "name": "draft-only"},
        ],
        "https://api.github.com/repos/HarshitGadge/ragbench/releases/latest": {
            "tag_name": "v1.0.0", "published_at": "2026-12-20T10:00:00Z", "html_url": "https://github.com/HarshitGadge/ragbench/releases/tag/v1.0.0"},
        "https://api.github.com/repos/HarshitGadge/agentic-rag-service/releases/latest": {
            "tag_name": "v0.3.0", "published_at": "2026-12-01T10:00:00Z", "html_url": "https://github.com/HarshitGadge/agentic-rag-service/releases/tag/v0.3.0"},
        "https://api.github.com/repos/HarshitGadge/draft-only/releases/latest": {
            "tag_name": "v0.1", "published_at": None, "draft": True, "html_url": "x"},
    })
    out = ua.render_releases(ua.latest_releases(f))
    assert out.splitlines() == [
        "## Releases", "",
        "- [**ragbench** v1.0.0](https://github.com/HarshitGadge/ragbench/releases/tag/v1.0.0) · `Dec 20, 2026`",
        "- [**agentic-rag-service** v0.3.0](https://github.com/HarshitGadge/agentic-rag-service/releases/tag/v0.3.0) · `Dec 01, 2026`",
    ]
