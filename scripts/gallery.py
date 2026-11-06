#!/usr/bin/env python3
"""Build a self-contained GitHub-connected artwork gallery from the asset manifest."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
COLORS = [
    "light-gray",
    "light-blue",
    "charcoal",
    "black",
    "white",
    "gray",
    "slate",
    "blue",
    "dark",
    "light",
]


def catalog():
    checksums = json.loads((ROOT / "manifest.json").read_text())
    assets = []
    for name, sha in checksums.items():
        path = ROOT / name
        if (
            path.is_symlink()
            or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != sha
        ):
            raise ValueError("Invalid artwork: " + name)
        stem = path.stem
        width = height = None
        if path.suffix in {".png", ".webp", ".ico", ".icns"}:
            from PIL import Image

            with Image.open(path) as image:
                width, height = image.size
        elif path.suffix == ".svg":
            svg = ET.fromstring(path.read_bytes())
            box = svg.get("viewBox", "").split()
            if len(box) == 4:
                width, height = [round(float(v)) for v in box[2:]]
        color = next(
            (c for c in COLORS if re.search(r"(?:^|[-/])" + c + r"(?:[-/.]|$)", name)),
            "original",
        )
        family = (
            "symbols"
            if name.startswith("symbols/") or stem.startswith("mark-")
            else "terminal"
            if name.startswith("ascii/")
            else "icons"
            if name.startswith("icons/")
            else "sheets"
            if "sheet" in stem
            else "wordmarks"
            if "wordmark" in stem
            else "products"
        )
        variant = next(
            (v for v in ["outline", "two-tone", "solid"] if v in name), "standard"
        )
        assets.append(
            {
                "path": name,
                "name": stem.replace("-", " ").replace("_", " "),
                "family": family,
                "variant": variant,
                "color": color,
                "format": path.suffix[1:],
                "width": width,
                "height": height,
                "sha256": sha,
                "size": path.stat().st_size,
            }
        )
    # Paths in the embedded catalog are pinned to the commit containing this artwork.
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    return {
        "schema": 1,
        "repository": "every-lemon/kagnode-logos",
        "source_commit": sha,
        "assets": sorted(assets, key=lambda a: (a["family"], a["path"])),
    }


def build(check=False):
    if check:
        existing = json.loads((ROOT / "catalog.json").read_text())
        expected = catalog()
        expected["source_commit"] = existing["source_commit"]
        if existing != expected:
            raise ValueError("Gallery catalog is stale")
        if not re.fullmatch(r"[0-9a-f]{40}", existing["source_commit"]):
            raise ValueError("Invalid catalog commit")
        data = existing
    else:
        data = catalog()
    encoded = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    page = (
        (ROOT / "web/gallery.html")
        .read_text()
        .replace(
            "/* CSS */",
            (ROOT / "web/gallery.css").read_text()
            + "\n"
            + (ROOT / "web/kagnode-scroll.css").read_text(),
        )
        .replace(
            "/* CATALOG */",
            json.dumps(data, separators=(",", ":")).replace("<", "\\u003c"),
        )
        .replace(
            "/* JS */",
            (ROOT / "web/gallery.js").read_text()
            + "\n"
            + (ROOT / "web/kagnode-scroll.js").read_text(),
        )
    )
    outputs = {"catalog.json": encoded, "index.html": page, "kagnode-logos.html": page}
    for name, value in outputs.items():
        path = ROOT / name
        if check and (not path.exists() or path.read_text() != value):
            raise ValueError("Rebuild gallery output: " + name)
        if not check:
            path.write_text(value)
    print(
        f"Gallery: {len(data['assets'])} assets verified"
        if check
        else f"Gallery built with {len(data['assets'])} assets"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    build(parser.parse_args().check)
