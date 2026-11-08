#!/usr/bin/env python3
"""Rebuild the KagNode artwork from the canonical SVG mark; no external images."""

from pathlib import Path
from html import escape
import argparse
import datetime
import os
import re
import json, hashlib, io
import xml.etree.ElementTree as ET
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


def svg(label, mark, text=None, stack=False, shape=SHAPE):
    width, height = (64, 64) if text is None else (600, 150) if stack else (600, 100)
    body = f'<!-- PHASE 01: canonical geometric symbol -->\n<g transform="translate(0 0) scale(2)" fill="{mark}">{shape}</g>'
    if text is not None:
        body = f'<!-- PHASE 01: canonical geometric symbol -->\n<g transform="translate(8 14) scale(2)" fill="{mark}">{shape}</g>'
        paths, end = text_paths("KagNode.", 88, 59, 43, text)
        body += "\n<!-- PHASE 02: outlined wordmark, including period -->\n" + paths
        if label:
            paths, end = text_paths(label, 88, 97 if stack else 88, 22, text)
            body += (
                "\n<!-- PHASE 03: product name or editable project placeholder -->\n"
                + paths
            )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape("KagNode. " + label)}">\n<!-- PHASE 00: transparent canvas; geometry and typography are vectors -->\n{body}\n</svg>\n'


PRODUCTS = [
    "Cloud",
    "Developer",
    "Mail",
    "Passwords",
    "Media",
    "Core",
    "Entropy",
    "VPN",
    "HTTP Boot",
    "CLI",
    "[Project]",
]
TREATMENTS = [
    ("light", "#2563eb", "#111111"),
    ("dark", "#7da8ff", "#ffffff"),
    ("black", "#111111", "#111111"),
    ("white", "#ffffff", "#ffffff"),
]


def entropy_shape():
    source = ET.fromstring((ROOT / "source/canonical-entropy.svg").read_bytes())
    paths = [
        node.attrib["d"] for node in source.iter("{http://www.w3.org/2000/svg}path")
    ]
    if source.attrib.get("viewBox") != "0 0 32 32" or len(paths) != 5:
        raise ValueError("Invalid canonical Entropy symbol")
    return "".join(f'<path d="{data}"/>' for data in paths)


