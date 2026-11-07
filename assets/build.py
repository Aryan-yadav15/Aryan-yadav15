"""Generates the README's hero and about cards, each in a light and dark variant.

Run: python3 assets/build.py
Style: editorial layout (masthead, rules, ticker) with Apple-keynote restraint
(system sans, generous space, rise-in motion). Pure SVG + SMIL so it animates inside GitHub's <img>.
"""
import sys
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from fonts import font_css, text_width

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent

# display face (name, letter, numbers) + UI sans; both embedded so every OS renders them identically
DISPLAY_FAMILY, DISPLAY_SPEC, DW = "Bricolage Grotesque", "wght@200..800", 800
SANS_FAMILY, SANS_SPEC = "Inter", "wght@100..900"
FONT_CSS = font_css("Display", DISPLAY_FAMILY, DISPLAY_SPEC) + font_css("Sans", SANS_FAMILY, SANS_SPEC)
DISPLAY = "'Display','Segoe UI',Helvetica,Arial,sans-serif"
# size the name so it spans the same width whatever the display face's proportions
NAME_SIZE = min(190, 152 * 930 / text_width(DISPLAY_FAMILY, DISPLAY_SPEC, "Aryan Yadav.", 152, -4))
SF = "'Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

THEMES = {
    "light": dict(bg="#f5f5f7", fg="#1d1d1f", sub="#6e6e73", rule="#d2d2d7", accent="#f56300", ok="#28a745"),
    "dark": dict(bg="#1c1c1e", fg="#f5f5f7", sub="#86868b", rule="#38383a", accent="#ff9f0a", ok="#32d74b"),
}

TICKER = ["KhaoGully", "DocRAG for VS Code", "AI Form Filler", "NLP → SQL", "Deloitte · Walmart hackathons"]


