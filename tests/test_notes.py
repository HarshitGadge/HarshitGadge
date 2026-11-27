"""The write-ups in notes/ must stick to the README's numbers and be linked from it."""
from pathlib import Path

from test_agent_files import README, numbers

NOTES = Path(__file__).resolve().parents[1] / "notes"
WRITEUPS = sorted(p for p in NOTES.glob("*.md") if p.name != "README.md")


def test_there_are_writeups_and_each_is_listed():
    index = (NOTES / "README.md").read_text(encoding="utf-8")
    assert WRITEUPS
    for p in WRITEUPS:
        assert f"({p.name})" in index, f"{p.name} isn't listed in notes/README.md"
        assert f"(notes/{p.name})" in README, f"{p.name} isn't linked from the profile README"


def test_every_number_in_a_writeup_is_in_readme():
    for p in WRITEUPS:
        missing = sorted(n for n in numbers(p.read_text(encoding="utf-8")) if n not in README)
        assert not missing, f"{p.name} has numbers that the README doesn't: {missing}"
