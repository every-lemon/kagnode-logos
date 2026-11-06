#!/usr/bin/env python3
"""Rebuild the KagNode artwork from the canonical SVG mark; no external images."""

from pathlib import Path
from html import escape
import json, hashlib, io
import cairosvg
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
font = TTFont(font_path)
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
upm = font["head"].unitsPerEm
SHAPE = '<path d="M4 18C4 9 11 4 23 5L18 27C10 28 4 25 4 18Z"/><path d="m25 11 4 5-3 10-4-3Z"/>'


def text_paths(text, x, y, size, color):
    out = []
    scale = size / upm
    for char in text:
        name = cmap.get(ord(char), ".notdef")
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        if pen.getCommands():
            out.append(
                f'<path fill="{color}" transform="translate({x:g} {y:g}) scale({scale:g} {-scale:g})" d="{pen.getCommands()}"/>'
            )
        x += font["hmtx"].metrics[name][0] * scale
    return "".join(out), x


def svg(label, mark, text=None, stack=False):
    width, height = (64, 64) if text is None else (600, 150) if stack else (600, 100)
    body = f'<!-- PHASE 01: canonical geometric symbol -->\n<g transform="translate(0 0) scale(2)" fill="{mark}">{SHAPE}</g>'
    if text is not None:
        body = f'<!-- PHASE 01: canonical geometric symbol -->\n<g transform="translate(8 14) scale(2)" fill="{mark}">{SHAPE}</g>'
        paths, end = text_paths("KagNode.", 88, 59, 43, text)
        body += "\n<!-- PHASE 02: outlined wordmark, including period -->\n" + paths
        if label:
            paths, end = text_paths(label, 88, 97 if stack else 88, 22, text)
            body += (
                "\n<!-- PHASE 03: product name or editable project placeholder -->\n"
                + paths
            )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape("KagNode. " + label)}">\n<!-- PHASE 00: transparent canvas; geometry and typography are vectors -->\n{body}\n</svg>\n'


variants = {}
for name, color in [("blue", "#2563eb"), ("black", "#111111"), ("white", "#ffffff")]:
    variants["mark-" + name] = svg("", color)
for name, mark, text in [
    ("light", "#2563eb", "#111111"),
    ("dark", "#7da8ff", "#ffffff"),
    ("black", "#111111", "#111111"),
    ("white", "#ffffff", "#ffffff"),
]:
    variants["wordmark-" + name] = svg("", mark, text)
    for product in [
        "Cloud",
        "Developer",
        "Operator",
        "Mail",
        "VPN",
        "HTTP Boot",
        "CLI",
        "[Project]",
    ]:
        key = product.lower().replace(" ", "-").replace("[", "").replace("]", "")
        variants[key + "-" + name] = svg(product, mark, text, True)
for folder in ["svg", "png", "webp", "pdf", "eps", "icons", "ascii"]:
    (ROOT / folder).mkdir(exist_ok=True)
for name, data in variants.items():
    b = data.encode()
    (ROOT / "svg" / f"{name}.svg").write_bytes(b)
    png = cairosvg.svg2png(
        bytestring=b, output_width=1200 if not name.startswith("mark-") else 1024
    )
    (ROOT / "png" / f"{name}.png").write_bytes(png)
    im = Image.open(io.BytesIO(png))
    im.save(ROOT / "webp" / f"{name}.webp", lossless=True)
    cairosvg.svg2pdf(bytestring=b, write_to=str(ROOT / "pdf" / f"{name}.pdf"))
    cairosvg.svg2eps(bytestring=b, write_to=str(ROOT / "eps" / f"{name}.eps"))
mark = variants["mark-blue"].encode()
for size in [16, 32, 48, 64, 128, 180, 256, 512, 1024]:
    cairosvg.svg2png(
        bytestring=mark,
        output_width=size,
        output_height=size,
        write_to=str(ROOT / "icons" / f"kagnode-{size}.png"),
    )
im = Image.open(ROOT / "icons/kagnode-1024.png")
im.save(
    ROOT / "icons/favicon.ico",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
im.save(ROOT / "icons/kagnode.icns")
(ROOT / "icons/favicon.svg").write_bytes(mark)
from ascii_art import write_ascii

write_ascii(ROOT)
from symbols import write_symbols

write_symbols(ROOT)
sheet = (ROOT / "source/KagNode-logo-sheet.svg").read_bytes()
cairosvg.svg2pdf(bytestring=sheet, write_to=str(ROOT / "pdf/logo-sheet.pdf"))
cairosvg.svg2eps(bytestring=sheet, write_to=str(ROOT / "eps/logo-sheet.eps"))
cairosvg.svg2png(
    bytestring=sheet, output_width=1600, write_to=str(ROOT / "png/logo-sheet.png")
)
Image.open(ROOT / "png/logo-sheet.png").save(
    ROOT / "webp/logo-sheet.webp", lossless=True
)
manifest = {
    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in ["svg", "png", "webp", "pdf", "eps", "icons", "ascii", "symbols"]
    for p in sorted((ROOT / folder).rglob("*"))
    if p.is_file() and p.suffix.lower() != ".md"
}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("Generated", len(manifest), "assets")
