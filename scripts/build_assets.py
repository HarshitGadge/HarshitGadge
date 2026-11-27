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
# Hero: name, tagline, and a terminal that asks the live RAG demo questions
# ---------------------------------------------------------------------------
# Every answer below is copied, not written. Each one is a single cited sentence
# taken verbatim from the live service's response to exactly that question
# (POST https://agentic-rag-service-fxsc.onrender.com/query). The full responses
# are saved in scripts/hero_responses.json, and check_answers() refuses to build
# if a sentence, its [n] marker or its source file stops matching them.
RESPONSES = Path(__file__).resolve().parent / "hero_responses.json"


@dataclass(frozen=True)
class QA:
    question: str
    sentence: str      # verbatim from the response's `answer`, whitespace collapsed
    marker: str        # the [n] that follows the sentence in the response
    source: str        # citations[n-1].source in the same response


QAS = [
    QA("how does the payments pipeline ignore a stale, replayed CDC event?",
       "The MERGE guards on `cdc_lsn > target.cdc_lsn`, so a stale event re-applied after a newer one is ignored.",
       "[5]", "demo/corpus/payments-data-platform/README.md"),
    QA("how are hospital readmissions defined in the Medicare claims project?",
       "**Readmissions:** an index stay is discharged alive with 30 days of follow-up left in the data, "
       "and a readmission is any stay starting 1–30 days later.",
       "[1]", "demo/corpus/medicare-claims-analytics/README.md"),
    QA("how does capability-runtime replay a workflow without calling a model?",
       "The model never sees the portal — deterministic replay runs underneath each tool call, "
       "and the model reasons only about the task and the typed result.",
       "[5]", "demo/corpus/capability-runtime/README.md"),
]


