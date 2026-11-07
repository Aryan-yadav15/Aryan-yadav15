"""Embeds Google Fonts into SVGs so GitHub's <img> sandbox (which blocks external fonts) still renders them.

Fonts are fetched once into assets/fonts/, subset to the characters we use, and inlined as base64 woff2.
Needs: pip install fonttools brotli
"""
import base64
import io
import re
import urllib.parse
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

CACHE = Path(__file__).parent / "fonts"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
CHARS = "".join(chr(c) for c in range(32, 127)) + "·•→×—–’‘“”…№º"


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read()


def fetch(family, spec):
    """Download the latin woff2 files for a css2 spec, e.g. ("Inter", "wght@100..900").
    Returns [(path, style, weight)] where weight is "400" or a range like "100 900"."""
    CACHE.mkdir(exist_ok=True)
    q = urllib.parse.quote(family) + (f":{spec}" if spec else "")
    css = _get(f"https://fonts.googleapis.com/css2?family={q}&display=swap").decode()
    faces = []
    for block in re.findall(r"/\* latin \*/\s*@font-face\s*{([^}]*)}", css):
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
        style = re.search(r"font-style:\s*(\w+)", block).group(1)
        weight = re.search(r"font-weight:\s*([\d ]+);", block).group(1).strip()
        path = CACHE / f"{family.replace(' ', '')}-{style}-{weight.replace(' ', '_')}.woff2"
        if not path.exists():
            path.write_bytes(_get(url))
        faces.append((path, style, weight))
    if not faces:
        raise SystemExit(f"no latin faces for {family} {spec}")
    return faces


def _subset(path):
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt", "lnum", "pnum"]
    opts.name_IDs = []
    opts.notdef_outline = True
    font = TTFont(path)
    s = subset.Subsetter(opts)
    s.populate(text=CHARS)
    s.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def font_css(alias, family, spec):
    """@font-face rules registering `family` under `alias`, ready to drop into an SVG <style>."""
    # dedupe: variable fonts return one file for several weight blocks
    seen, rules = set(), []
    for path, style, weight in fetch(family, spec):
        if (path, style) in seen:
            continue
        seen.add((path, style))
        rules.append(
            f"@font-face{{font-family:'{alias}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{_subset(path)}) format('woff2')}}"
        )
    return "".join(rules)


def text_width(family, spec, text, size, tracking=0.0, style="normal"):
    """Advance width of `text` in px at `size`, from the font's metrics (default instance for variable fonts)."""
    path = next(p for p, st, _ in fetch(family, spec) if st == style)
    font = TTFont(path)
    cmap, hmtx, upm = font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    units = sum(hmtx[cmap[ord(c)]][0] for c in text if ord(c) in cmap)
    return units / upm * size + tracking * (len(text) - 1)