def rise(begin, dy=16):
    ease = 'calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"'
    return (f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="1s" fill="freeze" {ease}/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 {dy}" to="0 0" begin="{begin}s" dur="1.2s" fill="freeze" {ease}/>')


def hero(mode):
    t = THEMES[mode]
    W, H = 1200, 440
    ticker = "     •     ".join(TICKER) + "     •     "
    tick_w = len(ticker) * 8.6  # approx advance of 14px SF with 2px tracking
    badge = "OPEN TO WORK • OPEN TO WORK • "
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Aryan Yadav. Full stack. Fully shipped.">
<style>{FONT_CSS}</style>
<defs>
  <clipPath id="pill"><rect x="40" y="366" width="{W - 80}" height="44" rx="22"/></clipPath>
  <path id="ring" d="M0,-54 a54,54 0 1,1 0,108 a54,54 0 1,1 0,-108"/>
</defs>
<rect width="{W}" height="{H}" rx="28" fill="{t['bg']}"/>

<g font-family="{SF}" font-size="12" font-weight="600" letter-spacing="2.2" fill="{t['sub']}" opacity="0">{rise(.1, 0)}
  <text x="40" y="46">ISSUE Nº 15</text>
  <text x="{W / 2}" y="46" text-anchor="middle" fill="{t['fg']}">THE PORTFOLIO OF ARYAN YADAV</text>
  <text x="{W - 40}" y="46" text-anchor="end">INDIA · EST. 2021</text>
</g>
<rect x="40" y="62" height="1" width="0" fill="{t['fg']}"><animate attributeName="width" to="{W - 80}" begin=".2s" dur="1.1s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/></rect>

<g opacity="0">{rise(.4, 22)}
  <text x="34" y="222" font-family="{DISPLAY}" font-size="{NAME_SIZE:.0f}" font-weight="{DW}" letter-spacing="-4" fill="{t['fg']}">Aryan Yadav<tspan fill="{t['accent']}">.</tspan></text>
</g>
<g opacity="0">{rise(.8)}
  <text x="42" y="282" font-family="{SF}" font-size="34" font-weight="600" letter-spacing="-.6" fill="{t['sub']}">Full stack. <tspan fill="{t['fg']}">Fully shipped.</tspan></text>
</g>
<g opacity="0">{rise(1.05, 10)}
  <text x="42" y="322" font-family="{SF}" font-size="20" fill="{t['sub']}">Whole products, from first schema to last pixel.</text>
</g>

<g transform="translate(1084 284)"><g opacity="0">{rise(1.2, 0)}
  <circle r="72" fill="none" stroke="{t['rule']}"/>
  <g><text font-family="{SF}" font-size="11" font-weight="600" letter-spacing="3.9" fill="{t['fg']}"><textPath href="#ring">{badge}</textPath></text>
    <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="24s" repeatCount="indefinite"/></g>
  <circle r="9" fill="{t['ok']}"><animate attributeName="r" values="9;11;9" dur="2.4s" repeatCount="indefinite"/></circle>
  <circle r="9" fill="none" stroke="{t['ok']}"><animate attributeName="r" values="9;26" dur="2.4s" repeatCount="indefinite"/><animate attributeName="opacity" values=".7;0" dur="2.4s" repeatCount="indefinite"/></circle>
</g></g>

<g opacity="0">{rise(1.4, 10)}
  <rect x="40" y="366" width="{W - 80}" height="44" rx="22" fill="{t['fg']}"/>
  <g clip-path="url(#pill)" font-family="{SF}" font-size="14" font-weight="600" letter-spacing="2" fill="{t['bg']}">
    <text x="64" y="393">{escape(ticker.upper() * 4)}<animateTransform attributeName="transform" type="translate" from="0 0" to="-{tick_w:.0f} 0" dur="26s" repeatCount="indefinite"/></text>
  </g>
</g>
</svg>
"""
    (OUT / f"hero-{mode}.svg").write_text(svg)


LEAD = "I build products end to end."
LETTER = (
    "Right now that's KhaoGully, a food-ordering platform where I build "
    "every surface: the customer app, the restaurant dashboard, delivery navigation, inventory and the "
    "economics behind it. On the side I make the tools I want to use myself, like a VS Code extension "
    "that feeds fresh docs to Copilot, a browser extension that fills forms with AI, and plain-English "
    "search over databases."
)
SPECS = [
    ("Based in", "India"),
    ("Building", "KhaoGully"),
    ("Focus", "AI · Mobile · 3D"),
    ("Languages", "TypeScript · Python · Kotlin"),
    ("Status", "Open to work"),
]


def about(mode):
    t = THEMES[mode]
    W = 1200
    lines = textwrap.wrap(f"{LEAD} {LETTER}", 66, break_on_hyphens=False)
    y0, lh = 112, 36
    para = []
    for i, line in enumerate(lines):
        if i == 0 and line.startswith(LEAD):
            # the opening sentence is set bold, the rest in the regular weight
            line = f'<tspan font-weight="700">{escape(LEAD)}</tspan>{escape(line[len(LEAD):])}'
        else:
            line = escape(line)
        para.append(f'<text x="40" y="{y0 + i * lh}" xml:space="preserve">{line}</text>')
    H = max(y0 + len(lines) * lh + 30, 120 + len(SPECS) * 52 + 20)

    spec = []
    for i, (k, v) in enumerate(SPECS):
        y = 100 + i * 52
        dot = f'<circle cx="{850 + len(v) * 9.6 + 12:.0f}" cy="{y + 33}" r="5" fill="{t["ok"]}"/>' if k == "Status" else ""
        spec.append(
            f'<g opacity="0">{rise(.5 + i * .12, 8)}'
            f'<rect x="850" y="{y}" width="310" height="1" fill="{t["rule"]}"/>'
            f'<text x="850" y="{y + 20}" font-size="12" fill="{t["sub"]}">{k}</text>'
            f'<text x="850" y="{y + 40}" font-size="18" font-weight="600" fill="{t["fg"]}">{escape(v)}</text>{dot}</g>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="From the engineer">
<style>{FONT_CSS}</style>
<rect width="{W}" height="{H}" rx="28" fill="{t['bg']}"/>
<g opacity="0">{rise(.1, 8)}
  <text x="40" y="58" font-family="{SF}" font-size="12" font-weight="700" letter-spacing="2.2" fill="{t['accent']}">FROM THE ENGINEER</text>
  <text x="850" y="58" font-family="{SF}" font-size="12" font-weight="700" letter-spacing="2.2" fill="{t['accent']}">AT A GLANCE</text>
</g>
<g opacity="0">{rise(.3, 12)}
  <g font-family="{DISPLAY}" font-size="23" fill="{t['fg']}">{''.join(para)}</g>
</g>
<g font-family="{SF}">{''.join(spec)}</g>
<rect x="788" y="84" width="1" height="{H - 120}" fill="{t['rule']}"/>
</svg>
"""
    (OUT / f"about-{mode}.svg").write_text(svg)


for m in THEMES:
    hero(m)
    about(m)
print("wrote hero-{light,dark}.svg, about-{light,dark}.svg")