def check_answers() -> None:
    """Fail the build unless every hero answer is the service's own words and citation."""
    import json
    import re

    def flat(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip()

    responses = {r["question"]: r for r in json.loads(RESPONSES.read_text(encoding="utf-8"))}
    for qa in QAS:
        r = responses.get(qa.question)
        assert r is not None, f"no saved response for {qa.question!r}"
        assert f"{qa.sentence} {qa.marker}" in flat(r["answer"]), f"not verbatim in the response: {qa.sentence!r}"
        n = int(qa.marker.strip("[]"))
        assert r["citations"][n - 1]["source"] == qa.source, f"{qa.marker} is not {qa.source}"


SLOT = 18.0                     # seconds each question stays on screen
CYCLE = SLOT * len(QAS)         # one full loop through every question
SLOT_FADE = (0.94, 0.97)        # fraction of a slot where its content fades out


def pct(seconds: float) -> float:
    return round(seconds / CYCLE * 100, 3)


def appear(name: str, at: float, slot: int) -> str:
    """Keyframes: hidden until `at` seconds into `slot`, fade in over 0.35s, hold, fade with the slot."""
    base = slot * SLOT
    a, b = pct(base + at), pct(base + at + 0.35)
    f0, f1 = pct(base + SLOT * SLOT_FADE[0]), pct(base + SLOT * SLOT_FADE[1])
    return (f"@keyframes {name}{{0%,{a}%{{opacity:0;transform:translateY(4px)}}"
            f"{b}%,{f0}%{{opacity:1;transform:none}}"
            f"{f1}%,100%{{opacity:0}}}}")


def window(name: str, a: float, b: float, slot: int) -> str:
    """Keyframes: fully visible from `a` to `b` seconds into `slot`, hidden otherwise (hard cuts)."""
    base = slot * SLOT
    s, e = pct(base + a), pct(base + b)
    parts = []
    if s > 0:
        parts.append(f"0%,{round(s - 0.001, 3)}%{{opacity:0}}")
    parts.append(f"{s}%,{e}%{{opacity:1}}")
    if e < 100:
        parts.append(f"{round(e + 0.001, 3)}%,100%{{opacity:0}}")
    return f"@keyframes {name}{{{''.join(parts)}}}"


def typing(name: str, start: float, end: float, width: float, chars: int, slot: int) -> str:
    """Keyframes that slide a cover rect right one character at a time within `slot`."""
    base = slot * SLOT
    s, e = pct(base + start), pct(base + end)
    f1 = pct(base + SLOT * SLOT_FADE[1])
    return (f"@keyframes {name}{{0%,{s}%{{transform:translateX(0);animation-timing-function:steps({chars},end)}}"
            f"{e}%,{f1}%{{transform:translateX({width:.1f}px)}}"
            f"{round(f1 + 0.5, 3)}%,100%{{transform:translateX(0)}}}}")


def wrap(text: str, width: int) -> list[str]:
    """Greedy word wrap that keeps every character of `text` (lines rejoin with single spaces)."""
    lines: list[str] = []
    cur = ""
    for word in text.split(" "):
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    lines.append(cur)
    return lines


@dataclass(frozen=True)
class HeroLayout:
    """Geometry for one hero size. `wide` is the desktop banner, `narrow` the phone one."""
    name: str
    W: int
    mono: float          # monospace font size in the terminal
    char_w: float        # advance width at that size, close enough for a cover rect
    line_h: float        # terminal line height
    q_wrap: int          # characters per question line (0: one line after the prompt)
    a_wrap: int          # characters per answer line
    trace: tuple[tuple[str, str], ...]
    answer_note: str


WIDE = HeroLayout(
    "wide", 960, 13.5, 8.1, 22, 0, 100,
    (("plan", "decompose multi-part questions into sub-queries"),
     ("retrieve", "vector search per sub-query, top-k 5"),
     ("fuse", "reciprocal rank fusion across sub-queries"),
     ("assess", "broaden and retry if coverage is weak (max 2 rounds)")),
    "  extractive · excerpt, cited to the retrieved passage",
)
NARROW = HeroLayout(
    "narrow", 480, 15.0, 9.0, 24, 44, 44,
    (("plan", "split multi-part questions"),
     ("retrieve", "vector search, top-k 5"),
     ("fuse", "reciprocal rank fusion"),
     ("assess", "retry if coverage is weak")),
    "  extractive · cited excerpt",
)


def hero(t: Theme, L: HeroLayout) -> str:
    W = L.W
    narrow = L is NARROW
    css = [
        f"text{{font-family:{MONO};font-size:{L.mono}px;fill:{t.text}}}",
        f".sans{{font-family:{SANS}}}",
        f".muted{{fill:{t.muted}}}",
        f".acc{{fill:{t.accent}}}",
        f".acc2{{fill:{t.accent2}}}",
        f".grn{{fill:{t.green}}}",
        f".pur{{fill:{t.purple}}}",
        f".sm{{font-size:{L.mono - 2}px}}",
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}",
        "@keyframes pulse{0%{transform:scale(1);opacity:.9}70%,100%{transform:scale(2.8);opacity:0}}",
        f"@keyframes sweep{{0%{{transform:translateX(-320px)}}100%{{transform:translateX({W + 20}px)}}}}",
        ".cursor{animation:blink 1s step-end infinite}",
        ".ring{animation:pulse 2.2s ease-out infinite;transform-box:fill-box;transform-origin:center}",
        f".sweep{{animation:sweep {6 if not narrow else 4}s linear infinite}}",
    ]

    body: list[str] = []
    # header
    if narrow:
        m = 20
        body.append(f'<text x="{m}" y="50" class="sans" style="font-size:30px;font-weight:700;letter-spacing:-.5px">Harshit Gadge</text>')
        body.append(f'<text x="{m}" y="80" class="sans muted" style="font-size:16px">AI engineer &#183; data engineer &#8212; I build AI</text>')
        body.append(f'<text x="{m}" y="102" class="sans muted" style="font-size:16px">and data systems, then measure whether they work.</text>')
        body.append(f'<circle cx="{m + 7}" cy="129" r="4.5" fill="{t.green}"/><circle cx="{m + 7}" cy="129" r="4.5" fill="none" stroke="{t.green}" stroke-width="2" class="ring"/>')
        body.append(f'<text x="{m + 20}" y="134" class="sans grn" style="font-size:15px;font-weight:600">open to work</text>')
        body.append(f'<text x="{m}" y="160" class="sans muted" style="font-size:15px">AI Engineer &#183; Data Engineer &#183; Data Scientist</text>')
        body.append(f'<text x="{m}" y="184" class="sans muted" style="font-size:15px">MS Data Science, UMD &#183; patent co-inventor</text>')
        tx, ty = 14, 204
    else:
        body.append('<text x="24" y="58" class="sans" style="font-size:34px;font-weight:700;letter-spacing:-.5px">Harshit Gadge</text>')
        body.append('<text x="24" y="90" class="sans muted" style="font-size:16px">AI engineer &#183; data engineer &#8212; I build AI and data systems, then measure whether they work.</text>')
        body.append(f'<circle cx="31" cy="116" r="4" fill="{t.green}"/><circle cx="31" cy="116" r="4" fill="none" stroke="{t.green}" stroke-width="2" class="ring"/>')
        body.append('<text x="44" y="120.5" class="sans" style="font-size:13.5px"><tspan class="grn" style="font-weight:600">open to work</tspan><tspan class="muted"> &#183; AI Engineer &#183; Data Engineer &#183; Data Scientist</tspan></text>')
        body.append(f'<text x="{W - 24}" y="120.5" text-anchor="end" class="sans muted" style="font-size:13px">MS Data Science, UMD &#183; patent co-inventor</text>')
        tx, ty = 24, 150
    tw = W - 2 * tx
    lx = tx + (18 if narrow else 22)
    bar = 34 if narrow else 30

    # Lay out every slot first, so the terminal is tall enough for the longest answer.
    prompt = "harshit@portfolio:~$ "
    slots = []
    tallest = 0.0
    for qa in QAS:
        asked = f'ask "{qa.question}"'
        q_lines = wrap(asked, L.q_wrap) if L.q_wrap else [asked]
        a_lines = wrap(f"{qa.sentence} {qa.marker}", L.a_wrap)
        y = bar + 28                                   # first line, relative to the terminal top
        q_ys = [y + (i + (1 if L.q_wrap else 0)) * L.line_h for i in range(len(q_lines))]
        y = q_ys[-1] + L.line_h + 10                    # trace
        tr_y = y
        y += len(L.trace) * L.line_h + 12               # answer header
        ah_y = y
        y += L.line_h + 2
        a_ys = [y + i * (L.line_h - 1) for i in range(len(a_lines))]
        y = a_ys[-1] + L.line_h + 4                     # citation
        ci_y = y
        y += (L.line_h - 2) if narrow else 0
        tallest = max(tallest, y + (22 if narrow else 24))
        slots.append((qa, q_lines, q_ys, tr_y, ah_y, a_lines, a_ys, ci_y))
    th = round(tallest)
    H = ty + th + (20 if narrow else 24)

    # terminal chrome
    body.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="10" fill="{t.term}" stroke="{t.border}"/>')
    body.append(f'<path d="M{tx} {ty + 10}a10 10 0 0 1 10-10h{tw - 20}a10 10 0 0 1 10 10v{bar - 10}h-{tw}z" fill="{t.panel}"/>')
    body.append(f'<line x1="{tx}" y1="{ty + bar}" x2="{tx + tw}" y2="{ty + bar}" stroke="{t.border}"/>')
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        body.append(f'<circle cx="{tx + 18 + i * 18}" cy="{ty + bar / 2}" r="5.5" fill="{c}"/>')
    title = "agentic-rag-service &#8212; portfolio Q&amp;A"
    body.append(f'<text x="{tx + tw / 2}" y="{ty + bar / 2 + 4.5}" text-anchor="middle" class="muted" style="font-size:12px">{title}</text>')
    body.append(f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{t.accent}" stop-opacity="0"/><stop offset=".5" stop-color="{t.accent}" stop-opacity=".9"/><stop offset="1" stop-color="{t.accent}" stop-opacity="0"/></linearGradient>'
                f'<clipPath id="tc"><rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="10"/></clipPath></defs>')
    body.append(f'<g clip-path="url(#tc)"><rect class="sweep" x="0" y="{ty + bar - 1}" width="300" height="2" fill="url(#g)"/></g>')

    # one dot per question in the title bar; the current one lights up
    for k in range(len(QAS)):
        cx = tx + tw - 18 - (len(QAS) - 1 - k) * 14
        body.append(f'<circle cx="{cx}" cy="{ty + bar / 2}" r="3.5" fill="none" stroke="{t.muted}" stroke-width="1.2"/>')
        css.append(window(f"dot{k}", 0, SLOT, k))
        css.append(f".dot{k}{{animation:dot{k} {CYCLE}s infinite}}")
        body.append(f'<circle class="dot{k}" cx="{cx}" cy="{ty + bar / 2}" r="3.5" fill="{t.accent}"/>')

    for k, (qa, q_lines, q_ys, tr_y, ah_y, a_lines, a_ys, ci_y) in enumerate(slots):
        css.append(window(f"s{k}", 0, SLOT, k))
        css.append(f".s{k}{{animation:s{k} {CYCLE}s infinite}}")
        body.append(f'<g class="s{k}">')

        # typed question; a cover rect slides off each line in turn
        y0 = ty + q_ys[0] - (L.line_h if L.q_wrap else 0)
        body.append(f'<text x="{lx}" y="{y0}"><tspan class="acc">harshit@portfolio</tspan><tspan class="muted">:~$ </tspan></text>')
        qx0 = lx if L.q_wrap else lx + len(prompt) * L.char_w
        total = sum(len(s) for s in q_lines)
        start, per_char = 0.6, 0.038
        for i, (line, ly) in enumerate(zip(q_lines, q_ys)):
            y = ty + ly
            chars = len(line) + 1
            end = start + chars * per_char
            w = chars * L.char_w
            name = f"q{k}_{i}"
            css.append(typing(name, start, end, w, chars, k))
            css.append(f".{name}{{animation:{name} {CYCLE}s infinite}}")
            body.append(f'<text x="{qx0}" y="{y}" xml:space="preserve">{escape(line)}</text>')
            last = i == len(q_lines) - 1
            css.append(window(f"k{k}_{i}", 0 if i == 0 else start, SLOT * SLOT_FADE[1] if last else end, k))
            css.append(f".k{k}_{i}{{animation:k{k}_{i} {CYCLE}s infinite}}")
            cursor = (f'<g class="k{k}_{i}"><rect class="cursor" x="{qx0}" y="{y - L.mono + 2}" '
                      f'width="{L.char_w:.1f}" height="{L.mono + 2}" fill="{t.accent}"/></g>')
            body.append(f'<g clip-path="url(#tc)"><g class="{name}"><rect x="{qx0}" y="{y - L.mono - 0.5}" width="{w + 14:.1f}" height="{L.line_h}" fill="{t.term}"/>{cursor}</g></g>')
            start = end
        typed_end = start
        assert total > 0

        # trace
        for i, (stage, note) in enumerate(L.trace):
            name = f"t{k}_{i}"
            css.append(appear(name, typed_end + 0.5 + i * 0.55, k))
            css.append(f".{name}{{animation:{name} {CYCLE}s infinite}}")
            body.append(f'<g class="{name}"><text x="{lx}" y="{ty + tr_y + i * L.line_h}" xml:space="preserve"><tspan class="pur">&#9656; </tspan>'
                        f'<tspan class="acc2">{stage:<9}</tspan><tspan class="muted"> {escape(note)}</tspan></text></g>')
        t_ans = typed_end + 0.5 + len(L.trace) * 0.55 + 0.5

        # answer
        name = f"h{k}"
        css.append(appear(name, t_ans, k))
        css.append(f".{name}{{animation:{name} {CYCLE}s infinite}}")
        body.append(f'<g class="{name}"><text x="{lx}" y="{ty + ah_y}" xml:space="preserve"><tspan class="grn">&#10003; answer</tspan>'
                    f'<tspan class="muted">{escape(L.answer_note)}</tspan></text></g>')
        for i, (line, ly) in enumerate(zip(a_lines, a_ys)):
            name = f"a{k}_{i}"
            css.append(appear(name, t_ans + 0.6 + i * 0.45, k))
            css.append(f".{name}{{animation:{name} {CYCLE}s infinite}}")
            body.append(f'<g class="{name}"><text x="{lx}" y="{ty + ly}" xml:space="preserve">{escape(line)}</text></g>')

        name = f"c{k}"
        css.append(appear(name, t_ans + 0.6 + len(a_lines) * 0.45 + 0.4, k))
        css.append(f".{name}{{animation:{name} {CYCLE}s infinite}}")
        live = "live at agentic-rag-service-fxsc.onrender.com"
        if narrow:
            body.append(f'<g class="{name}"><text x="{lx}" y="{ty + ci_y}" class="sm"><tspan class="acc">{qa.marker}</tspan>'
                        f'<tspan class="muted"> {escape(qa.source)}</tspan></text>'
                        f'<text x="{lx}" y="{ty + ci_y + L.line_h - 2}" class="sm muted">{live}</text></g>')
        else:
            body.append(f'<g class="{name}"><text x="{lx}" y="{ty + ci_y}"><tspan class="acc">{qa.marker}</tspan>'
                        f'<tspan class="muted"> {escape(qa.source)} &#183; {live}</tspan></text></g>')
        body.append("</g>")

    label = ("Harshit Gadge: an animated terminal asks the portfolio Q&A service three questions in turn "
             "and shows each cited answer")
    return svg(W, H, t, css, body, label)


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
    check_answers()
    ASSETS.mkdir(exist_ok=True)
    for t in (DARK, LIGHT):
        (ASSETS / f"hero-{t.name}.svg").write_text(hero(t, WIDE), encoding="utf-8")
        (ASSETS / f"hero-phone-{t.name}.svg").write_text(hero(t, NARROW), encoding="utf-8")
        for i, c in enumerate(CARDS):
            (ASSETS / f"card-{c.slug.lower()}-{t.name}.svg").write_text(card(c, t, delay=i * 1.1), encoding="utf-8")
    print(f"wrote {len(list(ASSETS.glob('*.svg')))} SVGs to {ASSETS}")


if __name__ == "__main__":
    main()
