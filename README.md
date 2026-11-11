<p align="center"><img src="svg/github-wordmark.svg" width="440" alt="KagNode."></p>

# KagNode Logos

## Overview

Canonical KagNode symbols, wordmarks, product layouts and terminal artwork.

Gallery: https://every-lemon.github.io/kagnode-logos/ · [Download the HTML viewer](kagnode-logos.html). The viewer requires internet access for artwork.

## Release status

**5.0.1** is the coordinated stable artwork and gallery release. The gallery bundles reviewed Core 5 presentation and remains account-free.

Stable scope covers artwork, the browser gallery/viewer and data-only packages; it does not install or qualify native services. See [verification](docs/VERIFICATION.md) and [changelog](CHANGELOG.md).

## Features

- Transparent SVG, PNG and WebP marks, plus PDF/EPS print artwork.
- Symbol-only variants, favicons, product wordmarks and terminal banners.
- Dedicated [Entropy product artwork](docs/ENTROPY.md), including compact header lockups, dark/light product marks and dedicated favicons.
- Responsive gallery grouping sizes and formats by design, with color/product/format filters and a downloadable GitHub-connected HTML viewer.
- Real artwork previews for vector, print and icon downloads; terminal art displays without raw ANSI escape codes. Automatic contrast, light/dark themes and transparent favicon.

## Requirements

The gallery works in modern browsers. Rebuilding artwork requires Python 3.12, the pinned `requirements-artwork.txt` dependencies, Cairo 1.16 or newer, and the documented DejaVu font.

## Installation and downloads

Download from [GitHub Releases](https://github.com/every-lemon/kagnode-logos/releases). Verify `SHA256SUMS` before extracting or installing a package.

| Payload | Formats | Support |
| --- | --- | --- |
| Complete source / artwork | `.tar.xz`, `.tar.gz`, `.zip` | Named top-level directory; manual setup |
| Artwork and gallery | `.deb` | Data only |
| Artwork and gallery | `.rpm` | Rocky Linux 10 data-only package |



Source packages install under `/usr/share/kagnode/`; they do not replace an existing application, migrate data, start services or configure networking.  See [package details](docs/PACKAGING.md).

## Usage

```sh
python3 scripts/verify.py
# Open kagnode-logos.html or visit the gallery linked below.
```

See [operations and existing setup instructions](docs/OPERATIONS.md) for the full workflow and its prerequisites.

## Configuration and storage

Shared presentation bundles reviewed [KagNode Core](docs/CORE.md) assets at publication time. The gallery and downloaded viewer have no accounts, server bindings or update daemon; rebuild the published HTML to upgrade its UI.

Edit canonical sources in source/. Keep existing /png, symbols/ and icon paths available for consumers.

## Security

Use HTTPS and least-privilege accounts for hosted services. Keep secrets and user data out of Git. Data packages contain artwork and the viewer; they do not install services. Verification records distinguish package checks from unrelated native-service claims. See [security guidance](docs/SECURITY.md).

## Development and testing

```sh
python3 scripts/verify.py
python3 scripts/gallery.py --check
python3 scripts/repository_check.py
python3 scripts/format_source.py --check
python3 scripts/release.py --output dist/packages
```

Install the formatting dependencies from `requirements-format.txt`. Data package building additionally needs `dpkg-deb`, `rpmbuild` and XZ support. Read [the repository map](docs/STRUCTURE.md) before editing generated files.

## Documentation

- [Repository structure](docs/STRUCTURE.md)
- [Operations](docs/OPERATIONS.md)
- [Entropy product assets and provenance](docs/ENTROPY.md)
- [Packages and release process](docs/PACKAGING.md)
- [Verification and limits](docs/VERIFICATION.md)
- [Changelog](CHANGELOG.md)

## Licensing

See [LICENSE](LICENSE) and retained third-party notices. Artwork permissions and code licensing are separate; see LICENSE-CODE and BRAND-POLICY.md.
