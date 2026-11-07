"""Builds the toolkit card: tools grouped by domain, as logo chips (light + dark SVG).

Run: python3 assets/toolkit.py
Logos come from Simple Icons (CC0), cached in assets/icons/. Tools without a logo get a dot.
"""
import re
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from fonts import font_css, text_width

OUT = Path(__file__).parent
ICONS = OUT / "icons"
DISPLAY = "'Display','Segoe UI',Helvetica,Arial,sans-serif"
SF = "'Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
FONT_CSS = font_css("Display", "Bricolage Grotesque", "wght@200..800") + font_css("Sans", "Inter", "wght@100..900")

THEMES = {
    "light": dict(bg="#f5f5f7", fg="#1d1d1f", sub="#6e6e73", rule="#d2d2d7", chip="#ffffff", accent="#f56300"),
    "dark": dict(bg="#1c1c1e", fg="#f5f5f7", sub="#86868b", rule="#38383a", chip="#2c2c2e", accent="#ff9f0a"),
}

# (domain, one-line proof, [(label, simple-icons slug or None)])
STACK = [
    ("AI & ML", "Agents, RAG and embeddings in real tools", [
        ("Gemini", "googlegemini"), ("LangChain", "langchain"), ("Transformers.js", "huggingface"),
        ("RAG pipelines", None), ("Vector search", "sqlite"), ("Embeddings · UMAP", None),
        ("LLM tool orchestration", None),
    ]),
    ("Mobile", "Native Android and cross-platform apps", [
        ("Kotlin", "kotlin"), ("Jetpack Compose", "jetpackcompose"), ("Hilt · Room", "android"),
        ("React Native", "react"), ("Expo", "expo"), ("Firebase FCM", "firebase"), ("Razorpay", "razorpay"),
    ]),
    ("Web", "Product frontends, dashboards and maps", [
        ("TypeScript", "typescript"), ("React", "react"), ("Next.js", "nextdotjs"), ("Tailwind", "tailwindcss"),
        ("TanStack Query", "reactquery"), ("Redux", "redux"), ("MapLibre", "maplibre"), ("Leaflet", "leaflet"),
    ]),
    ("Backend & data", "APIs, queues, realtime and geospatial", [
        ("FastAPI", "fastapi"), ("Python", "python"), ("Node.js", "nodedotjs"), ("PostgreSQL · PostGIS", "postgresql"),
        ("Supabase", "supabase"), ("Redis", "redis"), ("Celery", "celery"), ("SQLAlchemy", "sqlalchemy"),
        ("Prisma", "prisma"), ("Drizzle", "drizzle"), ("MongoDB", "mongodb"), ("WebSockets", "socketdotio"),
        ("Docker", "docker"), ("H3 geo-indexing", None),
    ]),
    ("Automation", "Scrapers, bots, schedulers and RPA", [
        ("Playwright", "playwright"), ("UiPath", "uipath"), ("Web scraping", None), ("Cron · APScheduler", None),
        ("launchd agents", None), ("Android Accessibility", "android"), ("GitHub Actions", "githubactions"),
    ]),
    ("3D & graphics", "Photoreal 3D from phone captures", [
        ("Blender · Cycles", "blender"), ("Gaussian splatting", None), ("COLMAP", None), ("Three.js", "threedotjs"),
        ("Spark", None), ("OpenCV", "opencv"), ("FFmpeg", "ffmpeg"),
    ]),
    ("Design", "Interfaces and motion", [
        ("Figma", "figma"), ("Illustrator", "adobeillustrator"), ("Photoshop", "adobephotoshop"), ("Lottie", "lottiefiles"),
    ]),
]


def icon_path(slug):
    """The single <path d> of a Simple Icons glyph (24x24 viewBox), cached locally."""
    ICONS.mkdir(exist_ok=True)
    f = ICONS / f"{slug}.svg"
    if not f.exists():
        url = f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg"
        f.write_bytes(urllib.request.urlopen(url).read())
    return re.search(r'<path d="([^"]+)"', f.read_text()).group(1)


def render(mode):
    t = THEMES[mode]
    W, LX, CX, CR = 1200, 40, 330, 1160  # width, label column x, chips x, chips right edge
    CH, GAP, ROWGAP = 34, 10, 10
    y, rows = 108, []
    for i, (domain, proof, tools) in enumerate(STACK):
        top = y
        x, chips = CX, []
        for label, slug in tools:
            w = 14 + (24 if slug else 16) + text_width("Inter", "wght@100..900", label, 14) * 1.03 + 14
            if x + w > CR:
                x, y = CX, y + CH + ROWGAP
            mark = (f'<g transform="translate({x + 14:.1f} {y + 9}) scale(.6667)"><path d="{icon_path(slug)}" fill="{t["fg"]}"/></g>'
                    if slug else f'<circle cx="{x + 18:.1f}" cy="{y + CH / 2}" r="4" fill="{t["accent"]}"/>')
            chips.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{CH}" rx="{CH / 2}" fill="{t["chip"]}" stroke="{t["rule"]}"/>{mark}'
                f'<text x="{x + (38 if slug else 30):.1f}" y="{y + 22}" font-family="{SF}" font-size="14" font-weight="500" fill="{t["fg"]}">{escape(label)}</text>'
            )
            x += w + GAP
        bottom = max(y + CH, top + 46)
        rows.append(
            f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{0.15 + i * 0.12:.2f}s" dur=".7s" fill="freeze"/>'
            f'<text x="{LX}" y="{top + 22}" font-family="{DISPLAY}" font-size="22" font-weight="800" letter-spacing="-.3" fill="{t["fg"]}">{escape(domain)}</text>'
            f'<text x="{LX}" y="{top + 42}" font-family="{SF}" font-size="12.5" fill="{t["sub"]}">{escape(proof)}</text>'
            f'{"".join(chips)}</g>'
        )
        y = bottom + 22
        if i < len(STACK) - 1:
            rows.append(f'<rect x="{LX}" y="{y - 11}" width="{W - 2 * LX}" height="1" fill="{t["rule"]}"/>')
            y += 11
    H = y + 18
    count = sum(len(tools) for _, _, tools in STACK)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Toolkit: {escape(', '.join(d for d, _, _ in STACK))}">
<style>{FONT_CSS}</style>
<rect width="{W}" height="{H}" rx="28" fill="{t['bg']}"/>
<text x="40" y="58" font-family="{SF}" font-size="12" font-weight="700" letter-spacing="2.2" fill="{t['accent']}">THE TOOLKIT</text>
<text x="{W - 40}" y="58" text-anchor="end" font-family="{SF}" font-size="12" fill="{t['sub']}">{count} tools across {len(STACK)} domains, all used in real projects</text>
<rect x="40" y="74" width="{W - 80}" height="1" fill="{t['fg']}"/>
{''.join(rows)}
</svg>
"""
    (OUT / f"toolkit-{mode}.svg").write_text(svg)


for m in THEMES:
    render(m)
print("wrote toolkit-{light,dark}.svg")
