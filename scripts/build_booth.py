"""Render the DJ booth record sleeves for the profile README.

Each featured project is a record: a sleeve with its own pattern, the disc
sliding out of it, and the headline number on the liner. A sleeve links to the
same record on the booth, the home page of https://harshitgadge.github.io/, where
the full liner notes live.

The facts come from CARDS in build_assets.py, so the sleeves, the old cards and
the booth page all say the same thing. Silent: CSS keyframes only.

    python scripts/build_booth.py     # writes assets/sleeve-*.svg
"""
from __future__ import annotations

import math
from html import escape
from pathlib import Path

from build_assets import ASSETS, CARDS, DARK, LIGHT, MONO, SANS, Card, Theme

BOOTH = "https://harshitgadge.github.io/"
W, H = 460, 200

# One colour and one pattern per record, the same ones the booth page uses.
# The sleeve itself is an object, so it keeps its colour in both themes; only
# the liner text switches to the theme's colours.
STYLE = {
    "agentic-rag-service": ("#2dd4bf", "rings"),
    "capability-runtime": ("#a78bfa", "steps"),
    "payments-data-platform": ("#f0b429", "stripes"),
    "medicare-claims-analytics": ("#f472b6", "dots"),
    "kafka-databricks-nasa": ("#38bdf8", "burst"),
    "fraud-screening": ("#fb7185", "grid"),
    "ragbench": ("#a3e635", "bars"),
}
# Darker text accents for the light theme, so the liner reads on white.
LIGHT_TEXT = {
    "#2dd4bf": "#0f766e", "#a78bfa": "#8250df", "#f0b429": "#9a6700",
    "#f472b6": "#bf3989", "#38bdf8": "#0969da", "#fb7185": "#cf222e",
    "#a3e635": "#4d7c0f",
}
SLEEVE_BG = "#0b0d11"
# Running order on the booth page and in the README (A1 to A7).
ORDER = list(STYLE)


def repo(c: Card) -> str:
    """The GitHub repo name, which is also the record's anchor on the booth page."""
    return "fraud-screening" if c.slug == "Detecting_Fradulent_job" else c.slug


def booth_link(c: Card) -> str:
    return f"{BOOTH}#{repo(c)}"


def asset_name(c: Card, t: Theme) -> str:
    return f"sleeve-{repo(c)}-{t.name}.svg"


def title_lines(title: str, max_chars: int = 18) -> list[str]:
    """Split a long repo name after a hyphen so it fits the liner."""
    if len(title) <= max_chars:
        return [title]
    cut = title.rfind("-", 0, max_chars) + 1
    return [title[:cut], title[cut:]] if cut else [title]


def pattern(kind: str, c: str) -> str:
    """The sleeve art, drawn inside a 156x156 box at the origin."""
    bg = f'<rect width="156" height="156" fill="{SLEEVE_BG}"/>'
    if kind == "rings":
        rings = "".join(f'<circle cx="110" cy="46" r="{r}" fill="none" stroke="{c}" stroke-width="6"/>'
                        for r in range(10, 170, 15))
        return bg + rings
    if kind == "steps":
        bands = "".join(f'<rect x="{x}" y="-60" width="{w}" height="280" fill="{c}"/>'
                        for x, w in ((10, 18), (48, 11), (78, 6), (100, 3)))
        return bg + f'<g transform="rotate(45 78 78)">{bands}</g>'
    if kind == "stripes":
        out = [bg]
        for x in range(0, 156, 24):
            out.append(f'<rect x="{x}" width="8" height="156" fill="{c}"/>')
            out.append(f'<rect x="{x+13}" width="3" height="156" fill="{c}" opacity=".6"/>')
        return "".join(out)
    if kind == "dots":
        return bg + "".join(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{c}"/>'
                            for x in range(8, 156, 16) for y in range(8, 156, 16))
    if kind == "burst":
        cx, cy, R = 47, 109, 240
        rays = []
        for i in range(0, 360, 18):
            a, b = math.radians(i), math.radians(i + 6)
            rays.append(f'<polygon points="{cx},{cy} {cx + R*math.cos(a):.1f},{cy + R*math.sin(a):.1f} '
                        f'{cx + R*math.cos(b):.1f},{cy + R*math.sin(b):.1f}" fill="{c}"/>')
        return bg + "".join(rays)
    if kind == "grid":
        lines = "".join(f'<rect x="{i}" width="2" height="156" fill="{c}"/><rect y="{i}" width="156" height="2" fill="{c}"/>'
                        for i in range(0, 156, 20))
        return (f'<defs><linearGradient id="g" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{SLEEVE_BG}"/>'
                f'<stop offset="1" stop-color="{c}" stop-opacity=".35"/></linearGradient></defs>'
                f'{bg}<rect width="156" height="156" fill="url(#g)"/>' + lines)
    if kind == "bars":
        out = [bg]
        for x in range(0, 156, 22):
            out.append(f'<rect x="{x + 6}" width="6" height="156" fill="{c}" opacity=".47"/>')
        for y in range(0, 156, 22):
            out.append(f'<rect y="{154 - y}" width="156" height="2" fill="{c}"/>')
        return "".join(out)
    raise ValueError(kind)


