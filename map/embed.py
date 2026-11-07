"""Embeds every public repo and projects the vectors to 2D for the README's project map.

Each repo becomes one document: its name, description, README (minus framework boilerplate),
dependencies, and the names of the files/routes it contains. Documents are embedded with
BAAI/bge-small-en-v1.5, assigned to a domain by zero-shot classification (cosine similarity to an
embedded description of each domain), and laid out in 2D with UMAP (cosine).

Usage: python map/embed.py   (needs: gh CLI logged in; pip install fastembed scikit-learn umap-learn)
Writes map/projects.json, which map/render.py turns into the SVG.
"""
import base64
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import umap
from fastembed import TextEmbedding

USER = "Aryan-yadav15"
OUT = Path(__file__).parent / "projects.json"
DOMAINS = {
    "Food & delivery": "restaurant food ordering and delivery: menus and dishes, restaurant owner dashboard, customer food app, delivery riders and navigation",
    "AI & developer tools": "AI tools built on LLMs: retrieval augmented generation, embeddings, vector search, Gemini, LangChain, natural language to SQL, code and repository analysis, browser and IDE extensions, robotic process automation",
    "Commerce & operations": "e-commerce and business operations: product catalog, inventory and stock, sales and transactions analytics, price tracking and scraping, retail admin dashboards",
    "Community & realtime": "community platforms: events and ticketing, campus clubs, courses and workshops, chat and messaging, video, team workspaces, email collaboration",
    "Brand sites & portfolios": "personal and client websites: portfolios, about me, studio and brand landing pages, showcase galleries, scroll animations, contact forms",
}

BOILERPLATE = re.compile(
    r"create-next-app|create react app|getting started|npm (run|start|test|install)|yarn |pnpm |bun dev|"
    r"localhost:3000|learn more|vercel platform|deploy on vercel|available scripts|next/font|geist|"
    r"you can start editing|auto-updates|this project was bootstrapped|ejected|code splitting|nextjs\.org|next\.js|"
    r"tutorial|feedback and contributions|deployment|vercel\.com|font optimization", re.I)
# UI plumbing every app shares; it says nothing about what the app is for
NOISE_DEPS = re.compile(r"^(react|react-dom|next|clsx|tailwind.*|class-variance-authority|lucide-react|@radix-ui/.*|"
                        r"@types/.*|eslint.*|postcss|autoprefixer|typescript|framer-motion|react-icons|@tabler/.*|"
                        r"@heroicons/.*|next-themes|web-vitals|@testing-library/.*|react-scripts|zod|axios)$")
GENERIC = set("""index layout page route src app apps components component ui lib libs utils util config configs
package json tsconfig eslint eslintrc next readme globals global css scss js ts tsx jsx mjs cjs md public styles
style button card dialog input label select textarea toast tooltip sheet separator skeleton avatar badge tabs form
dropdown menu popover accordion alert checkbox slider switch table scroll area navigation hover collapsible aspect
ratio icons icon types type hooks hook context provider providers vite postcss tailwind gitignore env example test
tests spec mock mocks setup main home not found loading error middleware api lib actions action store data assets
images img fonts font favicon manifest robots sitemap license changelog prettierrc babel metro expo android ios
lock jsconfig vitals report web text project link module jest
node modules dist build out vercel netlify docker dockerfile yml yaml github workflows git keep logo header footer
navbar sidebar hero section sections wrapper container root client server shared common helpers helper constants
constant theme themes models model schema schemas services service controllers controller routes router db""".split())

# Hand corrections where the classifier misreads thin repos. Kept explicit so the map stays honest.
OVERRIDES = {
    "Opal": "Community & realtime",            # team video workspace; its routes look like a storefront
    "Hackathon": "AI & developer tools",       # UiPath email-automation bot
    "WalmartHackathon": "Commerce & operations",
}
SKIP = {"ai-bot"}  # untouched Create React App template


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


def words(s):
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    return [w.lower() for w in re.split(r"[^A-Za-z]+", s) if len(w) > 2]


def document(repo):
    name = repo["name"]
    parts = [" ".join(words(name)), repo.get("description") or ""]

    readme = gh(f"repos/{USER}/{name}/readme")
    if readme:
        text = base64.b64decode(readme["content"]).decode("utf-8", "ignore")
        lines = [ln for ln in text.splitlines() if ln.strip() and not BOILERPLATE.search(ln)]
        parts.append(re.sub(r"[`#*>\[\]()!|_-]+", " ", " ".join(lines))[:1500])

    pkg = gh(f"repos/{USER}/{name}/contents/package.json")
    if pkg:
        try:
            deps = json.loads(base64.b64decode(pkg["content"]))
            useful = [d for d in deps.get("dependencies", {}) if not NOISE_DEPS.match(d)]
            parts.append("uses " + " ".join(useful[:20]))
        except ValueError:
            pass

    tree = gh(f"repos/{USER}/{name}/git/trees/{repo['default_branch']}?recursive=1") or {}
    seen = []
    for item in tree.get("tree", []):
        p = item["path"]
        if re.search(r"node_modules|\.git/|public/|\.(png|jpe?g|svg|ico|gif|webp|lock|map|woff2?|ttf|mp4)$", p):
            continue
        for w in words(re.sub(r"\.\w+$", "", p)):
            if w not in GENERIC and w not in seen:
                seen.append(w)
    parts.append("features " + " ".join(seen[:120]))
    return " . ".join(p for p in parts if p).strip(), len(seen)


def main():
    repos = [r for r in gh(f"users/{USER}/repos?per_page=100") if not r["fork"] and r["name"] not in SKIP | {USER}]
    docs = []
    for r in repos:
        text, n_paths = document(r)
        if n_paths < 2 and len(text) < 80:  # empty placeholder repo
            continue
        docs.append({"name": r["name"], "url": r["html_url"], "lang": r["language"], "text": text})
        print(f"  {r['name']:<32} {len(text):>5} chars")

    model = TextEmbedding("BAAI/bge-small-en-v1.5")
    X = np.array(list(model.embed([d["text"] for d in docs])))
    X /= np.linalg.norm(X, axis=1, keepdims=True)

    names = list(DOMAINS)
    A = np.array(list(model.embed([f"Represent this sentence for searching relevant passages: {DOMAINS[n]}" for n in names])))
    A /= np.linalg.norm(A, axis=1, keepdims=True)
    sims = X @ A.T
    # some descriptions sit closer to everything; z-score each domain's column so they compete fairly
    labels = ((sims - sims.mean(0)) / sims.std(0)).argmax(1)
    xy = umap.UMAP(n_neighbors=6, min_dist=0.35, metric="cosine", random_state=7).fit_transform(X)

    for d, (x, y), c in zip(docs, xy, labels):
        d.update(x=float(x), y=float(y), domain=OVERRIDES.get(d["name"], names[c]), corrected=d["name"] in OVERRIDES)
        del d["text"]
    OUT.write_text(json.dumps({"model": "BAAI/bge-small-en-v1.5", "dims": int(X.shape[1]), "projects": docs}, indent=1))
    for n in names:
        print(n, [d["name"] for d in docs if d["domain"] == n])


main()
