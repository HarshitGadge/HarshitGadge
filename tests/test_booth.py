"""Offline checks for the DJ booth sleeves in scripts/build_booth.py."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_booth as bb  # noqa: E402
from build_assets import CARDS  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_every_featured_project_has_a_sleeve_with_its_own_number():
    out = bb.render()
    assert len(out) == 2 * len(CARDS)
    for c in CARDS:
        for theme in ("dark", "light"):
            svg = out[f"sleeve-{bb.repo(c)}-{theme}.svg"]
            # the headline number and its label come straight from CARDS
            assert f">{c.metric}</text>" in svg
            for line in c.metric_label:
                assert f">{line}</text>".replace("'", "&#x27;") in svg


def test_running_order_matches_the_readme_and_numbers_each_record_once():
    linked = re.findall(r'href="https://harshitgadge\.github\.io/#([\w-]+)"', README)
    assert linked == bb.ORDER
    for i, slug in enumerate(bb.ORDER):
        svg = bb.render()[f"sleeve-{slug}-dark.svg"]
        assert f">A{i + 1}</text>" in svg


def test_readme_sleeves_point_at_files_that_exist_and_keep_repo_links():
    for slug in bb.ORDER:
        for theme in ("dark", "light"):
            name = f"sleeve-{slug}-{theme}.svg"
            assert f"assets/{name}" in README
            assert (ROOT / "assets" / name).exists()
        assert f'href="https://github.com/HarshitGadge/{slug}"' in README


def test_sleeves_are_silent_small_and_respect_reduced_motion():
    for name, svg in bb.render().items():
        assert "<script" not in svg and "<audio" not in svg
        assert "prefers-reduced-motion" in svg
        assert "<title>" in svg
        assert len(svg.encode()) < 20_000, name


def test_committed_sleeves_match_the_generator():
    for name, svg in bb.render().items():
        assert (ROOT / "assets" / name).read_text(encoding="utf-8") == svg, name
