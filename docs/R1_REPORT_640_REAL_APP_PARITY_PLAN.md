# R1 REPORT_640 real app-vs-reference parity plan

Status: plan ready.

This is a planning document only.

No runtime code was changed.

No verifier code was changed.

No API or frontend code was changed.

No private artifacts were committed.

No raster files were generated.

## Goal

Move `R1 REPORT_640 real app-vs-reference parity` from blocked to runnable by defining the exact app-output, reference, and verifier gates.

## Current source-of-truth status

`R1 REPORT_640 real app-vs-reference parity` is currently blocked, not failed.

The unblock condition is:

```text
produce matching app-generated output on the D1C grid/source contract
prove CRS, scale, shape, transform/origin, dtype, band count, and semantics
run the existing D2-gated verifier/CLI against the frozen reference bundle
```

## Required REPORT_640 outputs

The R1 target family is exactly:

```text
REPORT_640_Pottery_Report.tif
REPORT_640_Mass_Report.tif
REPORT_640_FINAL_Zero_Point_Targets.tif
```

`QA/REPORT_640_manifest.json` is useful if present, but it is not sufficient to prove raster value parity.

## Existing verifier path

The existing verifier path is:

```text
scripts/d1_compare_report_value_parity.py
```

The verifier requires:

```text
--app-output-dir <private app REPORT_640 output root>
--reference-report-root <private frozen D1C reference REPORT_640 root>
--report <private verifier report path>
```

Expected verifier result to close R1:

```text
status: passed
pass_count: 3
fail_count: 0
missing_count: 0
comparison_unavailable_count: 0
```

The verifier report must remain outside Git.

## R1 gate sequence

### Gate 1 — locate private frozen D1C reference

Confirm the private frozen reference contains all three required `REPORT_640` TIFs.

Required evidence:

```text
reference root exists outside Git
three required reference TIFs exist
reference bundle identity is known
D2 validator passes for the reference bundle
```

If the reference files are missing locally, stop and reconcile the D1/D1C docs before continuing.

### Gate 2 — produce matching app-generated outputs

Produce the app-generated `REPORT_640` outputs without copying or fabricating reference files.

Required evidence:

```text
app output root exists outside Git or under a private run directory
three required app TIFs exist
outputs were produced by the app pipeline or approved app writer path
outputs are not renamed notebook reference files
```

### Gate 3 — prove D1C grid/source contract

Before value parity, verify the app outputs use the same grid/source contract as the frozen D1C reference.

Required checks:

```text
CRS
scale
width / height
transform / origin
band count
shape convention
dtype
nodata
output semantics
```

### Gate 4 — run D2-gated REPORT_640 verifier

Run the existing verifier against private app outputs and the frozen reference.

Template command:

```powershell
python scripts/d1_compare_report_value_parity.py `
  --app-output-dir <PRIVATE_APP_REPORT_640_ROOT> `
  --reference-report-root <PRIVATE_D1C_REPORT_640_REFERENCE_ROOT> `
  --report <PRIVATE_R1_REPORT_640_PARITY_REPORT_JSON> `
  --json
```

The report path must stay outside Git.

### Gate 5 — record result

Only after the verifier passes, record a docs-only result with:

```text
reference bundle identity
app output source/run identity
verifier command shape
status
pass_count
fail_count
missing_count
comparison_unavailable_count
tolerance
private report path category, not raw private rows or coordinates
```

Do not include private raster contents, exact coordinates, or private file payloads in Git.

## Blocked until these are known

R1 cannot be marked passed until all of these are true:

```text
reference REPORT_640 root located
app REPORT_640 output root located or generated
all three required app TIFs present
all three required reference TIFs present
D1C grid/source contract confirmed
D2-gated verifier status is passed
```

## Safety boundary

Still blocked:

```text
public REPORT_640 downloads
HTTP serving of REPORT_640 rasters
map overlays
raw private raster payloads in Git
coordinate-bearing public exposure
claiming parity from file existence alone
```

Allowed:

```text
private local verifier report
aggregate/pass-fail status docs
safe counts and status fields
```

## Current R1 checklist

```text
[x] R1 plan written
[ ] locate private D1C REPORT_640 reference root       <- NEXT
[ ] locate or generate private app REPORT_640 output root
[ ] confirm three required reference TIFs
[ ] confirm three required app TIFs
[ ] run grid/source contract check
[ ] run D2-gated value verifier
[ ] record R1 verifier result
```

## Decision

```text
r1_report_640_real_app_parity_plan_ready
```
