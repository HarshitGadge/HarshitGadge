"""Render the EDM-studio artwork for the profile README.

Silent by design: GitHub strips scripts and audio from README images, so all
motion is CSS keyframes inside the SVG, and every asset is drawn once per
GitHub colour scheme.

Hero: a spectrum analyzer. Its bars dance, settle at the tops of the letters,
then hand over to the same LED grid spelling the name. The pattern loops, and
visitors who ask for reduced motion see the name straight away.

    python scripts/build_studio.py     # writes assets/studio-*.svg
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# 5x7 LED glyphs, top row first
GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    " ": ["00000"] * 7,
}


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    off: str        # an unlit LED
    text: str
    muted: str
    low: str        # bottom rows
    mid: str
    high: str       # top rows


DARK = Theme("dark", "#0d1117", "#161b22", "#e6edf3", "#8b949e", "#2dd4bf", "#a371f7", "#f472b6")
LIGHT = Theme("light", "#ffffff", "#eaeef2", "#1f2328", "#59636e", "#0f766e", "#8250df", "#bf3989")


@dataclass(frozen=True)
class Layout:
    name: str
    lines: tuple[str, ...]      # the name, one string per LED row block
    rows: int                   # grid height in LEDs
    first_row: int              # grid row where the first line of letters starts
    line_gap: int               # empty LED rows between lines
    width: int
    pad_x: int
    top: int
    pitch_x: int = 14
    pitch_y: int = 11
    cell_w: int = 11
    cell_h: int = 8
    subtitle: tuple[str, ...] = ()


WIDE = Layout("wide", ("HARSHIT GADGE",), rows=15, first_row=4, line_gap=0, width=1200, pad_x=62, top=34,
              subtitle=("AI &amp; data engineer · RAG, agents and data pipelines · open to full-time roles",))
NARROW = Layout("phone", ("HARSHIT", "GADGE"), rows=21, first_row=3, line_gap=2, width=640, pad_x=33, top=34,
                subtitle=("AI &amp; data engineer", "RAG, agents and data pipelines", "open to full-time roles"))


def letter_grid(L: Layout) -> list[list[bool]]:
    """rows x cols booleans: which LEDs spell the name. Each line is centred."""
    cols = max(len(line) * 6 - 1 for line in L.lines)
    grid = [[False] * cols for _ in range(L.rows)]
    for n, line in enumerate(L.lines):
        width = len(line) * 6 - 1
        x0 = (cols - width) // 2
        y0 = L.first_row + n * (7 + L.line_gap)
        for i, ch in enumerate(line):
            for r, bits in enumerate(GLYPHS[ch]):
                for c, bit in enumerate(bits):
                    if bit == "1":
                        grid[y0 + r][x0 + i * 6 + c] = True
    return grid


def settle_heights(grid: list[list[bool]]) -> list[int]:
    """Where each bar comes to rest: the top of its column's highest letter LED (0 for an empty column)."""
    rows = len(grid)
    out = []
    for c in range(len(grid[0])):
        lit = [r for r in range(rows) if grid[r][c]]
        out.append(rows - lit[0] if lit else 0)
    return out


CYCLE = 14.0           # seconds per loop
DANCE = 3.4            # bars move for this long, then settle
STEP = 0.2             # seconds per bar frame
FADE = (3.6, 4.2)      # bars hand over to the name
HOLD_END = (13.2, 13.7)


def pct(s: float) -> str:
    return f"{s / CYCLE * 100:.3f}".rstrip("0").rstrip(".") + "%"


def bar_frames(col: int, cols: int, rows: int, final: int, rng: random.Random) -> list[int]:
    """Bar heights (in LEDs) for each frame of the dance, easing onto `final`."""
    frames = int(DANCE / STEP)
    bass = 1.0 - 0.45 * col / max(cols - 1, 1)          # left side a bit louder, like low frequencies
    out = []
    for k in range(frames):
        wild = rng.randint(2, rows) * bass
        blend = max(0.0, (k - frames * 0.55) / (frames * 0.45))   # last ~45% of frames drift to the letters
        out.append(max(0, min(rows, round(wild * (1 - blend) + final * blend))))
    out[-1] = final
    return out


def row_colour(t: Theme, r: int, rows: int) -> str:
    f = 1 - r / (rows - 1)          # 0 at the bottom row, 1 at the top
    return t.low if f < 0.38 else t.mid if f < 0.72 else t.high


