# KagNode Entropy artwork

Entropy uses a separate pixel E with a detached middle cell, paired with the existing outlined KagNode. typography. The mark identifies the project; it is not an entropy assessment, security seal or attestation badge. The canonical KagNode symbol is unchanged.

| Use | Paths | Canvas |
| --- | --- | --- |
| Product symbol | `svg/entropy-mark-{light,dark,black,white}.svg` | Transparent 64 × 64 |
| Standard product wordmark | `svg/entropy-{light,dark,black,white}.svg` | 600 × 150 |
| Compact header lockup | `svg/entropy-lockup-{light,dark,black,white}.svg` | Tight viewBox `8 14 304 96`, same paths/outlines |
| Browser favicon | `icons/entropy/favicon.svg`, `icons/entropy/favicon.ico` | Vector or 16–256 px ICO |
| Raster icons | `icons/entropy/entropy-{16,32,48,64,128,180,256,512,1024}.png` | Transparent |
| macOS icon | `icons/entropy/entropy.icns` | Multi-size icon |
| Other formats | Matching `png/`, `webp/`, `pdf/`, `eps/` names | Raster and print |

Use `light` on a light background and `dark` on a dark background. The white/black variants provide monochrome alternatives. Wordmarks contain outlined glyphs and load no fonts. Keep the transparent padding; do not stretch or clip the symbol.

## Rebuild and provenance

Install `requirements-artwork.txt`, `requirements-format.txt`, Cairo 1.16+ and DejaVu Sans at the path in the generator. Run:

```sh
SOURCE_DATE_EPOCH=$(git log -1 --format=%ct) .venv/bin/python scripts/generate.py --product entropy
.venv/bin/python -m unittest discover -s tests -p test_entropy_artwork.py -v
.venv/bin/python scripts/verify.py
```

Partial generation updates only Entropy assets and the checksum manifest. All 774 earlier artwork hashes are retained. PDF dates use the [Cairo metadata API](https://www.cairographics.org/manual/cairo-PDF-Surfaces.html#cairo-pdf-surface-set-metadata); EPS creation comments are normalized without changing drawing commands. Fixed-epoch repeat builds are tested.

Commit canonical sources and artwork before generating `catalog.json` and the HTML viewers. The catalog must pin an ancestor containing every referenced asset; use a merge preserving that ancestor, or repin to a reachable merged commit before publication. Never point a released viewer at an uncommitted asset.

Applications should bundle the selected files on their own server with their source repository URL, exact reviewed commit and SHA256 values. Preserve [artwork permission](../LICENSE), [font notices](../source/FONT-NOTICES.txt) and [brand guidance](../BRAND-POLICY.md). Generator code retains its separate MIT license.
