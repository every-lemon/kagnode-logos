from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
for name,digest in json.loads((root/'manifest.json').read_text()).items():
    path=root/name
    assert path.is_relative_to(root) and path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
    if path.suffix=='.svg':ET.fromstring(path.read_bytes())
print('All artwork checksums and SVG documents verified.')
