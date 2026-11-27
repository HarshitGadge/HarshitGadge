"""Render the festival poster (what's coming) and the backstage pass (contact).

The poster bills the three projects I'm building next as headliners, marked
"coming soon" and carrying no numbers: every number on this page has to come
from a run in a repo, and these don't have runs yet. Under them, the setlist
names the first five records already out, in the booth's running order.

The pass carries the same contact details as the links at the top of the
README.

Silent: CSS keyframes only, and still for reduced motion.

    python scripts/build_poster.py     # writes assets/poster-*.svg, assets/pass-*.svg
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape

from build_assets import ASSETS, DARK as CARD_DARK, LIGHT as CARD_LIGHT
from build_booth import ORDER
from build_studio import DARK, LIGHT, Theme

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# The three projects I'm building next. No numbers here until they have runs.
HEADLINERS = [
    ("RAGBench", "An open-source harness for evaluating RAG pipelines"),
    ("Grounded Policy Assistant", "Agentic RAG over public US regulatory documents, with cited answers and refusals"),
    ("Market Intelligence Platform", "An event-driven, multi-agent research copilot for market intelligence"),
]
SETLIST = ORDER[:5]   # the first five records in the booth

# Contact details, as the README's top links give them.
CONTACT = [
    ("email", "harshit.gadge.1805@gmail.com"),
    ("linkedin", "linkedin.com/in/harshitg-"),
    ("github", "github.com/HarshitGadge"),
]


@dataclass(frozen=True)
class Layout:
    name: str
    width: int
    title: int      # title font size
    head: int       # headliner font size
    line: int       # characters per setlist line


WIDE = Layout("wide", 1200, 64, 34, 150)
NARROW = Layout("phone", 640, 40, 22, 30)


def wrap(words: list[str], width: int, sep: str = " · ") -> list[str]:
    lines, cur = [], ""
    for w in words:
        nxt = w if not cur else cur + sep + w
        if len(nxt) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = nxt
    return lines + [cur] if cur else lines


def poster(t: Theme, L: Layout) -> str:
    W = L.width
    cx = W / 2
    colours = [t.low, t.mid, t.high]
    desc_size = 14 if L.name == "wide" else 12
    desc_chars = 90 if L.name == "wide" else 52

    css = [
        f"text{{font-family:{SANS};fill:{t.text}}}",
        f".mono{{font-family:{MONO}}}",
        f".muted{{fill:{t.muted}}}",
        # stage lights sway slowly from the top edge
        "@keyframes sway{0%,100%{transform:rotate(-9deg)}50%{transform:rotate(9deg)}}",
        ".beam{transform-box:view-box;animation:sway 9s ease-in-out infinite}",
        "@keyframes blink{0%,100%{opacity:1}50%{opacity:.45}}",
        ".soon{animation:blink 2.4s ease-in-out infinite}",
        "@media (prefers-reduced-motion:reduce){.beam,.soon{animation:none}}",
    ]
    b: list[str] = []
    y = 58
    b.append(f'<text x="{cx}" y="{y}" text-anchor="middle" class="mono muted" style="font-size:12px;letter-spacing:4px">HARSHIT GADGE PRESENTS</text>')
    y += L.title + 14
    b.append(f'<text x="{cx}" y="{y}" text-anchor="middle" style="font-size:{L.title}px;font-weight:900;letter-spacing:2px">WINTER BUILDS</text>')
    y += 30
    b.append(f'<text x="{cx}" y="{y}" text-anchor="middle" class="muted" style="font-size:{desc_size + 1}px">New projects, built in the open over the holidays</text>')
    y += 28

    for i, (name, desc) in enumerate(HEADLINERS):
        c = colours[i]
        y += L.head + (18 if i == 0 else 30)
        b.append(f'<text x="{cx}" y="{y}" text-anchor="middle" style="font-size:{L.head}px;font-weight:800;letter-spacing:1px;fill:{c}">{escape(name.upper())}</text>')
        for part in wrap(desc.split(" "), desc_chars, " "):
            y += desc_size + 8
            b.append(f'<text x="{cx}" y="{y}" text-anchor="middle" class="muted" style="font-size:{desc_size}px">{escape(part)}</text>')
        y += 22
        b.append(f'<g class="soon"><rect x="{cx - 52}" y="{y - 14}" width="104" height="20" rx="10" fill="none" stroke="{c}"/>'
                 f'<text x="{cx}" y="{y}" text-anchor="middle" class="mono" style="font-size:10px;font-weight:700;letter-spacing:2px;fill:{c}">COMING SOON</text></g>')

    y += 34
    b.append(f'<line x1="{cx - 120}" y1="{y}" x2="{cx + 120}" y2="{y}" stroke="{t.muted}" stroke-opacity=".4"/>')
    y += 26
    b.append(f'<text x="{cx}" y="{y}" text-anchor="middle" class="mono muted" style="font-size:11px;letter-spacing:3px">ALREADY OUT · THE SETLIST</text>')
    numbered = [f"{i + 1}. {slug}" for i, slug in enumerate(SETLIST)]
    for part in wrap(numbered, L.line, "  ·  "):
        y += 22
        b.append(f'<text x="{cx}" y="{y}" text-anchor="middle" class="mono" style="font-size:13px">{escape(part)}</text>')
    H = y + 36

    # the background and the lights go under everything drawn above
    beams = []
    for i, c in enumerate(colours):
        bx = W * (0.2 + 0.3 * i)
        delay = -3 * i
        beams.append(f'<g class="beam" style="transform-origin:{bx:.0f}px 0px;animation-delay:{delay}s">'
                     f'<polygon points="{bx - 6:.0f},0 {bx + 6:.0f},0 {bx + 140:.0f},{H} {bx - 140:.0f},{H}" fill="{c}" opacity=".07"/></g>')
    under = [f'<rect width="{W}" height="{H}" rx="12" fill="{t.bg}"/>',
             f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="12"/></clipPath>',
             f'<g clip-path="url(#frame)">{"".join(beams)}</g>',
             f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" rx="8" fill="none" stroke="{t.muted}" stroke-opacity=".3" stroke-dasharray="2 6"/>']

    names = "; ".join(f"{n}: {d}" for n, d in HEADLINERS)
    title = (f"Festival poster, Winter Builds. Coming soon: {names}. "
             f"Already out: {', '.join(SETLIST)}.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title><style>{"".join(css)}</style>' + "".join(under + b) + "</svg>\n")


def backstage(theme_name: str) -> str:
    """A lanyard pass, 460 by 200, the same size as the record sleeves."""
    t = {"dark": DARK, "light": LIGHT}[theme_name]
    card = {"dark": CARD_DARK, "light": CARD_LIGHT}[theme_name]
    W, H = 460, 200
    css = [
        f"text{{font-family:{SANS};fill:{t.text}}}",
        f".mono{{font-family:{MONO}}}",
        f".muted{{fill:{t.muted}}}",
        # a holographic sheen crosses the pass now and then
        f"@keyframes sheen{{0%,60%{{transform:translateX(-200px)}}100%{{transform:translateX({W + 200}px)}}}}",
        ".sheen{animation:sheen 7s ease-in-out infinite}",
        "@media (prefers-reduced-motion:reduce){.sheen{display:none}}",
    ]
    b = [f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="{card.panel}" stroke="{card.border}"/>']
    # the band down the left with the slot for the lanyard
    b.append(f'<clipPath id="pass"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12"/></clipPath>')
    b.append(f'<g clip-path="url(#pass)"><rect width="92" height="{H}" fill="{t.high}"/>'
             f'<rect x="32" y="16" width="28" height="8" rx="4" fill="{card.panel}"/>'
             f'<text transform="translate(58 {H - 20}) rotate(-90)" class="mono" style="font-size:18px;font-weight:800;letter-spacing:3px;fill:#0b0d11">ALL ACCESS</text>'
             f'<g class="sheen"><rect x="0" y="-40" width="60" height="{H + 80}" fill="#ffffff" opacity=".10" transform="rotate(20 30 {H / 2})"/></g></g>')
    x = 114
    b.append(f'<text x="{x}" y="40" class="mono" style="font-size:10.5px;font-weight:700;letter-spacing:2px;fill:{t.high}">BACKSTAGE PASS</text>')
    b.append(f'<text x="{x}" y="70" style="font-size:22px;font-weight:800">Harshit Gadge</text>')
    b.append(f'<text x="{x}" y="92" class="muted" style="font-size:12.5px">AI and data engineer, open to full-time roles</text>')
    for i, (k, v) in enumerate(CONTACT):
        yy = 124 + i * 22
        b.append(f'<text x="{x}" y="{yy}" class="mono muted" style="font-size:11px">{k}</text>'
                 f'<text x="{x + 66}" y="{yy}" class="mono" style="font-size:12px">{escape(v)}</text>')
    label = "Backstage pass: Harshit Gadge, AI and data engineer. " + "; ".join(f"{k} {v}" for k, v in CONTACT) + "."
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><style>{"".join(css)}</style>' + "".join(b) + "</svg>\n")


def render() -> dict[str, str]:
    out = {}
    for t in (DARK, LIGHT):
        out[f"poster-{t.name}.svg"] = poster(t, WIDE)
        out[f"poster-phone-{t.name}.svg"] = poster(t, NARROW)
        out[f"pass-{t.name}.svg"] = backstage(t.name)
    return out


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for name, text in render().items():
        (ASSETS / name).write_text(text, encoding="utf-8")
    print("wrote poster and pass SVGs")


if __name__ == "__main__":
    main()
