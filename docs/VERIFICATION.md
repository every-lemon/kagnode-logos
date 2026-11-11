# Verification boundaries

CI validates the existing application checks separately from source formatting, source publication allowlists and archive/package inspection. The packaging workflow produces checksums and source-commit provenance. Debian and RPM source/data packages have no service-start scripts; installation/removal validation does not establish native service compatibility.

Logos 5.0 RPMs target Rocky Linux 10 as data-only packages. This project has no native service to provision. Native Mail, VPN and HTTP Boot setup is outside this repository. Media worker, FFmpeg, codecs and hardware acceleration are not exercised by packaging tests. No Client image or qualification VM is built for this work. Existing verification documents remain authoritative for previously recorded checks.