def hero(t: Theme, L: Layout) -> str:
    rng = random.Random(f"{L.name}-spectrum")
    grid = letter_grid(L)
    rows, cols = L.rows, len(grid[0])
    gx = L.pad_x + (L.width - 2 * L.pad_x - (cols * L.pitch_x - (L.pitch_x - L.cell_w))) / 2
    gy = L.top
    floor = gy + rows * L.pitch_y
    height = floor + 26 + 26 * len(L.subtitle) + 10
    finals = settle_heights(grid)

    css = [
        f"text{{font-family:{SANS};fill:{t.text}}}",
        f".sub{{fill:{t.muted};font-size:{15 if L.name == 'wide' else 15}px}}",
        f"@keyframes bars{{0%,{pct(FADE[0])}{{opacity:1}}{pct(FADE[1])},{pct(HOLD_END[1])}{{opacity:0}}100%{{opacity:1}}}}",
        f"@keyframes name{{0%,{pct(FADE[0])}{{opacity:0}}{pct(FADE[1])},{pct(HOLD_END[0])}{{opacity:1}}{pct(HOLD_END[1])},100%{{opacity:0}}}}",
        f".bars{{animation:bars {CYCLE}s linear infinite}}",
        f".name{{opacity:0;animation:name {CYCLE}s linear infinite}}",
        "@media (prefers-reduced-motion:reduce){.bars{display:none}.name{opacity:1;animation:none}.col{animation:none!important}}",
    ]
    body: list[str] = []
    cell = lambda x, y, fill: f'<rect x="{x:.1f}" y="{y}" width="{L.cell_w}" height="{L.cell_h}" rx="1.5" fill="{fill}"/>'

    # one lit column, drawn once and reused for every bar
    body.append('<defs>'
                f'<pattern id="off" x="{gx:.1f}" y="{gy}" width="{L.pitch_x}" height="{L.pitch_y}" patternUnits="userSpaceOnUse">'
                f'<rect width="{L.cell_w}" height="{L.cell_h}" rx="1.5" fill="{t.off}"/></pattern>'
                '<g id="lit">' + "".join(cell(0, gy + r * L.pitch_y, row_colour(t, r, rows)) for r in range(rows)) + '</g>'
                '</defs>')
    # unlit LEDs
    body.append(f'<rect x="{gx:.1f}" y="{gy}" width="{cols * L.pitch_x:.1f}" height="{rows * L.pitch_y}" fill="url(#off)"/>')

    # dancing bars: a full lit column slides up and down; the floor below hides the rest
    bars = []
    for c in range(cols):
        frames = bar_frames(c, cols, rows, finals[c], rng)
        kf = []
        for k, h in enumerate(frames):
            kf.append(f"{pct(k * STEP)}{{transform:translateY({(rows - h) * L.pitch_y}px)}}")
        kf.append(f"{pct(DANCE)},100%{{transform:translateY({(rows - finals[c]) * L.pitch_y}px)}}")
        css.append(f"@keyframes c{c}{{{''.join(kf)}}}")
        css.append(f".c{c}{{animation:c{c} {CYCLE}s step-end infinite}}")
        bars.append(f'<g transform="translate({gx + c * L.pitch_x:.1f} 0)"><use href="#lit" class="col c{c}"/></g>')
    body.append('<g class="bars">' + "".join(bars) + '</g>')
    body.append(f'<rect x="0" y="{floor - (L.pitch_y - L.cell_h)}" width="{L.width}" height="{height - floor + L.pitch_y}" fill="{t.bg}"/>')

    # the name, on the same grid
    body.append('<g class="name">' + "".join(cell(gx + c * L.pitch_x, gy + r * L.pitch_y, row_colour(t, r, rows))
                                             for r in range(rows) for c in range(cols) if grid[r][c]) + '</g>')

    for i, line in enumerate(L.subtitle):
        body.append(f'<text x="{L.width / 2}" y="{floor + 26 + i * 26}" text-anchor="middle" class="sub">{line}</text>')

    label = "Harshit Gadge: spectrum analyzer bars settle into my name. AI and data engineer, open to full-time roles."
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{L.width}" height="{height}" viewBox="0 0 {L.width} {height}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<style>{"".join(css)}</style><rect width="100%" height="100%" fill="{t.bg}"/>' + "".join(body) + "</svg>\n")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for t in (DARK, LIGHT):
        (ASSETS / f"studio-hero-{t.name}.svg").write_text(hero(t, WIDE), encoding="utf-8")
        (ASSETS / f"studio-hero-phone-{t.name}.svg").write_text(hero(t, NARROW), encoding="utf-8")
    print("wrote studio hero SVGs")


if __name__ == "__main__":
    main()
