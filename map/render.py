"""Draws map/projects.json as the README's project-embedding map (light + dark SVG).

Usage: python map/render.py   (after map/embed.py)
"""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "assets"))
from fonts import font_css  # noqa: E402

DATA = json.loads((ROOT / "map" / "projects.json").read_text())
DISPLAY = "'Display','Segoe UI',Helvetica,Arial,sans-serif"
SF = "'Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
FONT_CSS = font_css("Display", "Bricolage Grotesque", "wght@200..800") + font_css("Sans", "Inter", "wght@100..900")

THEMES = {
    "light": dict(bg="#f5f5f7", fg="#1d1d1f", sub="#6e6e73", rule="#d2d2d7", accent="#f56300",
                  dom=["#f56300", "#0071e3", "#28a745", "#af52de", "#8e8e93"]),
    "dark": dict(bg="#1c1c1e", fg="#f5f5f7", sub="#86868b", rule="#38383a", accent="#ff9f0a",
                 dom=["#ff9f0a", "#0a84ff", "#30d158", "#bf5af2", "#98989d"]),
}
ORDER = ["Food & delivery", "AI & developer tools", "Commerce & operations", "Community & realtime", "Brand sites & portfolios"]
# projects worth naming on the map; everything else is an unlabelled dot
LABELS = {
    "KhaoGully-Main-website": "KhaoGully", "khaooGully-customer-web": "Customer app",
    "KhaoGully-restraunt-facing": "Restaurant dashboard", "khaao-gully-navigator": "Rider navigator",
    "DocAiAssist": "DocRAG", "formfillerAi-Browser-extension": "AI Form Filler", "Database-NLP-Query": "NLP → SQL",
    "Ai-github": "Repo Insights", "Hackathon": "Email RPA bot", "Thrift_Track": "Thrift Track",
    "inventory-management": "Inventory", "WoodpeckerStockSmart": "StockSmart", "CampusBuzz": "CampusBuzz",
    "MultiLang-ChatApp": "MultiLang Chat", "MailMesh-Delloite-Hackathon": "MailMesh", "LMS-Client": "LMS",
    "RealEstate-Chat": "Real-estate chat", "Interverse_video": "Interverse", "Blend": "Blend", "karya_studios_v2": "Karya Studios", "My-Portfolio": "Portfolio",
}
PX, PY, PW, PH = 70, 120, 700, 400  # plot area


def layout():
    ps = DATA["projects"]
    xs, ys = [p["x"] for p in ps], [p["y"] for p in ps]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for p in ps:
        p["px"] = PX + (p["x"] - x0) / (x1 - x0) * PW
        p["py"] = PY + (p["y"] - y0) / (y1 - y0) * PH
    return ps


def place_labels(ps):
    """Greedy: try right, left, above, below each labelled dot; skip spots that collide."""
    boxes = [(p["px"] - 7, p["py"] - 7, p["px"] + 7, p["py"] + 7) for p in ps]
    out = []
    for p in sorted(ps, key=lambda p: p["name"] not in LABELS):
        text = LABELS.get(p["name"])
        if not text:
            continue
        w, h = len(text) * 7.4, 15
        for dx, dy, anchor in [(11, 4, "start"), (-11, 4, "end"), (0, -12, "middle"), (0, 20, "middle")]:
            x = p["px"] + dx
            left = x if anchor == "start" else x - w if anchor == "end" else x - w / 2
            box = (left - 2, p["py"] + dy - 12, left + w + 2, p["py"] + dy + 3)
            if not any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1] for b in boxes):
                boxes.append(box)
                out.append((x, p["py"] + dy, anchor, text, p))
                break
    return out


def render(mode):
    t = THEMES[mode]
    ps = layout()
    color = {d: t["dom"][i] for i, d in enumerate(ORDER)}
    W, H = 1200, 580

    # soft halo per dot: overlapping halos darken where a domain is dense, without hulls stretched by outliers
    blobs = [f'<circle cx="{p["px"]:.1f}" cy="{p["py"]:.1f}" r="30" fill="{color[p["domain"]]}" opacity=".10"/>' for p in ps]

    dots = []
    for i, p in enumerate(sorted(ps, key=lambda p: p["px"])):
        big = p["name"] in LABELS
        r = 7 if big else 5
        dots.append(
            f'<a href="{p["url"]}"><circle cx="{p["px"]:.1f}" cy="{p["py"]:.1f}" r="0" fill="{color[p["domain"]]}">'
            f'<title>{escape(p["name"])} · {escape(p["domain"])}</title>'
            f'<animate attributeName="r" from="0" to="{r}" begin="{0.3 + i * 0.03:.2f}s" dur=".5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"/></circle></a>'
        )

    labels = "".join(
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{a}" font-family="{SF}" font-size="12.5" font-weight="{600 if p["domain"] == ORDER[0] else 500}" '
        f'fill="{t["fg"]}" opacity="0">{escape(text)}<animate attributeName="opacity" to="1" begin="1.6s" dur=".6s" fill="freeze"/></text>'
        for x, y, a, text, p in place_labels(ps)
    )

    legend = []
    for i, d in enumerate(ORDER):
        n = sum(p["domain"] == d for p in ps)
        y = 150 + i * 62
        legend.append(
            f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{0.8 + i * 0.12:.2f}s" dur=".6s" fill="freeze"/>'
            f'<rect x="850" y="{y - 22}" width="310" height="1" fill="{t["rule"]}"/>'
            f'<circle cx="858" cy="{y}" r="7" fill="{color[d]}"/>'
            f'<text x="876" y="{y + 5}" font-family="{DISPLAY}" font-size="19" font-weight="700" fill="{t["fg"]}">{escape(d)}</text>'
            f'<text x="1160" y="{y + 5}" text-anchor="end" font-family="{DISPLAY}" font-size="19" font-weight="700" fill="{t["sub"]}">{n}</text></g>'
        )

    caption = f"{len(ps)} repos · {DATA['model'].split('/')[-1]} ({DATA['dims']}-d) · UMAP to 2D · zero-shot domain labels"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Map of {len(ps)} projects in embedding space, grouped by domain">
<style>{FONT_CSS}</style>
<rect width="{W}" height="{H}" rx="28" fill="{t['bg']}"/>
<text x="40" y="58" font-family="{SF}" font-size="12" font-weight="700" letter-spacing="2.2" fill="{t['accent']}">PROJECT EMBEDDING SPACE</text>
<text x="{W - 40}" y="58" text-anchor="end" font-family="{SF}" font-size="12" fill="{t['sub']}">{escape(caption)}</text>
<rect x="40" y="74" width="{W - 80}" height="1" fill="{t['fg']}"/>
<g opacity="0"><animate attributeName="opacity" to="1" begin=".1s" dur="1.2s" fill="freeze"/>{''.join(blobs)}</g>
{''.join(dots)}
{labels}
<text x="850" y="112" font-family="{SF}" font-size="12" font-weight="600" letter-spacing="1.5" fill="{t['sub']}">DOMAINS</text>
{''.join(legend)}
<text x="850" y="{150 + len(ORDER) * 62 - 6}" font-family="{SF}" font-size="12.5" fill="{t['sub']}">Nearby dots = similar code and purpose.</text>
<text x="850" y="{150 + len(ORDER) * 62 + 14}" font-family="{SF}" font-size="12.5" fill="{t['sub']}">Rebuilt from the repos by map/embed.py.</text>
</svg>
"""
    (ROOT / "assets" / f"map-{mode}.svg").write_text(svg)


for m in THEMES:
    render(m)
print("wrote assets/map-{light,dark}.svg")
