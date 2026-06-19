# AIREADY-S1 Secret Layers verifier result

Status: passed.

This document records safe verifier status only.

No raster payloads are included.

No exact coordinate-bearing private paths are included.

No public downloads were enabled.

No API or frontend code was changed.

No private artifacts were committed.

## Verifier

```text
CLI: python -m app.cli.secret_layers_verify
schema: secret_layers_parity_verification_v1
result: passed
```

The verifier was run with:

```text
D2 manifest bundle root: D1_NEW_IPYNB_REFERENCE_2026_06_10
reference output subdir: AI_READY_640
app run id: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
run id: aiready-s1-e11d3280
```

A different app run candidate was rejected before this result:

```text
rejected app run id: a11309bf-ed47-4bf5-bbf4-f755b904065c
reason: different grid/location from the D2 AIREADY reference bundle and values did not match
```

## Required outputs

```text
AI_READY_640_Secret_Gold_Halo.tif
AI_READY_640_Secret_Silver_Oxide.tif
AI_READY_640_Secret_Tunnel_Ceiling.tif
AI_READY_640_Secret_Thermal_Inertia.tif
AI_READY_640_Secret_Chemical_Protector.tif
AI_READY_640_Secret_Hidden_Doors.tif
```

## Result summary

```text
overall_status: passed
expected_count: 6
compared_count: 6
counts_by_status:
  passed: 6
```

## Tolerance policy

```text
atol: 1e-06
rtol: 1e-06
```

## Output-level results

### AI_READY_640_Secret_Chemical_Protector

```text
status: passed
hash_match: true
within_tolerance: true
count_compared_pixels: 409600
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

### AI_READY_640_Secret_Gold_Halo

```text
status: passed
hash_match: true
within_tolerance: true
count_compared_pixels: 409600
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

### AI_READY_640_Secret_Hidden_Doors

```text
status: passed
hash_match: true
within_tolerance: true
count_compared_pixels: 405902
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

Note: `Secret_Hidden_Doors` had fewer compared pixels because nodata/masked pixels were excluded from numeric comparison. The output still passed and had `hash_match: true`.

### AI_READY_640_Secret_Silver_Oxide

```text
status: passed
hash_match: true
within_tolerance: true
count_compared_pixels: 409600
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

### AI_READY_640_Secret_Thermal_Inertia

```text
status: passed
hash_match: true
within_tolerance: true
count_compared_pixels: 409600
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

### AI_READY_640_Secret_Tunnel_Ceiling

```text
status: passed
hash_match: true
within_tolerance: true
count_compared_pixels: 409600
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

## Safety boundary

Still blocked:

```text
public AIREADY downloads
HTTP serving of AIREADY rasters
map overlays
raw private raster payloads in Git
coordinate-bearing public exposure
claiming all AIREADY parity from AIREADY-S1 alone
claiming broader notebook parity from this result alone
```

Allowed and completed:

```text
D2-gated private local verifier report
safe docs-only pass/fail result
safe counts and status fields
```

## AIREADY-S1 checklist closeout

```text
[x] AIREADY plan written
[x] six reference TIFs confirmed
[x] six app TIFs confirmed
[x] D2 bundle root identified
[x] nested reference output directory support added to CLI
[x] CLI tests passed
[x] nonmatching app candidate rejected
[x] matching app candidate selected
[x] secret-layer verifier passed
[x] AIREADY-S1 verifier result recorded
```

## Decision

```text
aiready_s1_secret_layers_real_app_vs_reference_parity_passed
```

## Remaining AIREADY work

```text
[ ] AIREADY-FR Fraction outputs: source known, app writer/output path still needed
[ ] AIREADY-MH Metal Hardness: source-recovery blocked
[ ] AIREADY-AN Magnetic/EM anomaly: source-recovery blocked
```

## Next recommended task

```text
HYPER-1A RES_2p5M real app-vs-reference parity plan
```
