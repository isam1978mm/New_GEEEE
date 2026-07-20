# Depth Matched Sentinel-1 Feature Extractor Verification — 2026-07-20

Status: software verification passed. The real private extraction has not yet run.

This record covers implementation and test status only. It does not report a site-background signal, estimate depth, train a model, import calibration records, or enable app depth output.

## Verified results

The owner ran the focused extractor tests, the C1 redaction-risk tests, and the full unit suite on Windows with Python 3.13.5.

```text
matched feature extractor tests = 13 passed
C1 redaction-risk tests = 3 passed
full unit suite = 997 passed
failures = 0
warnings = 4 non-blocking
```

The warnings were the existing NumPy entropy warnings, the existing rasterio non-georeferenced test warning, and the pytest cache-write warning.

## Software gate decision

```text
manifest validation = passed
private-path enforcement = passed
identical-geometry rejection = passed
dry-run isolation = passed
transition exclusion = passed
complete-row handling = passed
incomplete-row handling = passed
privacy-safe aggregate console = passed
software_gate = ready_for_private_extraction
```

## Next permitted action

1. Run the no-network extractor dry run using the private site polygon, reviewed background polygon, and frozen exact-match manifest.
2. Confirm the dry-run result reports the expected 80 clean-pre rows, 82 clean-post rows, and 5 excluded transition rows.
3. Run the real private extraction with an output path outside Git.
4. Review only aggregate completeness fields in the console. Do not paste the private detailed output because it contains exact image identities and feature values.

A completed extraction means only that the private per-image table was produced. It does not establish a buried-feature effect or any depth relationship.

## Checklist

- [x] Focused extractor tests passed: 13.
- [x] C1 privacy tests passed: 3.
- [x] Full unit suite passed: 997.
- [x] No unit-test failures.
- [ ] Run the extractor dry run.
- [ ] Execute the private matched-feature extraction.
- [ ] Confirm complete rows before effect analysis.
