#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts/tyrone_napp_archive_check
7z l data/research/tyrone_napp_1996/Desktop.7z.001 | tee artifacts/tyrone_napp_archive_check/listing.txt
7z t data/research/tyrone_napp_1996/Desktop.7z.001 | tee artifacts/tyrone_napp_archive_check/test.txt
