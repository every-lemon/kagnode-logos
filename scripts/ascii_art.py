#!/usr/bin/env python3
"""Terminal versions of the canonical geometric mark. ASCII only; no font files."""
from pathlib import Path
import hashlib
import io
import json
import cairosvg
from PIL import Image

# Original seven-row letter cells; no external figlet font is required.
LETTERS = {
    'K': ['#   #','#  # ','# #  ','##   ','# #  ','#  # ','#   #'],
    'A': [' ### ','#   #','#   #','#####','#   #','#   #','#   #'],
    'G': [' ####','#    ','#    ','# ###','#   #','#   #',' ####'],
    'N': ['#   #','##  #','##  #','# # #','#  ##','#  ##','#   #'],
    'O': [' ### ','#   #','#   #','#   #','#   #','#   #',' ### '],
    'D': ['#### ','#   #','#   #','#   #','#   #','#   #','#### '],
    'E': ['#####','#    ','#    ','#### ','#    ','#    ','#####'],
    '.': [' ',' ',' ',' ',' ',' ','#'],
}

def mark_rows(root, width=28, height=14):
    # Rasterize square pixels first, then compensate for tall terminal cells.
    source = (root / 'source/canonical-mark.svg').read_bytes()
    image = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=source, output_width=1024, output_height=1024))).getchannel('A')
    image = image.crop(image.getbbox()).resize((width, height), Image.Resampling.LANCZOS)
    return [''.join('#' if image.getpixel((x, y)) >= 110 else ' ' for x in range(width)).rstrip() for y in range(height)]

def write_ascii(root):
    folder = root / 'ascii'
    folder.mkdir(exist_ok=True)
    mark = mark_rows(root,20,9)
    wordmark = [' '.join(LETTERS[c][y] for c in 'KAGNODE.').rstrip() for y in range(7)]
    wide = ['  ' + row.ljust(20) + ('   ' + wordmark[y-1] if 1 <= y < 8 else '') for y, row in enumerate(mark)]
    display=['  '+row.ljust(20)+('    '+wordmark[y-1].replace('#','##').replace(' ','  ') if 1 <= y < 8 else '') for y,row in enumerate(mark)]
    variants = {
        'kagnode': '\n'.join(row.rstrip() for row in wide) + '\n',
        'kagnode-display': '\n'.join(row.rstrip() for row in display)+'\n',
        'kagnode-wordmark': '\n'.join(wordmark)+'\n',
        'kagnode-compact': '\n'.join('  ' + row for row in mark) + '\n\n  KagNode.\n',
        'kagnode-small': '\n'.join('  ' + row for row in mark_rows(root, 16, 8)) + '\n\n  KagNode.\n',
        'mark': '\n'.join(mark) + '\n',
    }
    for name, plain in variants.items():
        (folder / (name + '.txt')).write_text(plain, encoding='ascii')
        (folder / (name + '-blocks.txt')).write_text(plain.replace('#','█'),encoding='utf-8')
        colored=[]
        for row in plain.splitlines():
            cut=25 if name=='kagnode' else 26 if name=='kagnode-display' else len(row)
            colored.append('\x1b[94m'+row[:cut].replace('#','█')+'\x1b[97m'+row[cut:].replace('#','█')+'\x1b[0m')
        (folder / (name + '.ansi')).write_text('\n'.join(colored)+'\n', encoding='utf-8')
    return variants

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    write_ascii(root)
    manifest = json.loads((root / 'manifest.json').read_text())
    for path in sorted((root / 'ascii').glob('*')):
        manifest[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print((root / 'ascii/kagnode.txt').read_text())
