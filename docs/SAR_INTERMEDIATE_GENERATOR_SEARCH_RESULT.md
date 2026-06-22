# SAR intermediate generator search result

Status: notebook-side intermediate generator not located in the searched source trees.

This is a docs-only safe summary from a local filesystem search. No manifest bodies, image identifiers, CSV rows, raster payloads, NPY payloads, coordinates, or per-pixel values are included.

## Search scope

Roots searched locally:

```text
C:\Dev\New_GEE
C:\Dev\New_GEE_REFERENCE
C:\Dev\New_GEE\data\private_references
```

Extensions searched:

```text
*.py
*.ipynb
*.json
*.md
```

Terms searched:

```text
sar_intermediate_manifest
per_image_products_db
pair_median
final_median_pre_rtc
post_sample_pre_rtc
post_rtc
```

## Key result

No notebook cell or standalone notebook-side generator was found that both defines/writes `sar_intermediate_manifest.json` and generates the full intermediate stages.

Relevant hits were limited to:

```text
app implementation / services / tests / docs
existing frozen manifests
new.ipynb containing per_image_products_db only
scripts/export_cell25_sar_intermediates.py app-side exporter
```

The searched notebook file only hit `per_image_products_db` and did not hit `sar_intermediate_manifest`, `pair_median`, `final_median_pre_rtc`, `post_sample_pre_rtc`, or `post_rtc` as a manifest-writing source.

## Existing manifest locations found

The search located existing manifest artifacts, including:

```text
D1_NEW_IPYNB_REFERENCE_2026_06_10\QA\sar\intermediates\sar_intermediate_manifest.json
D1C_NEW_IPYNB_REFERENCE_2026_06_10\QA\sar\intermediates\sar_intermediate_manifest.json
data\private_references\notebook_frozen\new_ipynb_d1_20260615_local\artifacts\report\QA\sar\intermediates\sar_intermediate_manifest.json
data\runs\a11309bf-ed47-4bf5-bbf4-f755b904065c\QA\sar\intermediates\sar_intermediate_manifest.json
data\runs\e11d3280-a7b7-4c7c-a761-8b08ac9452f2\QA\sar\intermediates\sar_intermediate_manifest.json
```

These are artifacts or app-side generated manifests, not a located notebook-side generator.

## Interpretation

```text
D1C notebook intermediate references should be treated as externally frozen artifacts for this investigation.
The visible notebook final Cell 24 sampling path matches the app sampling pattern.
The actual notebook-side full intermediate manifest generator was not located in the searched files.
The per_image_products_db row-shift remains a diagnostic observation against frozen intermediate artifacts, not a final-output parity failure.
```

## Decision

```text
SAR intermediate generator search: closed / generator not located
SAR core final output parity: still closed / passed
SAR per-image intermediate row-shift: diagnostic-only against frozen intermediate artifacts
Radar linear support stack parity: still open / downstream diagnostic
```

## Boundary

```text
No manifest bodies were committed.
No SAR JSON bodies were committed.
No CSV rows were committed.
No image identifiers were committed.
No raster or NPY payloads were committed.
No per-pixel values were committed.
No public downloads, HTTP table/array serving, or map overlays were enabled.
```
