# Reference Run v1

This directory holds the portable contract for the frozen notebook reference set.

The binary notebook reference bundle is operator-supplied and never committed. The repo commits only `MANIFEST.json`, which records the files expected in that bundle plus their checksums and safe metadata.

## Environment Variable

Set `NOTEBOOK_REFERENCE_BUNDLE_DIR` to the local directory containing the out-of-band reference bundle.

If the variable is unset, notebook reference-output parity tests skip cleanly with a message pointing back to this file. The app must still start without this variable.

## Manifest

`MANIFEST.json` records:

- bundle metadata: `reference_run_id`, `notebook_commit_sha`, `notebook_file_sha256`, `capture_date_iso`, and `canonical_roi_label`
- safe GRID identity only: CRS, EPSG, UTM zone, hemisphere, scale, output size, and nodata
- one entry per bundle file with relative path, SHA-256 checksum, and size in bytes
- comparison rules, including the `IRON_SWIR.tif` Option A rule

The manifest must not contain raw coordinates, raw bounds, raw transform values, absolute paths, or local machine paths.

## Regeneration

After copying or refreshing the operator-local bundle, regenerate the manifest with:

```powershell
$env:NOTEBOOK_REFERENCE_BUNDLE_DIR = "<operator-supplied-bundle-dir>"
python scripts/generate_reference_manifest.py
```

The script writes `tests/notebook_parity/fixtures/reference_run_v1/MANIFEST.json`. It prints only a file count and never prints the configured path.

## VPS / New Machine Workflow

This mechanism is portable. To verify parity on a second laptop or future VPS:

1. Copy the binary reference bundle out-of-band to a secure local directory.
2. Set `NOTEBOOK_REFERENCE_BUNDLE_DIR` on that machine.
3. Run the notebook parity tests.

The binaries remain outside git in every environment.

## IRON_SWIR Option A

`IRON_SWIR.tif` must use comparison rule `option_a_corrected_app_reference`.

That rule preserves the accepted Option A decision: compare the corrected analytical/app reference using `(B11 - B12) / (B11 + B12)`, not a checked-in notebook or sign-flipped notebook raster.

## Placeholder State

If `MANIFEST.json` contains `REQUIRES_OPERATOR_CAPTURE`, the manifest is not finalized. The operator must configure `NOTEBOOK_REFERENCE_BUNDLE_DIR` and rerun `scripts/generate_reference_manifest.py` before configured reference-bundle parity tests can pass.
