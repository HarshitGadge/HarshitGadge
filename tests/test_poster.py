"""Offline checks for the festival poster and backstage pass in scripts/build_poster.py."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_poster as bp  # noqa: E402
from build_booth import ORDER  # noqa: E402

README = (ROOT / "README.md").read_text(encoding="utf-8")


def texts(svg):
    return re.findall(r"<text[^>]*>([^<]*)</text>", svg)


def test_headliners_are_coming_soon_and_carry_no_numbers():
    for name, svg in bp.render().items():
        if not name.startswith("poster"):
            continue
        assert svg.count(">COMING SOON</text>") == len(bp.HEADLINERS)
        setlist = [l for l in texts(svg) if re.match(r"\d\. ", l)]
        others = [l for l in texts(svg) if l not in setlist]
        # the setlist's running numbers are the only digits on the poster
        assert not any(re.search(r"\d", l) for l in others), (name, others)


def test_setlist_is_every_record_in_booth_order():
    assert bp.SETLIST == ORDER
    assert "ragbench" in bp.SETLIST and "RAGBench" not in dict(bp.HEADLINERS)
    for name, svg in bp.render().items():
        if name.startswith("poster"):
            joined = " ".join(texts(svg))
            for i, slug in enumerate(bp.SETLIST):
                assert f"{i + 1}. {slug}" in joined


def test_pass_contacts_match_the_readme_links():
    assert 'href="mailto:harshit.gadge.1805@gmail.com"' in README
    assert 'href="https://www.linkedin.com/in/harshitg-"' in README
    assert 'href="https://github.com/HarshitGadge"' in README or "github.com/HarshitGadge/" in README
    for theme in ("dark", "light"):
        svg = bp.render()[f"pass-{theme}.svg"]
        for _, value in bp.CONTACT:
            assert f">{value}</text>" in svg


def test_artwork_is_silent_small_and_respects_reduced_motion():
    for name, svg in bp.render().items():
        assert "<script" not in svg and "<audio" not in svg
        assert "prefers-reduced-motion" in svg
        assert "<title>" in svg
        assert len(svg.encode()) < 20_000, name


def test_readme_shows_the_poster_and_pass():
    for name in bp.render():
        assert f"assets/{name}" in README
    assert re.search(r'media="\(max-width: ?600px\)[^"]*"[^>]*poster-phone', README)


def test_committed_artwork_matches_the_generator():
    for name, svg in bp.render().items():
        assert (ROOT / "assets" / name).read_text(encoding="utf-8") == svg, name
