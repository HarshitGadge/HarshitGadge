"""Every number in the agent-readable files must also appear in README.md.

llms.txt and AGENTS.md repeat the README's facts for AI tools. This keeps them
from drifting: if a result changes in the README, the copy has to change too.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
MONTH_YEAR = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}\b")
URL_OR_EMAIL = re.compile(r"https?://\S+|\S+@\S+")
NUMBER = re.compile(r"\d+(?:\.\d+)?%?")


def numbers(text):
    text = URL_OR_EMAIL.sub(" ", MONTH_YEAR.sub(" ", text))
    return set(NUMBER.findall(text))


def test_agent_files_exist_and_are_linked_from_readme():
    for name in ("llms.txt", "AGENTS.md"):
        assert (ROOT / name).is_file()
        assert f"({name})" in README


def test_every_number_in_agent_files_is_in_readme():
    for name in ("llms.txt", "AGENTS.md"):
        missing = sorted(n for n in numbers((ROOT / name).read_text(encoding="utf-8")) if n not in README)
        assert not missing, f"{name} has numbers that the README doesn't: {missing}"


def test_number_extraction_skips_dates_links_and_email():
    text = "Mar 2026 – Sep 2026, https://x.io/a/12, me.1805@mail.com, 0.713 and 77%"
    assert numbers(text) == {"0.713", "77%"}
