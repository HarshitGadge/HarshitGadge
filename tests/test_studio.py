"""Offline checks for the EDM studio artwork in scripts/build_studio.py."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_studio as bs  # noqa: E402


def test_the_letters_spell_the_name_on_both_layouts():
    for L in (bs.WIDE, bs.NARROW):
        grid = bs.letter_grid(L)
        # read each 5x7 block back and match it to a glyph
        cols = len(grid[0])
        text = []
        for n, line in enumerate(L.lines):
            x0 = (cols - (len(line) * 6 - 1)) // 2
            y0 = L.first_row + n * (7 + L.line_gap)
            for i in range(len(line)):
                block = ["".join("1" if grid[y0 + r][x0 + i * 6 + c] else "0" for c in range(5)) for r in range(7)]
                text.append(next(ch for ch, g in bs.GLYPHS.items() if g == block))
        assert "".join(text) == "".join(L.lines)


def test_bars_end_at_the_top_of_each_letter_column():
    grid = bs.letter_grid(bs.WIDE)
    finals = bs.settle_heights(grid)
    for c, h in enumerate(finals):
        lit = [r for r in range(bs.WIDE.rows) if grid[r][c]]
        assert h == (bs.WIDE.rows - lit[0] if lit else 0)
    import random
    frames = bs.bar_frames(0, 10, 15, finals[0], random.Random(1))
    assert frames[-1] == finals[0] and all(0 <= f <= 15 for f in frames)


def test_hero_is_silent_and_respects_reduced_motion():
    for t in (bs.DARK, bs.LIGHT):
        for L in (bs.WIDE, bs.NARROW):
            svg = bs.hero(t, L)
            assert "<script" not in svg and "<audio" not in svg
            assert "prefers-reduced-motion" in svg
            assert "<title>" in svg
            assert len(svg) < 120_000


def test_committed_hero_files_are_up_to_date():
    for t in (bs.DARK, bs.LIGHT):
        assert (bs.ASSETS / f"studio-hero-{t.name}.svg").read_text(encoding="utf-8") == bs.hero(t, bs.WIDE)
        assert (bs.ASSETS / f"studio-hero-phone-{t.name}.svg").read_text(encoding="utf-8") == bs.hero(t, bs.NARROW)
