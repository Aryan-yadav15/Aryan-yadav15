"""Builds the stats card (all-time contributions, growth, projects, weekly activity, top languages) from the GitHub API.

Usage: GITHUB_TOKEN=... python3 assets/stats.py <user> <out_dir>
Writes <out_dir>/stats-light.svg and stats-dark.svg. Run daily by .github/workflows/profile.yml
so the README never depends on third-party stat servers.
"""
import json
import os
import sys
import urllib.request
from datetime import date
from xml.sax.saxutils import escape

from fonts import font_css

USER, OUT = sys.argv[1], sys.argv[2]
DISPLAY = "'Display','Segoe UI',Helvetica,Arial,sans-serif"
SF = "'Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
FONT_CSS = font_css("Display", "Bricolage Grotesque", "wght@200..800") + font_css("Sans", "Inter", "wght@100..900")
THEMES = {
    "light": dict(bg="#f5f5f7", fg="#1d1d1f", sub="#6e6e73", rule="#d2d2d7", accent="#f56300",
                  langs=["#f56300", "#1d1d1f", "#6e6e73", "#a1a1a6", "#c7c7cc", "#e5e5ea"]),
    "dark": dict(bg="#1c1c1e", fg="#f5f5f7", sub="#86868b", rule="#38383a", accent="#ff9f0a",
                 langs=["#ff9f0a", "#f5f5f7", "#a1a1a6", "#6e6e73", "#48484a", "#2c2c2e"]),
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
    }
  }
}"""


def gql(query=QUERY):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        sys.exit(data["errors"])
    return data["data"]["user"]


def per_year(created):
    """Sum contributions per calendar year since the account was created (the API caps a range at one year)."""
    years = range(int(created[:4]), date.today().year + 1)
    fields = " ".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
        "{ contributionCalendar { totalContributions } }"
        for y in years
    )
    u = gql(f"query($login: String!) {{ user(login: $login) {{ {fields} }} }}")
    return {y: u[f"y{y}"]["contributionCalendar"]["totalContributions"] for y in years}


def growth(years):
    """Year-over-year tile: '3×' when the jump is big, '+40%' when modest, else just this year's count."""
    this, last = years[date.today().year], years.get(date.today().year - 1, 0)
    if last and this >= 2 * last:
        return f"{this / last:.0f}×", f"more than {date.today().year - 1}"
    if last and this > last:
        return f"+{100 * (this - last) / last:.0f}%", f"vs {date.today().year - 1}"
    return f"{this:,}", f"contributions in {date.today().year}"


