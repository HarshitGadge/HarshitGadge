"""Render the Toolbox as a 16-step drum sequencer.

Each track is one tool from the Toolbox line in README.md, grouped into four
kits. A cursor steps across the 16 steps and lights the pads it passes. The
beat is a loop, not a chart: which steps are lit says nothing about how well I
know a tool. The track names are read from the README, so the picture can't
drift from the text.

Silent: CSS keyframes only. Visitors who ask for reduced motion see the pads
lit and no cursor.

    python scripts/build_sequencer.py     # writes assets/sequencer-*.svg
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from pathlib import Path

from build_studio import DARK, LIGHT, Theme

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

STEPS = 16
LOOP = 4.0   # seconds per bar, which is 120 bpm

# Which kit each tool sits in. Every tool in the Toolbox line must be here.
KITS = {
    "Languages": ["Python", "SQL"],
    "AI": ["LangChain", "LangGraph", "FastAPI"],
    "Data": ["PySpark", "dbt", "Kafka", "Databricks", "Snowflake"],
    "Cloud & ops": ["AWS", "Docker", "GitHub Actions"],
}
AMBER = {"dark": "#f0b429", "light": "#9a6700"}

# A beat to fill the grid, one row per track in order. x is a hit.
BEAT = [
    "x...x...x...x...",   # kick
    "....x.......x...",   # snare
    "..x...x...x...x.",   # hats
    "x.x.x.x.x.x.x.x.",
    "...x.....x...x..",
    "x.....x.....x...",
    "..x.......x.....",
    "x...x...x...xx..",
    ".x...x...x...x..",
    "....x...x.x.....",
    "x.......x.......",
    "..x...x...x...xx",
    "......x.......x.",
]


def toolbox() -> list[str]:
    """The tools listed under ## Toolbox in the README, in order."""
    text = README.read_text(encoding="utf-8")
    block = text[text.index("## Toolbox"):]
    line = next(l for l in block.splitlines() if l.startswith("`"))
    return re.findall(r"`([^`]+)`", line)


def tracks() -> list[tuple[str, str]]:
    """(kit, tool) for each track, kit by kit, keeping the README's order inside a kit."""
    tools = toolbox()
    missing = [t for t in tools if not any(t in v for v in KITS.values())]
    if missing:
        raise ValueError(f"add these tools to KITS: {missing}")
    return [(kit, t) for kit, members in KITS.items() for t in tools if t in members]


@dataclass(frozen=True)
class Layout:
    name: str
    width: int
    head: int   # track name column
    row: int


WIDE = Layout("wide", 1200, 236, 26)
NARROW = Layout("phone", 640, 136, 26)


def sequencer(t: Theme, L: Layout) -> str:
    rows = tracks()
    kit_colour = dict(zip(KITS, [t.low, t.mid, t.high, AMBER[t.name]]))
    x0, x1 = L.head, L.width - 24
    step = (x1 - x0) / STEPS
    pad = step - 6
    top = 74
    gap = 8                                    # space between kits
    kits_seen: list[str] = []
    ys = []
    y = top
    for kit, _ in rows:
        if kit not in kits_seen:
            if kits_seen:
                y += gap
            kits_seen.append(kit)
        ys.append(y)
        y += L.row
    H = y + 40

    css = [
        f"text{{font-family:{SANS};fill:{t.text}}}",
        f".mono{{font-family:{MONO}}}",
        f".muted{{fill:{t.muted}}}",
        ".on{opacity:.5}",
        # a lit pad flashes as the cursor reaches its column, then dims
        "@keyframes hit{0%{opacity:1}20%,100%{opacity:.5}}",
        f"@keyframes walk{{to{{transform:translateX({STEPS * step:.2f}px)}}}}",
        f".cursor{{animation:walk {LOOP}s steps({STEPS},end) infinite}}",
    ]
    for k in range(STEPS):
        css.append(f".c{k}{{animation:hit {LOOP}s linear {k * LOOP / STEPS:.2f}s infinite}}")
    css.append("@media (prefers-reduced-motion:reduce){.cursor{display:none}.on{animation:none!important;opacity:.85}}")

    b: list[str] = [f'<rect width="{L.width}" height="{H}" rx="12" fill="{t.bg}"/>']
    b.append(f'<text x="24" y="32" class="mono" style="font-size:13px;font-weight:700">TOOLBOX</text>')
    b.append(f'<text x="{L.width - 24}" y="32" text-anchor="end" class="mono muted" style="font-size:12px">120 BPM · 16 steps</text>')

    # step numbers, with every fourth one stronger
    for k in range(STEPS):
        cx = x0 + k * step + step / 2
        strong = k % 4 == 0
        b.append(f'<text x="{cx:.1f}" y="{top - 12}" text-anchor="middle" class="mono muted" '
                 f'style="font-size:10px;opacity:{1 if strong else .55}">{k + 1}</text>')

    # the cursor: a soft column that steps across, drawn under the pads
    b.append(f'<rect class="cursor" x="{x0 + 1:.1f}" y="{top - 4}" width="{step - 2:.1f}" height="{y - top + 8}" rx="5" '
             f'fill="{t.text}" opacity=".08"/>')

    last_kit = None
    for (kit, tool), ry, beat in zip(rows, ys, BEAT):
        colour = kit_colour[kit]
        if kit != last_kit:
            # the kit name sits beside its first track on wide screens
            last_kit = kit
            if L.name == "wide":
                b.append(f'<text x="24" y="{ry + L.row / 2 + 4:.0f}" class="mono" style="font-size:10px;font-weight:700;letter-spacing:1px;fill:{colour}">{escape(kit.upper())}</text>')
        name_x = 126 if L.name == "wide" else 28
        b.append(f'<rect x="{name_x - 10}" y="{ry + 7}" width="3" height="{L.row - 14}" rx="1.5" fill="{colour}"/>')
        b.append(f'<text x="{name_x}" y="{ry + L.row / 2 + 4:.0f}" style="font-size:12px;font-weight:600">{escape(tool)}</text>')
        for k, ch in enumerate(beat):
            px = x0 + k * step + 3
            py = ry + 4
            ph = L.row - 8
            if ch == "x":
                b.append(f'<rect class="on c{k}" x="{px:.1f}" y="{py}" width="{pad:.1f}" height="{ph}" rx="3" fill="{colour}"/>')
            else:
                b.append(f'<rect x="{px:.1f}" y="{py}" width="{pad:.1f}" height="{ph}" rx="3" fill="{t.off}"/>')

    b.append(f'<text x="24" y="{H - 14}" class="muted" style="font-size:11px">A loop, not a chart: each track is a tool I use, and the beat is just a beat.</text>')

    names = ", ".join(tool for _, tool in rows)
    title = f"Toolbox as a 16-step drum sequencer, one track per tool: {names}."
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{L.width}" height="{H}" viewBox="0 0 {L.width} {H}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title><style>{"".join(css)}</style>' + "".join(b) + "</svg>\n")


def render() -> dict[str, str]:
    out = {}
    for t in (DARK, LIGHT):
        out[f"sequencer-{t.name}.svg"] = sequencer(t, WIDE)
        out[f"sequencer-phone-{t.name}.svg"] = sequencer(t, NARROW)
    return out


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for name, text in render().items():
        (ASSETS / name).write_text(text, encoding="utf-8")
    print("wrote sequencer SVGs")


if __name__ == "__main__":
    main()
