# Phase 2 Item #19 — Tesla v7.2 Inference Engines

Status: App-port / no exact notebook export.

## Canonical notebook cell

```text id="ygkb3v"
cell 095:
  Tesla v7.2 atomic/treasure inference image.
  source: COPERNICUS/S2_SR_HARMONIZED
  time range: 2022-01-01 to 2026-03-01
  cloud threshold: CLOUDY_PIXEL_PERCENTAGE < 5
  selected bands: B1, B2, B3, B4, B8, B8A, B11, B12
```

Notebook `treasure_arsenal` band order:

```text id="pfdmjl"
0. AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640
1. AI_BEH_Artifacts_Jars_Chests_DOM_lin_640
2. AI_BEH_Mercury_RareChemicals_DOM_lin_640
3. AI_BEH_Gemstones_AncientGlass_DOM_lin_640
4. AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640
```

## Notebook export availability

The downloaded notebook export did not contain exact references for:

```text id="4igou0"
TESLA_V7_2_ATOMIC_INFERENCE_STACK_640.npy
TESLA_V7_2_ATOMIC_INFERENCE_STACK_640.tif
```

The export scan found related per-band TIF candidates, but no exact stack reference. Full exact-file parity is therefore blocked.

## App validation

```text id="0yol4t"
TESLA_V7_2_ATOMIC_INFERENCE_STACK_640.npy:
  exists
  shape: 640x640x5
  dtype: float32
  per-band NPY outputs: present
  per-band TIF outputs: present
  stack-vs-band max delta: 0.0
```

Validated app band order:

```text id="d8344p"
0. AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640
1. AI_BEH_Artifacts_Jars_Chests_DOM_lin_640
2. AI_BEH_Mercury_RareChemicals_DOM_lin_640
3. AI_BEH_Gemstones_AncientGlass_DOM_lin_640
4. AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640
```

## Validator note

```text id="qbwjcy"
The first structure validator failed because it appended an extra _640 suffix to band names that already ended in _640.
The corrected validator checked both {band}.npy/{band}.tif and {band}_640.npy/{band}_640.tif forms.
Corrected validation passed with max delta 0.0.
```

## Decision

```text id="fkm9z9"
No code patch.
Keep app implementation.
Do not mark Full exact-file parity unless exact notebook stack refs appear and private comparison passes.
```
