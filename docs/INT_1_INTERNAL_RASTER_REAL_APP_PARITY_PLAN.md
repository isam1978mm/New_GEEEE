# INT-1 internal raster real app-vs-reference parity plan

Status: plan ready.

This is a planning document only.

No runtime code was changed.

No verifier code was changed.

No API or frontend code was changed.

No private artifacts were committed.

No raster files were generated.

## Goal

Move `INT-1 internal raster real app-vs-reference parity` from blocked to runnable by defining the exact reference, app-output, and verifier gates for the internal AI_BEH semantic raster families.

## Existing verifier

Existing CLI:

```text
python -m app.cli.internal_raster_verify
```

Existing delegated family verifiers:

```text
app/pipeline/parity/ai_beh_relation_verify.py
app/pipeline/parity/ai_beh_extended_verify.py
app/pipeline/parity/ai_beh_logic_verify.py
app/pipeline/parity/ai_beh_density_artifact_verify.py
app/pipeline/parity/ai_beh_rare_material_verify.py
app/pipeline/parity/ai_beh_alloy_statue_verify.py
```

The CLI is D2-gated. It validates the frozen reference bundle, delegates to the existing AI_BEH raster verifiers, prints a path-safe summary by default, and writes only JSON reports under `--run-dir`.

## Required output families

INT-1 covers six AI_BEH internal semantic raster families.

### ai_beh_relation

```text
AI_BEH_VegRoot_REL_ND_DOM_lin_640.tif
AI_BEH_IronOxide_REL_Ratio_DOM_lin_640.tif
AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640.tif
```

### ai_beh_extended

```text
AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640.tif
AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640.tif
AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640.tif
```

### ai_beh_logic

```text
AI_BEH_SecretEntry_REL_ND_DOM_lin_640.tif
AI_BEH_StatueLogic_REL_Diff_DOM_lin_640.tif
```

### ai_beh_density_artifact

```text
AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640.tif
AI_BEH_Artifacts_Jars_Chests_DOM_lin_640.tif
```

### ai_beh_rare_material

```text
AI_BEH_Mercury_RareChemicals_DOM_lin_640.tif
AI_BEH_Gemstones_AncientGlass_DOM_lin_640.tif
```

### ai_beh_alloy_statue

```text
AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif
```

Total required outputs:

```text
13 GeoTIFF rasters
```

## Important distinction from AIREADY-S1 and HYPER

AIREADY-S1 verified six AI_READY secret-layer rasters.

HYPER-1A verified 2.5 m resampled hypercube outputs.

HYPER-1B verified base-grid tensor/NPY outputs.

INT-1 verifies internal AI_BEH semantic GeoTIFF rasters at the 640 grid.

Do not treat AI_READY outputs, HYPER tensors, or HYPER RES_2p5M outputs as INT-1 evidence.

## Gate sequence

### Gate 1 — locate D2-valid reference files

Confirm the formal D2 bundle contains all 13 required INT-1 reference rasters.

Required evidence:

```text
reference_manifest.json exists in the D2 bundle root
all 13 required reference rasters exist
all 13 required reference rasters are listed in the manifest
reference files are not copied into Git
```

### Gate 2 — locate app-produced INT-1 files

Find matching app output files under the selected app run.

Required evidence:

```text
app output root exists under private/local run directory
all 13 required app rasters exist
files were produced by the app pipeline or approved app writer path
files are not copied/renamed notebook reference files
```

Known candidate runs from previous gates:

```text
a11309bf-ed47-4bf5-bbf4-f755b904065c
  matched R1 REPORT_640
  matched HYPER-1A source/resampled outputs
  matched HYPER-1B core tensors

e11d3280-a7b7-4c7c-a761-8b08ac9452f2
  matched AIREADY-S1 secret layers
  rejected for HYPER-1A and HYPER-1B
```

For INT-1, choose by evidence. Do not assume the correct run from prior tracks.

### Gate 3 — run metadata/source contract diagnostics

Before changing verifier policy, inspect any failure for:

```text
width / height
CRS
transform / origin delta
pixel size
dtype
nodata
band count
value max_abs_diff / mean_abs_diff
```

Known risk from prior gates:

```text
a113 often has benign transform/origin floating delta around 3.227032721042633e-06
```

Do not patch tolerance until the exact INT-1 failure is observed and classified.

### Gate 4 — run D2-gated verifier

Verifier command shape:

```powershell
python -m app.cli.internal_raster_verify `
  --app-output-dir <PRIVATE_APP_OUTPUT_ROOT> `
  --bundle-dir <PRIVATE_D2_REFERENCE_BUNDLE_ROOT> `
  --run-dir <PRIVATE_INT_1_RUN_DIR> `
  --run-id <RUN_ID>
```

Expected close result:

```text
overall_status: passed
family_count: 6
expected_count: 13
compared_count: 13
counts_by_status:
  passed: 13
```

Expected family results:

```text
ai_beh_relation: passed
ai_beh_extended: passed
ai_beh_logic: passed
ai_beh_density_artifact: passed
ai_beh_rare_material: passed
ai_beh_alloy_statue: passed
```

### Gate 5 — diagnose failures without changing data

Failure meanings:

```text
missing_app_output: app did not produce required raster
missing_reference_output: D2 reference bundle does not contain required raster
metadata_mismatch: raster metadata/grid contract differs
value_mismatch: raster values differ outside tolerance
comparison_unavailable: rasterio or value comparison unavailable
error: unexpected read/compare error
```

Do not copy, rename, or alias rasters to force a pass.

### Gate 6 — record INT-1 result

Only after pass:

```text
[ ] Add docs-only INT-1 result
[ ] Include reference bundle identity
[ ] Include selected app run identity
[ ] Include rejected candidate run identity if applicable
[ ] Include verifier command shape
[ ] Include family-level status counts
[ ] Include safe per-output summary
[ ] Include tolerance
[ ] Do not include private raster payloads
[ ] Do not include exact coordinate-bearing paths
[ ] Do not enable public downloads or serving
```

## Current INT-1 checklist

```text
[x] INT-1 plan written
[ ] locate D2-valid INT-1 reference files       <- NEXT
[ ] confirm all 13 reference rasters exist
[ ] confirm all 13 references are manifest-listed
[ ] locate app-produced INT-1 output root
[ ] confirm all 13 app rasters exist
[ ] run D2-gated verifier on candidate app run
[ ] diagnose failures if any
[ ] patch verifier policy only if evidence supports benign variance
[ ] rerun verifier if policy is patched
[ ] record INT-1 verifier result
```

## Safety boundary

Still blocked:

```text
public INT-1 downloads
HTTP serving of INT-1 rasters
map overlays
raw private raster payloads in Git
coordinate-bearing public exposure
claiming broader semantic raster parity from INT-1 alone
claiming broader notebook parity from this result alone
```

Allowed:

```text
private local verifier report
safe docs-only pass/fail result
safe counts and status fields
safe selected/rejected app run ids
```

## Decision

```text
int_1_internal_raster_real_app_parity_plan_ready
```

## Next actionable item

```text
INT-1 Gate 1: locate D2-valid internal raster reference files
```
