"""Offline checks for the now-playing hero in scripts/build_studio.py."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_studio as bs  # noqa: E402


def test_name_and_role_are_on_screen_from_the_first_frame():
    for t in (bs.DARK, bs.LIGHT):
        for L in (bs.WIDE, bs.NARROW):
            svg = bs.hero(t, L)
            assert ">Harshit Gadge</text>" in svg and ">AI Engineer</text>" in svg
            # the name is never faded or hidden by an animation
            assert "opacity:0" not in svg
            assert "open to full-time roles" in svg


def test_waveform_loops_cleanly():
    h = bs.waveform()
    assert len(h) == bs.PERIOD and all(0 < x <= 1 for x in h)
    svg = bs.hero(bs.DARK, bs.WIDE)
    assert f"translateX(-{bs.PERIOD * bs.PITCH}px)" in svg


def test_hero_is_silent_small_and_respects_reduced_motion():
    for t in (bs.DARK, bs.LIGHT):
        for L in (bs.WIDE, bs.NARROW):
            svg = bs.hero(t, L)
            assert "<script" not in svg and "<audio" not in svg
            assert re.search(r"prefers-reduced-motion:reduce\)\{\.wave,\.wheel,\.live\{animation:none\}", svg)
            assert "<title>" in svg
            assert len(svg) < 60_000


def test_committed_hero_files_are_up_to_date():
    for name, text in bs.render().items():
        assert (bs.ASSETS / name).read_text(encoding="utf-8") == text
