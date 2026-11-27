"""Render the animated SVGs used by the profile README.

GitHub serves README images through its image proxy and strips scripts, so all
motion here is CSS keyframes inside the SVG. Every asset is drawn twice, once
per GitHub theme, and the README picks one with <picture> + prefers-color-scheme.

    python scripts/build_assets.py     # writes assets/*.svg
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    panel: str
    term: str
    border: str
    text: str
    muted: str
    accent: str
    accent2: str
    green: str
    purple: str


DARK = Theme("dark", "#0d1117", "#161b22", "#010409", "#30363d",
             "#e6edf3", "#8b949e", "#2dd4bf", "#f0b429", "#3fb950", "#a371f7")
LIGHT = Theme("light", "#ffffff", "#f6f8fa", "#ffffff", "#d0d7de",
              "#1f2328", "#59636e", "#0f766e", "#9a6700", "#1a7f37", "#8250df")


# ---------------------------------------------------------------------------
# Hero: name, tagline, and a terminal that asks the live RAG demo a question
# ---------------------------------------------------------------------------
CYCLE = 18.0          # seconds per loop
FADE_OUT = (94.0, 97.0)  # % of the cycle where everything fades together
CHAR_W = 8.1          # advance width of 13.5px monospace, close enough for a cover rect


def pct(seconds: float) -> float:
    return round(seconds / CYCLE * 100, 2)


def appear(name: str, at: float) -> str:
    """Keyframes: hidden until `at` seconds, fade in over 0.35s, hold, fade with the rest."""
    a, b = pct(at), pct(at + 0.35)
    return (f"@keyframes {name}{{0%,{a}%{{opacity:0;transform:translateY(4px)}}"
            f"{b}%,{FADE_OUT[0]}%{{opacity:1;transform:none}}"
            f"{FADE_OUT[1]}%,100%{{opacity:0}}}}")


def typing(name: str, start: float, end: float, width: float, chars: int) -> str:
    """Keyframes that slide a cover rect right one character at a time."""
    s, e = pct(start), pct(end)
    return (f"@keyframes {name}{{0%,{s}%{{transform:translateX(0);animation-timing-function:steps({chars},end)}}"
            f"{e}%,{FADE_OUT[1]}%{{transform:translateX({width:.1f}px)}}"
            f"{FADE_OUT[1] + 0.5}%,100%{{transform:translateX(0)}}}}")


def hero(t: Theme) -> str:
    W, H = 960, 470
    tx, ty, tw, th = 24, 150, W - 48, 296          # terminal window
    lx = tx + 22                                    # text left edge
    question = 'ask "how does the payments pipeline ignore a stale, replayed CDC event?"'
    q_w = (len(question) + 1) * CHAR_W

    trace = [
        ("plan", "decompose multi-part questions into sub-queries"),
        ("retrieve", "vector search per sub-query, top-k 5"),
        ("fuse", "reciprocal rank fusion across sub-queries"),
        ("assess", "broaden and retry if coverage is weak (max 2 rounds)"),
    ]
    answer = [
        "The MERGE guards on cdc_lsn > target.cdc_lsn, so a stale event",
        "re-applied after a newer one is ignored. LSN, not ts_ms: the",
        "timestamp has millisecond resolution and two changes can tie.  [1]",
    ]

    css = [
        f"text{{font-family:{MONO};font-size:13.5px;fill:{t.text}}}",
        f".sans{{font-family:{SANS}}}",
        f".muted{{fill:{t.muted}}}",
        f".acc{{fill:{t.accent}}}",
        f".acc2{{fill:{t.accent2}}}",
        f".grn{{fill:{t.green}}}",
        f".pur{{fill:{t.purple}}}",
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}",
        "@keyframes pulse{0%{transform:scale(1);opacity:.9}70%,100%{transform:scale(2.8);opacity:0}}",
        "@keyframes sweep{0%{transform:translateX(-320px)}100%{transform:translateX(980px)}}",
        f".cursor{{animation:blink 1s step-end infinite}}",
        f".ring{{animation:pulse 2.2s ease-out infinite;transform-box:fill-box;transform-origin:center}}",
        f".sweep{{animation:sweep 6s linear infinite}}",
        typing("type", 0.6, 3.4, q_w, len(question) + 1),
        f".typer{{animation:type {CYCLE}s infinite}}",
    ]

    body: list[str] = []
    # header
    body.append(f'<text x="24" y="58" class="sans" style="font-size:34px;font-weight:700;letter-spacing:-.5px">Harshit Gadge</text>')
    body.append(f'<text x="24" y="90" class="sans muted" style="font-size:16px">AI engineer &#183; data engineer &#8212; I build AI and data systems, then measure whether they work.</text>')
    body.append(f'<circle cx="31" cy="116" r="4" fill="{t.green}"/><circle cx="31" cy="116" r="4" fill="none" stroke="{t.green}" stroke-width="2" class="ring"/>')
    body.append(f'<text x="44" y="120.5" class="sans" style="font-size:13.5px"><tspan class="grn" style="font-weight:600">open to work</tspan><tspan class="muted"> &#183; AI Engineer &#183; Data Engineer &#183; Data Scientist</tspan></text>')
    body.append(f'<text x="{W-24}" y="120.5" text-anchor="end" class="sans muted" style="font-size:13px">MS Data Science, UMD &#183; patent co-inventor</text>')

    # terminal chrome
    body.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="10" fill="{t.term}" stroke="{t.border}"/>')
    body.append(f'<path d="M{tx} {ty+10}a10 10 0 0 1 10-10h{tw-20}a10 10 0 0 1 10 10v20h-{tw}z" fill="{t.panel}"/>')
    body.append(f'<line x1="{tx}" y1="{ty+30}" x2="{tx+tw}" y2="{ty+30}" stroke="{t.border}"/>')
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        body.append(f'<circle cx="{tx+18+i*18}" cy="{ty+15}" r="5.5" fill="{c}"/>')
    body.append(f'<text x="{tx+tw/2}" y="{ty+19.5}" text-anchor="middle" class="muted" style="font-size:12px">agentic-rag-service &#8212; portfolio Q&amp;A</text>')
    # light sweep along the title bar
    body.append(f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{t.accent}" stop-opacity="0"/><stop offset=".5" stop-color="{t.accent}" stop-opacity=".9"/><stop offset="1" stop-color="{t.accent}" stop-opacity="0"/></linearGradient>'
                f'<clipPath id="tc"><rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="10"/></clipPath></defs>')
    body.append(f'<g clip-path="url(#tc)"><rect class="sweep" x="0" y="{ty+29}" width="300" height="2" fill="url(#g)"/></g>')

    # line 1: typed question
    y = ty + 58
    body.append(f'<text x="{lx}" y="{y}"><tspan class="acc">harshit@portfolio</tspan><tspan class="muted">:~$ </tspan></text>')
    qx = lx + len("harshit@portfolio:~$ ") * CHAR_W
    body.append(f'<text x="{qx}" y="{y}">{escape(question)}</text>')
    body.append(f'<g clip-path="url(#tc)"><g class="typer"><rect x="{qx}" y="{y-14}" width="{q_w+12}" height="20" fill="{t.term}"/>'
                f'<rect class="cursor" x="{qx}" y="{y-12}" width="8" height="16" fill="{t.accent}"/></g></g>')

    # trace
    y += 32
    for i, (stage, note) in enumerate(trace):
        name = f"tr{i}"
        css.append(appear(name, 3.9 + i * 0.55))
        css.append(f".{name}{{animation:{name} {CYCLE}s infinite}}")
        body.append(f'<g class="{name}"><text x="{lx}" y="{y}" xml:space="preserve"><tspan class="pur">&#9656; </tspan>'
                    f'<tspan class="acc2">{stage:<9}</tspan><tspan class="muted"> {escape(note)}</tspan></text></g>')
        y += 22

    # answer
    y += 12
    css.append(appear("ah", 6.4))
    css.append(f".ah{{animation:ah {CYCLE}s infinite}}")
    body.append(f'<g class="ah"><text x="{lx}" y="{y}"><tspan class="grn">&#10003; answer</tspan>'
                f'<tspan class="muted">  extractive &#183; grounded in retrieved passages</tspan></text></g>')
    y += 24
    for i, line in enumerate(answer):
        name = f"an{i}"
        css.append(appear(name, 7.0 + i * 0.45))
        css.append(f".{name}{{animation:{name} {CYCLE}s infinite}}")
        body.append(f'<g class="{name}"><text x="{lx}" y="{y}" xml:space="preserve">{escape(line)}</text></g>')
        y += 21
    y += 6
    css.append(appear("ci", 8.7))
    css.append(f".ci{{animation:ci {CYCLE}s infinite}}")
    body.append(f'<g class="ci"><text x="{lx}" y="{y}"><tspan class="acc">[1]</tspan>'
                f'<tspan class="muted"> payments-data-platform/README.md &#183; &#8220;The problems this is built around&#8221;</tspan></text></g>')

    return svg(W, H, t, css, body, "Harshit Gadge: an animated terminal asking the portfolio Q&A service a question and showing the cited answer")


# ---------------------------------------------------------------------------
# Project cards
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Card:
    slug: str
    kicker: str
    title: str
    lines: tuple[str, str]
    metric: str
    metric_label: tuple[str, str]
    chips: tuple[str, ...]


CARDS = [
    Card("capability-runtime", "AGENTIC AI", "capability-runtime",
         ("An LLM learns a web workflow once; it then", "replays deterministically, with a human for risky steps."),
         "0", ("model calls per", "production replay"),
         ("TypeScript", "Playwright", "Claude", "84 tests")),
    Card("agentic-rag-service", "RAG · EVALUATION", "agentic-rag-service",
         ("Query decomposition, hybrid search and cited", "answers, tuned against a real benchmark."),
         "+5.0", ("nDCG@10 on SciFact", "95% CI +3.1 to +6.9"),
         ("FastAPI", "ChromaDB", "ONNX", "97 tests")),
    Card("payments-data-platform", "DATA ENGINEERING", "payments-data-platform",
         ("Postgres CDC into an Iceberg lakehouse with an", "idempotent, LSN-guarded MERGE, plus an FX warehouse."),
         "102", ("tests, one named after", "each way CDC corrupts data"),
         ("Debezium", "Kafka", "Spark", "Iceberg", "dbt")),
    Card("kafka-databricks-nasa", "STREAMING", "kafka-databricks-nasa",
         ("NASA's real-time gamma-ray burst alerts into a", "Unity Catalog medallion lakehouse."),
         "33", ("tests: parser, Spark", "transforms, data model"),
         ("Kafka OAuth", "Structured Streaming", "Delta")),
    Card("medicare-claims-analytics", "HEALTHCARE ANALYTICS", "medicare-claims-analytics",
         ("dbt pipeline over 116k synthetic beneficiaries:", "PMPM, readmissions, a high-cost model."),
         "+6.7", ("pts of next year's high-cost", "members found on a 5% list"),
         ("dbt", "DuckDB", "LightGBM", "Streamlit")),
    Card("Detecting_Fradulent_job", "RISK · FRAUD", "fraud screening",
         ("Rules vs. models for fake job posts under a", "fixed review budget, tested on unseen posters."),
         "77%", ("of fraud caught reviewing", "the top 5% by risk"),
         ("DuckDB SQL", "scikit-learn", "LightGBM")),
]


def card(c: Card, t: Theme, delay: float) -> str:
    W, H = 460, 200
    css = [
        f"text{{font-family:{SANS};fill:{t.text}}}",
        f".mono{{font-family:{MONO}}}",
        f".muted{{fill:{t.muted}}}",
        f".acc{{fill:{t.accent}}}",
        "@keyframes sweep{0%{transform:translateX(-200px)}60%,100%{transform:translateX(660px)}}",
        f".sweep{{animation:sweep 7s ease-in-out {delay:.1f}s infinite;transform:translateX(-200px)}}",
    ]
    b: list[str] = []
    b.append(f'<defs><linearGradient id="s" x1="0" x2="1"><stop offset="0" stop-color="{t.accent}" stop-opacity="0"/>'
             f'<stop offset=".5" stop-color="{t.accent}"/><stop offset="1" stop-color="{t.accent}" stop-opacity="0"/></linearGradient>'
             f'<clipPath id="c"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12"/></clipPath></defs>')
    b.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" fill="{t.panel}" stroke="{t.border}"/>')
    b.append(f'<g clip-path="url(#c)"><rect class="sweep" x="0" y="0" width="180" height="3" fill="url(#s)"/></g>')
    b.append(f'<text x="22" y="34" class="acc" style="font-size:11px;font-weight:700;letter-spacing:1.4px">{escape(c.kicker)}</text>')
    b.append(f'<text x="22" y="60" class="mono" style="font-size:18px;font-weight:600">{escape(c.title)}</text>')
    for i, line in enumerate(c.lines):
        b.append(f'<text x="22" y="{88 + i*20}" class="muted" style="font-size:13px">{escape(line)}</text>')
    # metric block on the right
    b.append(f'<line x1="22" y1="134" x2="{W-22}" y2="134" stroke="{t.border}"/>')
    b.append(f'<text x="22" y="176" class="mono acc" style="font-size:28px;font-weight:700">{escape(c.metric)}</text>')
    mx = 22 + len(c.metric) * 17.5 + 12
    b.append(f'<text x="{mx}" y="162" class="muted" style="font-size:11.5px">{escape(c.metric_label[0])}</text>')
    b.append(f'<text x="{mx}" y="177" class="muted" style="font-size:11.5px">{escape(c.metric_label[1])}</text>')
    # chips, top-right on the kicker row
    x = W - 20
    for chip in reversed(c.chips[:3]):
        w = len(chip) * 6.6 + 16
        x -= w
        b.append(f'<rect x="{x:.1f}" y="18" width="{w:.1f}" height="22" rx="11" fill="none" stroke="{t.border}"/>'
                 f'<text x="{x + w/2:.1f}" y="33" text-anchor="middle" class="mono muted" style="font-size:11px">{escape(chip)}</text>')
        x -= 6
    b.append(f'<text x="{W-22}" y="176" text-anchor="end" class="acc" style="font-size:12.5px;font-weight:600">view repo &#8594;</text>')
    return svg(W, H, t, css, b, f"{c.title}: {c.metric} {' '.join(c.metric_label)}")


def svg(w: int, h: int, t: Theme, css: list[str], body: list[str], label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><style>{"".join(css)}</style>'
            + "".join(body) + "</svg>\n")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for t in (DARK, LIGHT):
        (ASSETS / f"hero-{t.name}.svg").write_text(hero(t), encoding="utf-8")
        for i, c in enumerate(CARDS):
            (ASSETS / f"card-{c.slug.lower()}-{t.name}.svg").write_text(card(c, t, delay=i * 1.1), encoding="utf-8")
    print(f"wrote {len(list(ASSETS.glob('*.svg')))} SVGs to {ASSETS}")


if __name__ == "__main__":
    main()
