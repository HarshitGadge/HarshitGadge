"""Render 1280x640 social-preview PNGs (the image LinkedIn/Slack/X show for a repo link).

    python scripts/build_social.py     # writes social/<repo>.png via headless Chrome
"""
from __future__ import annotations

import asyncio
from html import escape
from pathlib import Path

from build_assets import CARDS, MONO, SANS

OUT = Path(__file__).resolve().parent.parent / "social"
REPO = {c.slug: c.slug for c in CARDS} | {"Detecting_Fradulent_job": "Detecting_Fradulent_job"}

ACCENTS = {  # one hue per project so a feed of shares doesn't look identical
    "agentic-rag-service": ("#2dd4bf", "#0ea5e9"),
    "capability-runtime": ("#a78bfa", "#f472b6"),
    "payments-data-platform": ("#f0b429", "#fb7185"),
    "kafka-databricks-nasa": ("#60a5fa", "#a78bfa"),
    "medicare-claims-analytics": ("#34d399", "#2dd4bf"),
    "Detecting_Fradulent_job": ("#fb7185", "#f0b429"),
}


def page(c) -> str:
    a, b = ACCENTS[c.slug]
    chips = "".join(f'<span class="chip">{escape(x)}</span>' for x in c.chips)
    return f"""<!doctype html><html><head><style>
*{{box-sizing:border-box;margin:0}}
body{{width:1280px;height:640px;background:#0b0f17;color:#e6edf3;font-family:{SANS};overflow:hidden;position:relative}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(#ffffff08 1px,transparent 1px),linear-gradient(90deg,#ffffff08 1px,transparent 1px);background-size:40px 40px;mask-image:radial-gradient(ellipse at 70% 40%,#000 20%,transparent 75%)}}
.glow{{position:absolute;width:760px;height:760px;right:-180px;top:-260px;border-radius:50%;background:radial-gradient(circle,{a}55,transparent 62%);filter:blur(10px)}}
.glow2{{position:absolute;width:620px;height:620px;left:-260px;bottom:-360px;border-radius:50%;background:radial-gradient(circle,{b}40,transparent 62%)}}
.wrap{{position:absolute;inset:64px 72px;display:flex;flex-direction:column}}
.kicker{{font-size:22px;letter-spacing:4px;font-weight:700;color:{a}}}
h1{{font-family:{MONO};font-size:{66 if len(c.title) < 20 else 56}px;font-weight:700;letter-spacing:-1px;margin-top:18px;
   background:linear-gradient(90deg,#fff,{a});-webkit-background-clip:text;color:transparent}}
.line{{font-size:28px;color:#9aa7b4;margin-top:18px;line-height:1.4;max-width:900px}}
.metric{{display:flex;align-items:baseline;gap:22px;margin-top:auto}}
.num{{font-family:{MONO};font-size:120px;font-weight:800;line-height:1;color:{a};text-shadow:0 0 40px {a}66}}
.lbl{{font-size:26px;color:#c9d1d9;line-height:1.35}}
.foot{{display:flex;justify-content:space-between;align-items:center;margin-top:34px;padding-top:24px;border-top:1px solid #ffffff1a}}
.chip{{font-family:{MONO};font-size:19px;border:1px solid #ffffff2e;border-radius:999px;padding:7px 16px;margin-right:10px;color:#c9d1d9}}
.who{{font-family:{MONO};font-size:20px;color:#8b949e}}
.who b{{color:#e6edf3}}
</style></head><body><div class="grid"></div><div class="glow"></div><div class="glow2"></div>
<div class="wrap">
  <div class="kicker">{escape(c.kicker)}</div>
  <h1>{escape(c.title)}</h1>
  <div class="line">{escape(c.lines[0] + " " + c.lines[1])}</div>
  <div class="metric"><div class="num">{escape(c.metric)}</div><div class="lbl">{escape(c.metric_label[0])}<br>{escape(c.metric_label[1])}</div></div>
  <div class="foot"><div>{chips}</div><div class="who"><b>Harshit Gadge</b> · github.com/HarshitGadge</div></div>
</div></body></html>"""


async def main() -> None:
    from playwright.async_api import async_playwright

    OUT.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await browser.new_page(viewport={"width": 1280, "height": 640})
        for c in CARDS:
            await pg.set_content(page(c))
            await pg.screenshot(path=str(OUT / f"{c.slug}.png"))
        await browser.close()
    print(f"wrote {len(CARDS)} PNGs to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
