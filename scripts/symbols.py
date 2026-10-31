#!/usr/bin/env python3
"""Symbol-only color and treatment variants, derived from the canonical SVG."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import cairosvg

COLORS = {
    'black': '#000000',
    'white': '#ffffff',
    'charcoal': '#262626',
    'gray': '#808080',
    'light-gray': '#c4c4c4',
    'slate': '#64748b',
    'blue': '#2563eb',
    'light-blue': '#8ab4ff',
}
STYLES = ('solid', 'outline', 'two-tone')
SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024, 2048)


def symbol_svg(root, color, style):
    source = ET.fromstring((root / 'source/canonical-mark.svg').read_text())
    paths = [node.attrib['d'] for node in source.iter('{http://www.w3.org/2000/svg}path')]
    assert source.attrib['viewBox'] == '0 0 32 32' and len(paths) == 2
    treatment = (f'fill="none" stroke="{color}" stroke-width="1.6" '
                 'stroke-linecap="round" stroke-linejoin="round"') if style == 'outline' else f'fill="{color}"'
    opacity = ' opacity="0.45"' if style == 'two-tone' else ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" role="img" aria-label="KagNode symbol">
<!-- PHASE 00: transparent canvas; symbol only, no typography -->
<!-- PHASE 01: {style} treatment in {color}; canonical geometry is preserved -->
<g {treatment}>
  <!-- PHASE 02: primary shape -->
  <path d="{paths[0]}"/>
  <!-- PHASE 03: companion shape -->
  <path d="{paths[1]}"{opacity}/>
</g>
</svg>
'''


def write_symbols(root):
    (root / 'png').mkdir(exist_ok=True)
    for style in STYLES:
        svg_dir, png_dir = root / 'symbols/svg' / style, root / 'symbols/png' / style
        svg_dir.mkdir(parents=True, exist_ok=True)
        png_dir.mkdir(parents=True, exist_ok=True)
        for name, color in COLORS.items():
            data = symbol_svg(root, color, style).encode()
            (svg_dir / f'{name}.svg').write_bytes(data)
            for size in SIZES:
                png = cairosvg.svg2png(bytestring=data, output_width=size, output_height=size)
                (png_dir / f'{name}-{size}.png').write_bytes(png)
                # Keep every symbol size directly accessible in the main PNG folder.
                (root / 'png' / f'mark-{style}-{name}-{size}.png').write_bytes(png)


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    write_symbols(root)
    manifest = json.loads((root / 'manifest.json').read_text())
    paths = list((root / 'symbols').rglob('*')) + list((root / 'png').glob('mark-*.png'))
    for path in sorted(paths):
        if path.suffix in ('.svg', '.png'):
            manifest[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Generated {len(COLORS) * len(STYLES)} SVGs and {len(COLORS) * len(STYLES) * len(SIZES)} transparent PNGs.')
