"""Offline checks for the Toolbox sequencer in scripts/build_sequencer.py."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_sequencer as bs  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_every_toolbox_tool_is_a_track_and_nothing_else_is():
    assert sorted(t for _, t in bs.tracks()) == sorted(bs.toolbox())
    for name, svg in bs.render().items():
        for tool in bs.toolbox():
            assert f">{tool}</text>" in svg, (name, tool)


def test_there_is_a_beat_row_for_every_track_and_each_is_sixteen_steps():
    assert len(bs.BEAT) == len(bs.tracks())
    for row in bs.BEAT:
        assert len(row) == bs.STEPS and set(row) <= {"x", "."} and "x" in row


def test_it_says_the_beat_is_not_a_skill_rating():
    for svg in bs.render().values():
        assert "A loop, not a chart" in svg


def test_sequencer_is_silent_small_and_respects_reduced_motion():
    for name, svg in bs.render().items():
        assert "<script" not in svg and "<audio" not in svg
        assert "prefers-reduced-motion" in svg
        assert "<title>" in svg
        assert len(svg.encode()) < 30_000, name


def test_readme_shows_the_sequencer_for_each_screen_and_theme():
    for name in bs.render():
        assert f"assets/{name}" in README
    assert re.search(r'media="\(max-width: ?600px\)[^"]*"[^>]*sequencer-phone', README)


def test_committed_sequencer_matches_the_generator():
    for name, svg in bs.render().items():
        assert (ROOT / "assets" / name).read_text(encoding="utf-8") == svg, name
