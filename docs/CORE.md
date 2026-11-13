# KagNode Core 5 integration

This application uses [KagNode Core](https://github.com/every-lemon/kagnode-core) for its sidebar, controls, scrolling, loading and account presentation. Its committed `core.lock.json` records the baseline and compatible stable UI patch line. Editable corresponding Core source is retained under `vendor/core-source/`; generated pinned fallbacks let the interface start offline.

Application servers serve Core assets from their own origin. Browsers never fetch Core scripts from GitHub. The downloaded gallery embeds its UI and stays account-free. Artwork downloads still require internet access.

The gallery embeds a reviewed Core bundle at build time and remains account-free. Rebuild and republish the gallery and downloaded viewer when adopting Core changes. It does not run the Core manager, create server bindings or expose administration/update controls. Retain artwork paths, licenses and prior published viewers.

This stable gallery bundles reviewed Core 5 presentation. It does not qualify native services, codecs, HTTP Boot images, network hardware or unrelated native applications. Keep application databases and deployment configuration in their existing locations. No data reset or native provisioning is part of Core integration.

## Shared loading mark

Core supplies KagNode’s split-orbit spinner. The canonical logo stays still while its separated accent orbits. Reduced-motion settings stop the animation. Existing loading labels, retries and dismissal controls remain available. The server serves the spinner and artwork locally; no browser Core connection to GitHub is required.

## Update summaries

This account-free artwork gallery does not run the automatic manager notice channel. It does not invent update summaries or user dismissal records. Shared controls remain locally bundled and reviewed with the application/artwork release.