def rise(begin, dy=10):
    ease = 'calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .2 1"'
    return (f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" dur="1s" fill="freeze" {ease}/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 {dy}" to="0 0" begin="{begin}s" dur="1.2s" fill="freeze" {ease}/>')


def card(t, d):
    W, H = 1200, 420
    tiles = [(f"{d['total']:,}", "contributions all-time"), growth(d["years"]), (f"{d['repos'] // 5 * 5}+", "projects shipped")]
    tile_svg = []
    for i, (num, label) in enumerate(tiles):
        x = 40 + i * 380
        div = f'<rect x="{x - 20}" y="96" width="1" height="74" fill="{t["rule"]}"/>' if i else ""
        tile_svg.append(
            f'{div}<g opacity="0">{rise(.2 + i * .12)}'
            f'<text x="{x}" y="146" font-family="{DISPLAY}" font-size="60" font-weight="800" letter-spacing="-2" fill="{t["fg"]}">{num}</text>'
            f'<text x="{x + 2}" y="172" font-family="{SF}" font-size="14" fill="{t["sub"]}">{label}</text></g>'
        )

    # weekly activity line
    cx, cy, cw, ch = 40, 232, 700, 130
    weekly = d["weekly"]
    peak = max(weekly) or 1
    step = cw / max(len(weekly) - 1, 1)
    pts = [(cx + i * step, cy + ch - (v / peak) * ch) for i, v in enumerate(weekly)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    length = sum(((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** 0.5 for i in range(len(pts) - 1))
    px, py = max(pts, key=lambda p: -p[1])

    # languages as a ranked list with hairline bars
    lx, ly = 820, 232
    langs = []
    for i, (name, share) in enumerate(d["langs"][:5]):
        y = ly + i * 27
        langs.append(
            f'<g opacity="0">{rise(.9 + i * .08, 6)}'
            f'<text x="{lx}" y="{y + 12}" font-family="{SF}" font-size="14" font-weight="600" fill="{t["fg"]}">{escape(name)}</text>'
            f'<rect x="{lx + 120}" y="{y + 4}" width="190" height="6" rx="3" fill="{t["rule"]}"/>'
            f'<rect x="{lx + 120}" y="{y + 4}" width="{max(190 * share / d["langs"][0][1], 6):.0f}" height="6" rx="3" fill="{t["langs"][0] if i == 0 else t["fg"]}"/>'
            f'<text x="{lx + 340}" y="{y + 12}" text-anchor="end" font-family="{SF}" font-size="13" fill="{t["sub"]}">{share:.0f}%</text></g>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats for {USER}">
<style>{FONT_CSS}</style>
<rect width="{W}" height="{H}" rx="28" fill="{t['bg']}"/>
<text x="40" y="58" font-family="{SF}" font-size="12" font-weight="700" letter-spacing="2.2" fill="{t['accent']}">BY THE NUMBERS</text>
<text x="{W - 40}" y="58" text-anchor="end" font-family="{SF}" font-size="12" fill="{t['sub']}">Updated {date.today():%d %b %Y}</text>
<rect x="40" y="74" width="{W - 80}" height="1" fill="{t['fg']}"/>
{''.join(tile_svg)}
<text x="{cx}" y="214" font-family="{SF}" font-size="12" font-weight="600" letter-spacing="1.5" fill="{t['sub']}">WEEKLY CONTRIBUTIONS · 12 MONTHS</text>
<rect x="{cx}" y="{cy + ch}" width="{cw}" height="1" fill="{t['rule']}"/>
<polyline points="{line}" fill="none" stroke="{t['fg']}" stroke-width="2" stroke-linejoin="round" stroke-dasharray="{length:.0f}" stroke-dashoffset="{length:.0f}">
  <animate attributeName="stroke-dashoffset" to="0" dur="2.2s" begin=".4s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/>
</polyline>
<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{t['accent']}" opacity="0"><animate attributeName="opacity" to="1" begin="2.4s" dur=".4s" fill="freeze"/></circle>
<text x="{min(px + 10, cx + cw - 70):.0f}" y="{py + 4:.0f}" font-family="{SF}" font-size="12" fill="{t['sub']}" opacity="0">peak {peak}<animate attributeName="opacity" to="1" begin="2.4s" dur=".4s" fill="freeze"/></text>
<rect x="780" y="206" width="1" height="160" fill="{t['rule']}"/>
<text x="{lx}" y="214" font-family="{SF}" font-size="12" font-weight="600" letter-spacing="1.5" fill="{t['sub']}">TOP LANGUAGES</text>
{''.join(langs)}
</svg>
"""


def main():
    u = gql()
    cal = u["contributionsCollection"]["contributionCalendar"]
    years = per_year(u["createdAt"])
    sizes = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
    total = sum(sizes.values()) or 1
    d = dict(
        total=sum(years.values()), years=years, repos=u["repositories"]["totalCount"],
        weekly=[sum(x["contributionCount"] for x in w["contributionDays"]) for w in cal["weeks"]],
        langs=[(k, 100 * v / total) for k, v in sorted(sizes.items(), key=lambda kv: -kv[1])],
    )
    os.makedirs(OUT, exist_ok=True)
    for mode, t in THEMES.items():
        with open(os.path.join(OUT, f"stats-{mode}.svg"), "w") as f:
            f.write(card(t, d))
    print(f"wrote stats-{{light,dark}}.svg: {d['total']} all-time, {years}")


main()
