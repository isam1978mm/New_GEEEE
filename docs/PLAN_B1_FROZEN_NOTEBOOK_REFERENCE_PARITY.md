# Plan B1 — Frozen Notebook Reference Parity

Status: planned next phase.

Purpose: turn the current Plan B app ports from `Partial` into `Full` where possible by comparing app outputs against already-existing notebook run outputs.

## Plain-English rule

`Partial` does not mean the app port failed. It means the app output exists and passed output-proof, but it has not yet been compared against the notebook output files.

`Full` means the app output has been verified against frozen notebook reference outputs from the selected notebook cell/output family.

## Do not rerun the notebook if outputs already exist

If the notebook already produced the output files, do not rerun it just to create references.

Use the existing notebook output files as the frozen references when all of these are true:

1. The file exists.
2. The file can be tied to a notebook item/cell/output family.
3. The input run/data is known enough to compare to an app run.
4. The file was not manually edited after notebook generation.
5. The file can be hashed and stored or referenced safely.

Rerun the notebook only if the output is missing, corrupted, edited, produced from the wrong input, or cannot be tied to the selected notebook cell.

## Private reference location

Coordinate-bearing or sensitive outputs must stay outside the public repo.

Recommended local/private root:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\
```

Recommended per-item layout:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_<ITEM>_cell_<CELL>\
  reference_manifest.json
  notebook_outputs\
    <copied notebook output files>
  app_outputs_snapshot\
    <optional copied app output files used during comparison>
  comparison_reports\
    <private comparison reports, if coordinate-bearing>
```

Do not commit raw private reference outputs to GitHub unless they are confirmed safe, redacted, and approved.

## Public repo artifacts allowed

The public repository may contain:

```text
comparison code
test scaffolding
redacted/hash manifests
docs explaining parity status
small non-sensitive fixtures if explicitly approved
```

The public repository should not contain:

```text
exact coordinates
raw target geometry
private KMZ/KML/GeoJSON outputs
raw probability maps
private target CSVs with sensitive location columns
large raster/NPY reference outputs
model weights
private notebook run folders
```

## B1 workflow

For each Plan B item:

1. Select the exact canonical notebook cell already chosen during Plan B porting.
2. Locate the existing notebook output files for that item.
3. Copy those files into the private frozen-reference folder.
4. Write `reference_manifest.json` with:
   - item number
   - canonical cell
   - source notebook path/version if known
   - original notebook output path
   - frozen reference path
   - SHA256 hash for each reference file
   - app output path to compare
   - comparison method
   - privacy classification
5. Run the app output generation for the same run/input.
6. Compare app output vs frozen notebook output.
7. Write a comparison report.
8. If comparison passes, update the item status from `Partial` to `Full`.
9. If comparison fails, keep status `Partial` and document the exact mismatch.

## Comparison rules by file type

### NPY arrays

Full match requires:

```text
same shape
same dtype or approved dtype conversion
same finite/nodata policy
numeric values match within approved tolerance
```

Typical check:

```text
np.allclose(app, reference, rtol=<tolerance>, atol=<tolerance>, equal_nan=True)
```

### CSV files

Full match requires:

```text
same required columns
same row count
same stable key fields
same text/category labels
numeric columns match within approved tolerance
```

Ignore only explicitly documented volatile columns, such as timestamps, if present.

### JSON files

Full match requires:

```text
same required schema fields
same stable values
same record counts
numeric values match within approved tolerance
```

Ignore or normalize explicitly volatile fields such as `created_at`, local path roots, or run-specific IDs when documented.

### TXT reports

Full match requires:

```text
same required section titles
same source cell markers
same record counts and important result lines
```

Formatting-only differences may be allowed only if documented.

### GeoJSON/KMZ/KML

Coordinate-bearing outputs are private.

Full match requires one of two modes:

```text
private exact mode:
  same feature count
  same geometry within tolerance
  same key properties

redacted mode:
  same feature count
  same non-sensitive properties
  no exact coordinates exposed in public reports
```

### Gate manifests

Gate-only items can become `Full` only against their replacement contract, not the original live notebook behavior.

For example:

```text
#39 Full gate parity:
  proves the app correctly blocks probability overlay until probability maps and approval gates exist.

#40 Full gate parity:
  proves the app correctly blocks GPS/path tracing until probability maps, target records, stairs seed, and coordinate/privacy gates exist.
```

They cannot be full matches to the original notebook behavior until real model/probability/path outputs are approved and implemented.

## Initial B1 item order

Start with items that have concrete local outputs and do not require model weights or probability maps:

```text
1. #33 Metal fingerprint diagnostic
2. #24 Hard classifier
3. #25 Target CSV/TXT/JSON outputs
4. #26 GeoJSON detected-feature exports
5. #23 ROI-constrained AI analysis inside 17m focus
6. #27 KMZ heatmap / 3D target visualization, private exact/redacted comparison
7. #34 Field-operation KMZ outputs, private exact/redacted comparison
```

Then compare tensor/raster items:

```text
#8, #9, #15, #17, #18, #19, #20, #29
```

Gated items should be handled last:

```text
#28, #30, #31, #32, #39, #40
```

## B1 status labels

Use these labels in docs/tests:

```text
Partial:
  App output exists, but frozen notebook comparison is missing or failed.

Full:
  App output matches frozen notebook reference according to the approved comparison method.

Full gate parity:
  App gate manifest matches the approved safe replacement contract. This is not the same as full live-notebook behavior.

Blocked from full live parity:
  Original notebook behavior requires unapproved model weights, runtime, probability maps, exact-coordinate outputs, or operator/privacy gates.
```

## Acceptance checklist for marking an item Full

An item can be marked `Full` only when all of these are true:

```text
canonical notebook cell is documented
notebook reference outputs are frozen
reference file hashes are recorded
app output path is documented
comparison method is documented
comparison test/report passes
privacy policy is respected
no sensitive reference output is committed publicly by accident
aggregate Plan B table is updated
```

## Immediate next B1 task

Start with:

```text
B1 item #33 parity freeze:
  notebook cell: cell_185
  notebook output family: AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2
  app output family: full_job/focus/AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.{csv,json,txt}
```

Goal:

```text
Freeze existing notebook CSV/JSON/TXT outputs.
Compare them against app CSV/JSON/TXT outputs.
If they match, mark item #33 Full.
If they do not match, document exact row/column/field mismatch and keep Partial.
```