def sleeve(c: Card, t: Theme, index: int) -> str:
    colour, kind = STYLE[repo(c)]
    acc = colour if t.name == "dark" else LIGHT_TEXT[colour]
    delay = index * 0.7
    css = [
        f"text{{font-family:{SANS};fill:{t.text}}}",
        f".mono{{font-family:{MONO}}}",
        f".muted{{fill:{t.muted}}}",
        f".acc{{fill:{acc}}}",
        # the disc eases a little further out of the sleeve and back
        "@keyframes peek{0%,100%{transform:translateX(0)}50%{transform:translateX(14px)}}",
        f".disc{{animation:peek 6s ease-in-out {delay:.1f}s infinite}}",
        # a sheen sweeps the grooves, so the record reads as turning
        "@keyframes turn{to{transform:rotate(360deg)}}",
        f".sheen{{transform-origin:150px 100px;animation:turn 4s linear infinite}}",
        "@media (prefers-reduced-motion:reduce){.disc,.sheen{animation:none}}",
    ]
    b: list[str] = [f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" fill="{t.panel}" stroke="{t.border}"/>']

    # the disc, behind the sleeve
    grooves = "".join(f'<circle cx="150" cy="100" r="{r}" fill="none" stroke="#ffffff" stroke-opacity=".07"/>'
                      for r in range(34, 78, 5))
    b.append('<g class="disc">'
             f'<circle cx="150" cy="100" r="80" fill="#111318" stroke="#000" />{grooves}'
             '<path class="sheen" d="M150 100 L150 22 A78 78 0 0 1 189 32 Z" fill="#ffffff" fill-opacity=".07"/>'
             f'<circle cx="150" cy="100" r="26" fill="{colour}"/>'
             '<circle cx="150" cy="100" r="3" fill="#d7dde5"/></g>')

    # the sleeve
    b.append(f'<clipPath id="sl"><rect width="156" height="156" rx="4"/></clipPath>'
             f'<g transform="translate(20 22)"><g clip-path="url(#sl)">{pattern(kind, colour)}</g>'
             f'<rect width="156" height="156" rx="4" fill="none" stroke="#000" stroke-opacity=".5"/>'
             f'<text x="10" y="20" class="mono" style="font-size:11px;font-weight:700;fill:#fff;letter-spacing:1px">A{index + 1}</text></g>')

    # the liner
    x = 252
    b.append(f'<text x="{x}" y="38" class="acc" style="font-size:10.5px;font-weight:700;letter-spacing:1.3px">{escape(c.kicker)}</text>')
    lines = title_lines(c.title)
    for i, line in enumerate(lines):
        b.append(f'<text x="{x}" y="{62 + i*19}" class="mono" style="font-size:15px;font-weight:600">{escape(line)}</text>')
    top = 62 + (len(lines) - 1) * 19
    b.append(f'<text x="{x}" y="{top + 42}" class="mono acc" style="font-size:28px;font-weight:700">{escape(c.metric)}</text>')
    for i, label in enumerate(c.metric_label):
        b.append(f'<text x="{x}" y="{top + 62 + i*15}" class="muted" style="font-size:11.5px">{escape(label)}</text>')
    b.append(f'<text x="{W-22}" y="182" text-anchor="end" class="acc" style="font-size:12px;font-weight:600">play it on the booth &#8594;</text>')

    label = f"{c.title}: {c.metric} {' '.join(c.metric_label)}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><style>{"".join(css)}</style>' + "".join(b) + "</svg>\n")


def render() -> dict[str, str]:
    return {asset_name(c, t): sleeve(c, t, ORDER.index(repo(c))) for t in (DARK, LIGHT) for c in CARDS}


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    out = render()
    for name, text in out.items():
        (ASSETS / name).write_text(text, encoding="utf-8")
    print(f"wrote {len(out)} sleeves to {ASSETS}")


if __name__ == "__main__":
    main()