def write_entropy_icons(mark):
    target = ROOT / "icons/entropy"
    target.mkdir(parents=True, exist_ok=True)
    (target / "favicon.svg").write_bytes(mark)
    for size in [16, 32, 48, 64, 128, 180, 256, 512, 1024]:
        cairosvg.svg2png(
            bytestring=mark,
            output_width=size,
            output_height=size,
            write_to=str(target / f"entropy-{size}.png"),
        )
    with Image.open(target / "entropy-1024.png") as image:
        image.save(
            target / "favicon.ico",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        image.save(target / "entropy.icns")


def print_assets(raw):
    """Cairo needs explicit metadata normalization for repeatable print exports."""
    value = os.environ.get("SOURCE_DATE_EPOCH")
    date = None
    if value is not None:
        if not value.isdecimal():
            raise ValueError("SOURCE_DATE_EPOCH must be a nonnegative integer")
        date = (
            datetime.datetime.fromtimestamp(int(value), datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
    if date is None:
        pdf = cairosvg.svg2pdf(bytestring=raw)
    else:

        class DatedPDFSurface(cairosvg.surface.PDFSurface):
            def finish(self):
                self.cairo.set_metadata(
                    cairosvg.surface.cairo.PDF_METADATA_CREATE_DATE, date
                )
                self.cairo.set_metadata(
                    cairosvg.surface.cairo.PDF_METADATA_MOD_DATE, date
                )
                super().finish()

        pdf = DatedPDFSurface.convert(bytestring=raw)
    eps = cairosvg.svg2eps(bytestring=raw)
    if date is not None:
        # EPS is line-oriented PostScript; changing this DSC comment does not alter drawing commands.
        eps = re.sub(
            rb"(?m)^%%CreationDate:.*$", b"%%CreationDate: " + date.encode("ascii"), eps
        )
    return pdf, eps


def write_assets(product=None):
    if product not in (None, "entropy"):
        raise ValueError("Unsupported partial export")
    variants = {}
    if product is None:
        for name, color in [
            ("blue", "#2563eb"),
            ("black", "#111111"),
            ("white", "#ffffff"),
        ]:
            variants["mark-" + name] = svg("", color)
    entropy = entropy_shape()
    for name, mark, text in TREATMENTS:
        if product is None:
            variants["wordmark-" + name] = svg("", mark, text)
        for label in PRODUCTS:
            key = label.lower().replace(" ", "-").replace("[", "").replace("]", "")
            if product is not None and key != product:
                continue
            variants[key + "-" + name] = svg(
                label, mark, text, True, entropy if key == "entropy" else SHAPE
            )
        variants["entropy-mark-" + name] = svg("Entropy", mark, shape=entropy)
        # Same approved outlines, cropped for a practical header instead of the sheet canvas.
        variants["entropy-lockup-" + name] = svg(
            "Entropy", mark, text, True, entropy
        ).replace('viewBox="0 0 600 150"', 'viewBox="8 14 304 96"', 1)
    for folder in ["svg", "png", "webp", "pdf", "eps", "icons", "ascii", "symbols"]:
        (ROOT / folder).mkdir(exist_ok=True)
    for name, data in variants.items():
        raw = data.encode()
        (ROOT / "svg" / f"{name}.svg").write_bytes(raw)
        png = cairosvg.svg2png(
            bytestring=raw,
            output_width=1024
            if name.startswith("mark-") or name.startswith("entropy-mark-")
            else 1200,
        )
        (ROOT / "png" / f"{name}.png").write_bytes(png)
        with Image.open(io.BytesIO(png)) as image:
            image.save(ROOT / "webp" / f"{name}.webp", lossless=True)
        pdf, eps = print_assets(raw)
        (ROOT / "pdf" / f"{name}.pdf").write_bytes(pdf)
        (ROOT / "eps" / f"{name}.eps").write_bytes(eps)
    if product is None:
        mark = variants["mark-blue"].encode()
        for size in [16, 32, 48, 64, 128, 180, 256, 512, 1024]:
            cairosvg.svg2png(
                bytestring=mark,
                output_width=size,
                output_height=size,
                write_to=str(ROOT / "icons" / f"kagnode-{size}.png"),
            )
        with Image.open(ROOT / "icons/kagnode-1024.png") as image:
            image.save(
                ROOT / "icons/favicon.ico",
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            )
            image.save(ROOT / "icons/kagnode.icns")
        (ROOT / "icons/favicon.svg").write_bytes(mark)
        from ascii_art import write_ascii
        from symbols import write_symbols

        write_ascii(ROOT)
        write_symbols(ROOT)
        sheet = (ROOT / "source/KagNode-logo-sheet.svg").read_bytes()
        cairosvg.svg2pdf(bytestring=sheet, write_to=str(ROOT / "pdf/logo-sheet.pdf"))
        cairosvg.svg2eps(bytestring=sheet, write_to=str(ROOT / "eps/logo-sheet.eps"))
        cairosvg.svg2png(
            bytestring=sheet,
            output_width=1600,
            write_to=str(ROOT / "png/logo-sheet.png"),
        )
        with Image.open(ROOT / "png/logo-sheet.png") as image:
            image.save(ROOT / "webp/logo-sheet.webp", lossless=True)
    write_entropy_icons(variants["entropy-mark-light"].encode())
    manifest = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for folder in ["svg", "png", "webp", "pdf", "eps", "icons", "ascii", "symbols"]
        for path in sorted((ROOT / folder).rglob("*"))
        if path.is_file() and path.suffix.lower() != ".md"
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--product",
        choices=["entropy"],
        help="Export only this product, preserving every existing asset byte",
    )
    args = parser.parse_args()
    print("Generated", len(write_assets(args.product)), "assets")
