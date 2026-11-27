"""Render the Experience section as a DAW arrangement view.

Each role is a clip on its own track, placed by month. A playhead sweeps from
my first role to now and stops there. The roles and dates are read from the
Experience table in README.md, so the picture can't drift from the text; the
one extra clip is the MS, which the table doesn't list.

Silent: CSS keyframes only. Visitors who ask for reduced motion see the
playhead parked at now.

    python scripts/build_daw.py     # writes assets/daw-*.svg
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path

from build_studio import DARK, LIGHT, Theme

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
README = ROOT / "README.md"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
NOW = (2026, 11)   # the month "now" means on the ruler
START = (2023, 6)  # the ruler starts at my first role
END = (2026, 12)   # and runs to the end of this year
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# The degree isn't a job, so it isn't in the Experience table; it still fills
# the gap between Kuhoo and WENITE on the timeline.
STUDY = ("MS Data Science", "University of Maryland", (2024, 8), (2026, 5))


@dataclass(frozen=True)
class Clip:
    role: str
    where: str
    start: tuple[int, int]
    end: tuple[int, int] | None   # None means ongoing
    study: bool = False


def month(s: str) -> tuple[int, int]:
    name, year = s.split()
    return int(year), MONTHS.index(name[:3]) + 1


def experience() -> list[Clip]:
    """Read the roles from the README's Experience table, newest first."""
    text = README.read_text(encoding="utf-8")
    block = text[text.index("## Experience"):text.index("\n## ", text.index("## Experience") + 5)]
    clips = []
    for row in block.splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 4 or not cells[0].startswith("**"):
            continue
        role = cells[0].strip("*")
        where = cells[1].split("·")[0].strip()
        a, b = [p.strip() for p in cells[2].split("–")]
        clips.append(Clip(role, where, month(a), None if b == "now" else month(b)))
    return clips


def clips() -> list[Clip]:
    out = experience()
    study = Clip(*STUDY, study=True)
    # slot the degree in by start date, keeping newest first
    i = next(i for i, c in enumerate(out) if c.start < study.start)
    return out[:i] + [study] + out[i:]


def index(m: tuple[int, int]) -> int:
    return (m[0] - START[0]) * 12 + m[1] - START[1]


SPAN = index(END) + 1   # months on the ruler


def short(where: str) -> str:
    return {"Small Business Development Center": "SBDC", "University of Maryland": "UMD"}.get(where, where)


def label(m: tuple[int, int]) -> str:
    return f"{MONTHS[m[1] - 1]} {m[0]}"


@dataclass(frozen=True)
class Layout:
    name: str
    width: int
    head: int       # track header width
    row: int        # track height
    roles: bool     # show the role under the company in the header


WIDE = Layout("wide", 1200, 272, 46, True)
NARROW = Layout("phone", 640, 120, 40, False)


