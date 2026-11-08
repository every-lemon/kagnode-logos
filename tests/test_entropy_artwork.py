"""Entropy branding adds product assets without rewriting published artwork."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts" / (name + ".py")
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


generate = module("generate")
gallery = module("gallery")


class EntropyArtworkTests(unittest.TestCase):
    def test_existing_774_published_assets_and_core_mark_are_unchanged(self):
        legacy = json.loads(
            (ROOT / "tests/fixtures/pre-entropy-manifest.json").read_text()
        )
        current = json.loads((ROOT / "manifest.json").read_text())
        self.assertEqual(len(legacy), 774)
        for path, digest in legacy.items():
            self.assertEqual(current.get(path), digest, path)
            self.assertEqual(
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path
            )
        self.assertEqual(
            generate.svg("", "#2563eb").encode(),
            (ROOT / "svg/mark-blue.svg").read_bytes(),
        )

    def test_product_marks_wordmarks_and_tight_lockups_are_real_vectors(self):
        for variant in ("light", "dark", "black", "white"):
            mark = ET.fromstring(
                (ROOT / f"svg/entropy-mark-{variant}.svg").read_bytes()
            )
            self.assertEqual(
                len(list(mark.iter("{http://www.w3.org/2000/svg}path"))), 5
            )
            wordmark = ET.fromstring((ROOT / f"svg/entropy-{variant}.svg").read_bytes())
            lockup = ET.fromstring(
                (ROOT / f"svg/entropy-lockup-{variant}.svg").read_bytes()
            )
            self.assertIn("Entropy", wordmark.attrib["aria-label"])
            self.assertEqual(lockup.attrib["viewBox"], "8 14 304 96")
            self.assertEqual(
                [(p.attrib) for p in wordmark.iter("{http://www.w3.org/2000/svg}path")],
                [(p.attrib) for p in lockup.iter("{http://www.w3.org/2000/svg}path")],
            )
            self.assertFalse(list(lockup.iter("{http://www.w3.org/2000/svg}text")))
            with Image.open(ROOT / f"png/entropy-lockup-{variant}.png") as image:
                left, top, right, bottom = image.getchannel("A").getbbox()
                self.assertLess(left, image.width * 0.12)
                self.assertGreater(right, image.width * 0.85)
                self.assertLess(top, image.height * 0.15)
                self.assertGreater(bottom, image.height * 0.85)

    def test_favicons_use_entropy_previews_and_all_product_formats_are_discoverable(
        self,
    ):
        data = gallery.catalog()
        entropy = [a for a in data["assets"] if a["product"] == "entropy"]
        self.assertEqual(len(entropy), 72)
        for asset in entropy:
            if asset["family"] == "icons":
                self.assertEqual(asset["design"], "icons/entropy")
                self.assertEqual(asset["preview_path"], "icons/entropy/favicon.svg")
            self.assertTrue((ROOT / asset["preview_path"]).is_file())
        self.assertIn("ico", {a["format"] for a in entropy})
        self.assertIn("eps", {a["format"] for a in entropy})
        self.assertIn("pdf", {a["format"] for a in entropy})
        with Image.open(ROOT / "icons/entropy/favicon.ico") as icon:
            self.assertTrue(
                {(16, 16), (32, 32), (64, 64), (256, 256)}.issubset(icon.ico.sizes())
            )

    def test_partial_generation_preserves_legacy_files_and_repeats_with_fixed_epoch(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source").mkdir()
            shutil.copyfile(
                ROOT / "source/canonical-entropy.svg",
                root / "source/canonical-entropy.svg",
            )
            (root / "png").mkdir()
            retained = root / "png/retained-legacy.png"
            retained.write_bytes(b"unchanged legacy fixture")
            with (
                patch.object(generate, "ROOT", root),
                patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1794135600"}),
            ):
                first = generate.write_assets("entropy")
                second = generate.write_assets("entropy")
            self.assertEqual(first, second)
            self.assertEqual(len(first), 73)
            self.assertEqual(retained.read_bytes(), b"unchanged legacy fixture")


if __name__ == "__main__":
    unittest.main()
