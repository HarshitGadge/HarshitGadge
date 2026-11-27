"""Offline checks for the Experience timeline in scripts/build_daw.py."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_daw as bd  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")


def table_rows():
    block = README[README.index("## Experience"):README.index("## Try it live")]
    return [r for r in block.splitlines() if r.startswith("| **")]


def test_every_role_in_the_table_is_a_clip_with_its_dates():
    rows = table_rows()
    jobs = [c for c in bd.clips() if not c.study]
    assert len(jobs) == len(rows)
    for c, row in zip(jobs, rows):
        assert f"**{c.role}**" in row
        assert c.where in row
        assert bd.label(c.start) in row
        assert ("now" if c.end is None else bd.label(c.end)) in row


def test_the_only_extra_clip_is_the_degree_and_it_is_marked_as_study():
    extra = [c for c in bd.clips() if c.study]
    assert [c.where for c in extra] == ["University of Maryland"]
    for name, svg in bd.render().items():
        assert "Dashed clip: study, not a job." in svg, name


def test_clips_are_newest_first():
    starts = [c.start for c in bd.clips()]
    assert starts == sorted(starts, reverse=True)


def test_timeline_is_silent_small_and_respects_reduced_motion():
    for name, svg in bd.render().items():
        assert "<script" not in svg and "<audio" not in svg
        assert "prefers-reduced-motion" in svg
        assert "<title>" in svg
        assert len(svg.encode()) < 40_000, name


def test_readme_shows_the_timeline_for_each_screen_and_theme():
    for name in bd.render():
        assert f"assets/{name}" in README
    assert re.search(r'media="\(max-width: ?600px\)[^"]*"[^>]*daw-phone', README)


def test_committed_timeline_matches_the_generator():
    for name, svg in bd.render().items():
        assert (ROOT / "assets" / name).read_text(encoding="utf-8") == svg, name
