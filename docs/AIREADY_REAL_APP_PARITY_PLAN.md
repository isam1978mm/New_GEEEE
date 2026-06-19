# AIREADY real app-vs-reference parity plan

Status: plan ready.

This is a planning document only.

No runtime code was changed.

No verifier code was changed.

No API or frontend code was changed.

No private artifacts were committed.

No raster files were generated.

## Goal

Move `AIREADY real app-vs-reference parity` from a broad blocked item into ordered, runnable sub-gates.

Do not treat all `AI_READY` families as one equal-readiness task. The repo already has different readiness levels by subfamily.

## AIREADY family split

### AIREADY-S1 — Secret-layer rasters

Status: next runnable verifier path.

Required outputs:

```text
AI_READY_640_Secret_Gold_Halo.tif
AI_READY_640_Secret_Silver_Oxide.tif
AI_READY_640_Secret_Tunnel_Ceiling.tif
AI_READY_640_Secret_Thermal_Inertia.tif
AI_READY_640_Secret_Chemical_Protector.tif
AI_READY_640_Secret_Hidden_Doors.tif
```

Reason this is first:

```text
reference files are expected in the frozen notebook bundle
app outputs are expected under the app run AI_READY_640 layout
an existing secret-layer verifier/CLI exists
no source-recovery or writer implementation is required before the first check
```

Existing contract:

```text
docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md
```

Expected app layout:

```text
data/runs/<run_id>/AI_READY_640/
```

Expected verifier report:

```text
data/runs/<run_id>/manifests/secret_layers_parity_verification.json
```

Safety boundary:

```text
LOCAL_SENSITIVE
not public/shared
not HTTP servable
no map overlays
no raster payloads in Git
```

### AIREADY-MH — Metal Hardness

Status: blocked/source-recovery.

Required output:

```text
AI_READY_640_Metal_Hardness.tif
```

Current known blocker:

```text
standalone writer formula remains unrecovered
app does not write this notebook-named output explicitly
```

This subfamily should not block AIREADY-S1 secret-layer verification.

Existing contract:

```text
docs/AI_READY_METAL_HARDNESS_PARITY_CONTRACT.md
```

### AIREADY-FR — Fraction rasters

Status: source known, app-output/writer path still needed before verification.

Required outputs:

```text
AI_READY_640_Fraction_Gold.tif
AI_READY_640_Fraction_Pottery.tif
AI_READY_640_Fraction_Carbon_Age.tif
AI_READY_640_Fraction_Silver_Lead.tif
```

Recovered source formulas exist, but the current app does not write these notebook-named outputs explicitly.

This subfamily comes after AIREADY-S1 unless the operator chooses a source-recovery/build task first.

Existing contract:

```text
docs/AI_READY_FRACTION_PARITY_CONTRACT.md
```

### AIREADY-AN — Magnetic / EM anomaly rasters

Status: blocked/source-recovery.

Required outputs:

```text
AI_READY_640_Magnetic_Anomaly.tif
AI_READY_640_EM_Anomaly.tif
```

Current known blocker:

```text
standalone writer formula remains unrecovered
app does not write these notebook-named outputs explicitly
```

Existing contract:

```text
docs/AI_READY_ANOMALY_PARITY_CONTRACT.md
```

## AIREADY-S1 gate sequence

### Gate 1 — locate private frozen AIREADY-S1 reference root

Confirm the frozen D1C reference bundle contains the six required `AI_READY_640_Secret_*` TIFs.

Required evidence:

```text
reference root exists outside Git
six required reference TIFs exist
reference bundle identity is known
reference files are not copied into Git
```

### Gate 2 — locate private app AIREADY-S1 output root

Confirm the selected app run contains the six required `AI_READY_640_Secret_*` TIFs under the app output layout.

Required evidence:

```text
app output root exists under a private/local run directory
six required app TIFs exist
outputs were produced by app pipeline or approved app writer path
outputs are not copied/renamed notebook reference files
```

### Gate 3 — run metadata/value verifier

Use the existing secret-layer verifier path or CLI.

Expected close result:

```text
overall_status: passed
all six outputs: passed
runtime_output_verified: true
notebook_value_parity_verified: true
```

If the verifier fails only because of benign metadata policy already accepted in R1, do not edit rasters. Instead, update verifier policy with tests before rerunning.

### Gate 4 — record AIREADY-S1 result

Only after the verifier passes, record a docs-only result with:

```text
reference bundle identity
app output source/run identity
verifier command shape or helper invocation
status counts
safe tolerance/metadata policy
no private raster contents
no exact coordinates
no private file payloads
```

## Current AIREADY checklist

```text
[x] AIREADY plan written
[ ] AIREADY-S1 locate private secret-layer reference root       <- NEXT
[ ] AIREADY-S1 confirm six reference TIFs
[ ] AIREADY-S1 locate private app secret-layer output root
[ ] AIREADY-S1 confirm six app TIFs
[ ] AIREADY-S1 run secret-layer verifier
[ ] AIREADY-S1 record verifier result
[ ] AIREADY-FR decide whether to build Fraction output writer path
[ ] AIREADY-MH source-recovery decision
[ ] AIREADY-AN source-recovery decision
```

## Blocked until later

Do not mark all AIREADY parity complete until these are handled:

```text
AIREADY-S1 secret layers passed
AIREADY-FR Fraction outputs either passed or explicitly deferred as writer-path work
AIREADY-MH Metal Hardness resolved or explicitly kept source-blocked
AIREADY-AN Magnetic/EM anomaly resolved or explicitly kept source-blocked
```

## Safety boundary

Still blocked:

```text
public AIREADY downloads
HTTP serving of AIREADY rasters
map overlays
raw private raster payloads in Git
coordinate-bearing public exposure
claiming broader notebook parity from AIREADY-S1 alone
```

Allowed:

```text
private local verifier report
safe docs-only pass/fail result
safe counts and status fields
```

## Decision

```text
aiready_real_app_parity_plan_ready
```

## Next actionable item

```text
AIREADY-S1 Gate 1: locate private secret-layer reference root
```
