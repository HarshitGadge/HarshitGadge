"""Render the EDM-studio artwork for the profile README.

Silent by design: GitHub strips scripts and audio from README images, so all
motion is CSS keyframes inside the SVG, and every asset is drawn once per
GitHub colour scheme.

Hero: a DJ deck's "now playing" screen. The track is my name, the artist line
is the role, a jog wheel turns and a waveform scrolls under a fixed playhead.
The name is there from the first frame, and visitors who ask for reduced
motion get the same screen standing still.

The colour themes here are shared by the other generators.

    python scripts/build_studio.py     # writes assets/studio-hero-*.svg
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

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


TITLE = "Harshit Gadge"
ARTIST = "AI Engineer"


@dataclass(frozen=True)
class Layout:
    name: str
    width: int
    height: int
    pad: int            # screen inset from the image edge
    wheel: tuple[int, int, int]   # jog wheel centre x, centre y, radius
    text_x: int
    title_size: int
    title_y: int
    artist_y: int
    tagline: tuple[str, ...]      # lines under the artist
    wave: tuple[int, int]         # waveform top and height


WIDE = Layout("wide", 1200, 300, 24, (122, 132, 62), 216, 54, 124, 162,
              ("RAG, agents and data pipelines · open to full-time roles",), (212, 56))
NARROW = Layout("phone", 640, 300, 16, (80, 122, 46), 146, 34, 108, 138,
                ("RAG, agents and data pipelines", "open to full-time roles"), (210, 58))

PITCH = 4               # px between waveform bars
PERIOD = 360            # bars before the waveform repeats, so the scroll loops cleanly
SCROLL = 30.0           # seconds for one period to pass the playhead


def waveform() -> list[float]:
    """Bar heights from 0 to 1 for one period of a made-up track: verses, builds and drops."""
    rng = random.Random("now-playing")
    out = []
    for i in range(PERIOD):
        phase = i / PERIOD
        # four sections a period; each builds up and then drops back
        section = (phase * 4) % 1
        energy = 0.35 + 0.55 * section ** 1.6
        kick = 1.0 if i % 8 == 0 else 0.0
        out.append(max(0.08, min(1.0, energy * rng.uniform(0.55, 1.0) + 0.2 * kick)))
    return out


def bar_colour(t: Theme, h: float) -> str:
    return t.low if h < 0.5 else t.mid if h < 0.8 else t.high


def hero(t: Theme, L: Layout) -> str:
    W, H, P = L.width, L.height, L.pad
    cx, cy, r = L.wheel
    wy, wh = L.wave
    wx0, wx1 = P + 22, W - P - 22
    mid_y = wy + wh / 2
    play_x = round((wx0 + wx1) / 2)
    period_px = PERIOD * PITCH

    css = [
        f"text{{font-family:{SANS};fill:{t.text}}}",
        f".mono{{font-family:{MONO}}}",
        f".muted{{fill:{t.muted}}}",
        f"@keyframes scroll{{to{{transform:translateX(-{period_px}px)}}}}",
        f".wave{{animation:scroll {SCROLL}s linear infinite}}",
        "@keyframes turn{to{transform:rotate(360deg)}}",
        f".wheel{{transform-origin:{cx}px {cy}px;animation:turn 1.8s linear infinite}}",
        "@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}",
        ".live{animation:blink 1.6s ease-in-out infinite}",
        "@media (prefers-reduced-motion:reduce){.wave,.wheel,.live{animation:none}}",
    ]
    b: list[str] = [f'<rect width="{W}" height="{H}" fill="{t.bg}"/>',
                    f'<rect x="{P}" y="{P - 8}" width="{W - 2 * P}" height="{H - 2 * P + 8}" rx="16" fill="{t.off}" stroke="{t.muted}" stroke-opacity=".25"/>']

    # status line
    sy = P + 24
    b.append(f'<circle class="live" cx="{P + 28}" cy="{sy - 4}" r="4.5" fill="{t.high}"/>')
    b.append(f'<text x="{P + 42}" y="{sy}" class="mono" style="font-size:12px;font-weight:700;letter-spacing:3px">NOW PLAYING</text>')
    b.append(f'<text x="{W - P - 22}" y="{sy}" text-anchor="end" class="mono muted" style="font-size:12px;letter-spacing:3px">DECK A</text>')

    # jog wheel: a platter with grooves and a marker that turns
    grooves = "".join(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{t.muted}" stroke-opacity=".18"/>'
                      for rr in range(int(r * .42), r - 3, 5))
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 5}" fill="{t.bg}" stroke="{t.muted}" stroke-opacity=".35"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#111318"/>{grooves}')
    b.append(f'<g class="wheel"><rect x="{cx - 2}" y="{cy - r + 3}" width="4" height="{r * .34:.0f}" rx="2" fill="{t.high}"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{r * .3:.0f}" fill="{t.mid}"/>'
             f'<circle cx="{cx + r * .17:.0f}" cy="{cy - r * .1:.0f}" r="{max(2, r * .05):.0f}" fill="#0b0d11" opacity=".55"/></g>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="#d7dde5"/>')

    # the track: my name, the role as the artist, then the tagline
    tx = L.text_x
    b.append(f'<text x="{tx}" y="{L.title_y}" style="font-size:{L.title_size}px;font-weight:800;letter-spacing:-.5px">{escape(TITLE)}</text>')
    b.append(f'<text x="{tx}" y="{L.artist_y}" style="font-size:{round(L.title_size * .4)}px;font-weight:700;fill:{t.mid}">{escape(ARTIST)}</text>')
    for i, line in enumerate(L.tagline):
        b.append(f'<text x="{tx}" y="{L.artist_y + 26 + i * 21}" class="muted" style="font-size:{15 if L.name == "wide" else 13.5}px">{escape(line)}</text>')

    # waveform, scrolling under a fixed playhead; the part still to come is dimmed
    heights = waveform()
    visible = (wx1 - wx0) // PITCH + 2
    paths = {t.low: [], t.mid: [], t.high: []}
    for i in range(PERIOD + visible):
        h = heights[i % PERIOD]
        half = max(1.0, h * (wh / 2 - 4))
        paths[bar_colour(t, h)].append(f"M{wx0 + i * PITCH} {mid_y - half:.1f}v{2 * half:.1f}")
    b.append(f'<clipPath id="win"><rect x="{wx0}" y="{wy}" width="{wx1 - wx0}" height="{wh}" rx="8"/></clipPath>')
    b.append(f'<rect x="{wx0}" y="{wy}" width="{wx1 - wx0}" height="{wh}" rx="8" fill="{t.bg}"/>')
    b.append(f'<g clip-path="url(#win)"><g class="wave">' +
             "".join(f'<path d="{"".join(d)}" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>' for c, d in paths.items()) +
             f'</g><rect x="{play_x}" y="{wy}" width="{wx1 - play_x}" height="{wh}" fill="{t.bg}" opacity=".5"/></g>')
    b.append(f'<line x1="{play_x}" y1="{wy - 6}" x2="{play_x}" y2="{wy + wh + 6}" stroke="{t.text}" stroke-width="2"/>'
             f'<polygon points="{play_x - 6},{wy - 10} {play_x + 6},{wy - 10} {play_x},{wy - 3}" fill="{t.text}"/>')

    label = (f"Now playing: {TITLE}, {ARTIST}. {' '.join(L.tagline).replace(' · ', ', ')}. "
             "A DJ deck screen with a turning jog wheel and a waveform scrolling under the playhead.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<style>{"".join(css)}</style>' + "".join(b) + "</svg>\n")


def render() -> dict[str, str]:
    out = {}
    for t in (DARK, LIGHT):
        out[f"studio-hero-{t.name}.svg"] = hero(t, WIDE)
        out[f"studio-hero-phone-{t.name}.svg"] = hero(t, NARROW)
    return out


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for name, text in render().items():
        (ASSETS / name).write_text(text, encoding="utf-8")
    print("wrote studio hero SVGs")


if __name__ == "__main__":
    main()