def daw(t: Theme, L: Layout) -> str:
    cs = clips()
    colours = [t.low, t.mid, t.high]
    x0, x1 = L.head + 12, L.width - 24
    px = (x1 - x0) / SPAN
    ruler_y, top = 58, 74
    H = top + len(cs) * L.row + 34
    now_x = x0 + (index(NOW) + 0.9) * px

    css = [
        f"text{{font-family:{SANS};fill:{t.text}}}",
        f".mono{{font-family:{MONO}}}",
        f".muted{{fill:{t.muted}}}",
        # the playhead runs from the first role to now, then holds
        f"@keyframes play{{0%{{transform:translateX(0)}}55%,100%{{transform:translateX({now_x - x0:.1f}px)}}}}",
        ".head{animation:play 12s cubic-bezier(.45,0,.55,1) infinite}",
        "@media (prefers-reduced-motion:reduce){.head{animation:none;transform:translateX(%.1fpx)}.clip{animation:none!important;opacity:1}}" % (now_x - x0),
    ]
    b: list[str] = [f'<rect width="{L.width}" height="{H}" rx="12" fill="{t.bg}"/>']

    # transport bar
    b.append(f'<text x="24" y="32" class="mono" style="font-size:13px;font-weight:700">EXPERIENCE</text>')
    b.append(f'<text x="{L.width - 24}" y="32" text-anchor="end" class="mono muted" style="font-size:12px">'
             f'{escape(label(START))} → now</text>')

    # ruler: a tick each month, a label each year
    for m in range(SPAN + 1):
        x = x0 + m * px
        y_m = START[0] + (START[1] - 1 + m) // 12
        mo = (START[1] - 1 + m) % 12 + 1
        tall = mo == 1
        b.append(f'<line x1="{x:.1f}" y1="{ruler_y + (0 if tall else 8)}" x2="{x:.1f}" y2="{ruler_y + 14}" stroke="{t.muted}" stroke-opacity="{.8 if tall else .35}"/>')
        if (tall or m == 0) and x + 34 < L.width:   # no clipped year at the far edge
            b.append(f'<text x="{x + 4:.1f}" y="{ruler_y + 8}" class="mono muted" style="font-size:11px">{y_m}</text>')

    rng = random.Random(7)
    for i, c in enumerate(cs):
        y = top + i * L.row
        colour = t.muted if c.study else colours[i % 3]
        # lane
        b.append(f'<rect x="0" y="{y}" width="{L.width}" height="{L.row}" fill="{t.off}" opacity="{.55 if i % 2 else .3}"/>')
        # header: a colour chip, the company, and the role on wide screens
        b.append(f'<rect x="16" y="{y + 12}" width="4" height="{L.row - 24}" rx="2" fill="{colour}"/>')
        if L.roles:
            b.append(f'<text x="30" y="{y + 20}" style="font-size:13px;font-weight:600">{escape(c.where)}</text>')
            b.append(f'<text x="30" y="{y + 36}" class="muted" style="font-size:11.5px">{escape(c.role)}</text>')
        else:
            b.append(f'<text x="28" y="{y + L.row / 2 + 4:.0f}" style="font-size:12px;font-weight:600">{escape(short(c.where))}</text>')
        # the clip
        a = index(c.start)
        e = index(c.end) + 1 if c.end else index(NOW) + 0.9
        cx, cw = x0 + a * px, (e - a) * px
        reach = (cx - x0) / (now_x - x0) * 55   # % of the cycle when the playhead arrives
        style = f"animation:lit{i} 12s step-end infinite"
        css.append(f"@keyframes lit{i}{{0%{{opacity:.28}}{reach:.1f}%,100%{{opacity:1}}}}")
        g = [f'<g class="clip" style="{style}">']
        dash = ' stroke-dasharray="4 3"' if c.study else ""
        g.append(f'<rect x="{cx:.1f}" y="{y + 7}" width="{cw:.1f}" height="{L.row - 14}" rx="5" fill="{colour}" fill-opacity="{.16 if c.study else .3}" stroke="{colour}"{dash}/>')
        # a little waveform inside, so it reads as audio
        n = int(cw // 4)
        mid = y + L.row / 2
        for k in range(n):
            h = rng.uniform(.2, 1) * (L.row - 22) / 2
            b_x = cx + 3 + k * 4
            if b_x > cx + cw - 4:
                break
            g.append(f'<rect x="{b_x:.1f}" y="{mid - h:.1f}" width="2" height="{2 * h:.1f}" fill="{colour}" opacity=".7"/>')
        if c.end is None:   # ongoing: mark it as now
            g.append(f'<text x="{cx + cw + 6:.1f}" y="{mid + 4:.0f}" class="mono" style="font-size:11px;font-weight:700;fill:{colour}">now</text>')
        g.append("</g>")
        b.extend(g)
        if L.roles and c.end is not None:
            when = f"{MONTHS[c.start[1]-1]} {c.start[0] % 100:02d} – {MONTHS[c.end[1]-1]} {c.end[0] % 100:02d}"
            tx = cx + cw + 6
            anchor = "start"
            if tx + 90 > x1:
                tx, anchor = cx - 6, "end"
            b.append(f'<text x="{tx:.1f}" y="{mid + 4:.0f}" text-anchor="{anchor}" class="mono muted" style="font-size:10.5px">{when}</text>')

    # the playhead, drawn last so it sits over the clips
    b.append(f'<g class="head"><line x1="{x0}" y1="{ruler_y - 4}" x2="{x0}" y2="{H - 22}" stroke="{t.high}" stroke-width="2"/>'
             f'<polygon points="{x0 - 6},{ruler_y - 8} {x0 + 6},{ruler_y - 8} {x0},{ruler_y}" fill="{t.high}"/></g>')
    b.append(f'<text x="24" y="{H - 10}" class="muted" style="font-size:11px">Dashed clip: study, not a job.</text>')

    desc = "; ".join(f"{c.role}, {c.where}, {label(c.start)} to {label(c.end) if c.end else 'now'}" for c in cs)
    title = f"Experience as a DAW timeline: {desc}."
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{L.width}" height="{H}" viewBox="0 0 {L.width} {H}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title><style>{"".join(css)}</style>' + "".join(b) + "</svg>\n")


def render() -> dict[str, str]:
    out = {}
    for t in (DARK, LIGHT):
        out[f"daw-{t.name}.svg"] = daw(t, WIDE)
        out[f"daw-phone-{t.name}.svg"] = daw(t, NARROW)
    return out


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for name, text in render().items():
        (ASSETS / name).write_text(text, encoding="utf-8")
    print("wrote DAW timeline SVGs")


if __name__ == "__main__":
    main()
