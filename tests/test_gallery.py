"""Artwork previews resolve to real files without changing downloadable originals."""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gallery", ROOT / "scripts/gallery.py")
gallery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gallery)


class GalleryTests(unittest.TestCase):
    def test_every_original_has_a_renderable_matching_preview(self):
        data = gallery.catalog()
        assets = {a["path"]: a for a in data["assets"]}
        for item in assets.values():
            if item["format"] in {"txt", "ansi"}:
                self.assertTrue(item["preview_text"], item["path"])
                self.assertNotIn("\x1b", item["preview_text"])
            else:
                target = assets[item["preview_path"]]
                self.assertIn(target["format"], {"svg", "png", "webp", "ico"})
                self.assertEqual(target["sha256"], item["preview_sha256"])
                if item["format"] in {"pdf", "eps"}:
                    self.assertEqual(target["design"], item["design"])
        self.assertEqual(data["schema"], 2)

    def test_sizes_and_formats_share_designs_without_losing_files(self):
        data = gallery.catalog()
        symbols = [a for a in data["assets"] if a["design"] == "symbols/solid/blue"]
        self.assertGreater(len(symbols), 5)
        self.assertIn("svg", {a["format"] for a in symbols})
        self.assertIn("png", {a["format"] for a in symbols})
        self.assertEqual(
            {a["path"] for a in data["assets"]},
            set(json.loads((ROOT / "manifest.json").read_text())),
        )
        self.assertIn("png/mark-solid-blue-16.png", {a["path"] for a in symbols})
        self.assertIn("symbols/png/solid/blue-16.png", {a["path"] for a in symbols})


if __name__ == "__main__":
    unittest.main()
