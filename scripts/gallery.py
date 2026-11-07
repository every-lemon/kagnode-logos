#!/usr/bin/env python3
"""Build a self-contained GitHub-connected artwork gallery from the asset manifest."""

import argparse
import base64
import html
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


def enrich_previews(assets):
    """Every download has artwork; browser-unsupported originals use a sibling."""
    by_path = {item["path"]: item for item in assets}
    for item in assets:
        path = Path(item["path"])
        stem = path.stem
        if item["family"] == "symbols" and item["variant"] != "standard":
            identity = "symbols/" + item["variant"] + "/" + item["color"]
            candidate = "symbols/svg/" + item["variant"] + "/" + item["color"] + ".svg"
        elif item["family"] == "icons":
            identity, candidate = "icons/kagnode", "icons/favicon.svg"
        elif item["family"] == "sheets":
            identity, candidate = "sheets/logo-sheet", "png/logo-sheet.png"
        else:
            identity = item["family"] + "/" + stem
            candidate = "svg/" + stem + ".svg"
        item["design"] = identity
        item["product"] = (
            re.sub(r"-(?:black|white|dark|light)$", "", stem)
            if item["family"] == "products"
            else ""
        )
        item["preview_background"] = (
            "dark"
            if item["color"] in {"white", "light-gray", "light-blue", "dark"}
            else "light"
        )
        if item["format"] in {"txt", "ansi"}:
            # Never display terminal escape instructions or parse artwork as HTML.
            raw = (ROOT / item["path"]).read_text()
            plain = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", raw)
            plain = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", plain)
            item["preview_text"] = plain.rstrip()[:24000]
            item["preview_background"] = "dark"
            continue
        if candidate not in by_path:
            candidate = (
                item["path"] if item["format"] in {"svg", "png", "webp", "ico"} else ""
            )
        if not candidate:
            raise ValueError("No browser-renderable artwork for " + item["path"])
        preview = by_path[candidate]
        item["preview_path"] = candidate
        item["preview_format"] = preview["format"]
        item["preview_sha256"] = preview["sha256"]
    return assets


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
            "terminal"
            if name.startswith("ascii/")
            else "symbols"
            if name.startswith("symbols/") or stem.startswith("mark-")
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
        "schema": 2,
        "repository": "every-lemon/kagnode-logos",
        "source_commit": sha,
        "assets": enrich_previews(
            sorted(assets, key=lambda a: (a["family"], a["path"]))
        ),
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
    bundle = json.loads((ROOT / "vendor/core-bundle.json").read_text())
    assets = {
        name: base64.b64decode(value["data"]).decode()
        for name, value in bundle["files"].items()
    }
    config = {
        "version": bundle["version"],
        "authenticated": False,
        "app": "logos",
        "mark": "data:image/svg+xml;base64," + bundle["files"]["mark.svg"]["data"],
    }
    head = (
        '<meta name="kagnode-core" content="'
        + html.escape(json.dumps(config), quote=True)
        + '">\n<script>'
        + assets[bundle["entrypoints"]["theme"]]
        + "</script>"
    )
    page = (
        (ROOT / "web/gallery.html")
        .read_text()
        .replace("<!-- CORE HEAD -->", head)
        .replace(
            "/* CSS */",
            (ROOT / "web/gallery.css").read_text()
            + "\n"
            + assets[bundle["entrypoints"]["style"]],
        )
        .replace(
            "/* CATALOG */",
            json.dumps(data, separators=(",", ":")).replace("<", "\\u003c"),
        )
        .replace(
            "/* JS */",
            assets[bundle["entrypoints"]["script"]]
            + "\n"
            + (ROOT / "web/gallery.js").read_text(),
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
