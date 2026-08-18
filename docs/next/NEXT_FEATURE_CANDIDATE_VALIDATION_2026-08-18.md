# Next Feature — Candidate Validation

Date: 2026-08-18  
Status: PLANNED  
Target branch: `main` documentation only

## Purpose

Add a validation stage after Candidate Focus that answers a practical question for each selected candidate:

> Is this candidate a compact, repeatable anomaly supported by multiple independent data types, or can it be explained by surface, terrain, acquisition geometry, vegetation, drainage, roads, or raster-edge effects?

The output must be an operator-facing validation result such as `PASS`, `MIXED`, or `FAIL`, with the evidence behind that decision.

This feature is a follow-up validation layer. It is not a replacement for the classifier, and it must not silently change classifier behavior.

## Current app state

The app already produces Candidate Focus for the highest-ranked scene candidates and preserves the original user-coordinate Focus.

The current science/support stack already contains useful inputs including:

- radar: `VV_dB`, `VH_dB`, `logRatio_dB`;
- terrain: `curvature`, `TPI`, `TRI`, `roughness`, `slope`, `aspect`, `TWI`;
- thermal: `lst`;
- optical/environmental support such as `NDVI`, `NDWI`, `NDMI`, `NBR`, `BSI`;
- existing Focus-specific derived layers and reports, including thermal-inertia and report products.

Candidate Focus currently performs detailed analysis around selected candidates, but it does not yet combine these independent evidence sources into a clear candidate-validation decision.

## Verified ASC/DESC state before implementation

The ASC/DESC question was checked in the current `main` code before starting Candidate Validation implementation.

The current SAR stage **does acquire and use both Sentinel-1 orbit directions**:

- it builds separate `ASCENDING` and `DESCENDING` collections;
- it selects matching ascending/descending scene pairs under the existing SAR timing constraints;
- it records the selected pair metadata, including ascending image ID, descending image ID, dates, and time difference, in `QA/sar/sar_pair_diagnostics.json`.

However, the current processing path combines each selected ascending image and descending image into a median pair image, then combines the pair images again into the final radar product. The completed run therefore preserves the combined radar outputs such as `VV_dB`, `VH_dB`, and `logRatio_dB`, but it does **not** currently preserve separate processed ASC and DESC raster products for later Candidate Focus validation.

Therefore the current verified status is:

- ASC data are acquired: **YES**;
- DESC data are acquired: **YES**;
- ASC/DESC pair identities and timing metadata are preserved: **YES**;
- separate processed ASC raster evidence available to Candidate Focus after the run: **NO**;
- separate processed DESC raster evidence available to Candidate Focus after the run: **NO**;
- true candidate-level ASC-versus-DESC spatial consistency test on existing completed runs: **UNAVAILABLE**.

This distinction is important. Pair metadata proves that both viewing directions contributed to the radar processing, but it is not sufficient to prove that a candidate anomaly appears independently in each viewing direction.

No implementation work is authorized by this documentation update.

## Required next feature

For each Candidate Focus candidate, add a Candidate Validation stage that evaluates the candidate across several independent evidence groups.

### 1. Radar evidence

Evaluate whether the candidate is spatially distinct and locally consistent in radar evidence such as:

- `VV_dB`;
- `VH_dB`;
- `logRatio_dB`.

The validation should compare the candidate/core area with a surrounding ring or local background. A signal that appears only in one layer should be treated more cautiously than a spatially aligned signal supported by multiple radar measures.

### 2. ASC/DESC consistency

For existing completed runs produced by the current pipeline, report candidate-level ASC/DESC consistency as `UNAVAILABLE`, because the separately processed ASC and DESC raster products are not preserved after they are combined into the final radar product.

Do not infer ASC/DESC consistency from:

- the existence of ASC/DESC pair metadata;
- the final combined `VV_dB`, `VH_dB`, or `logRatio_dB` products;
- unrelated radar or Focus layers.

For future runs, true ASC/DESC consistency may be added only if the implementation explicitly preserves separate processed ASC and DESC evidence products before the current median combination step. Candidate Validation could then compare whether the anomaly remains spatially consistent between the two viewing geometries.

Preserving separate ASC/DESC evidence must not change the existing final combined radar product or classifier behavior.

### 3. Thermal evidence

Evaluate available thermal evidence, including `lst` and existing thermal-inertia products where appropriate, to determine whether the same candidate location behaves differently from its local surroundings.

Thermal support is corroborating evidence only. It must not be interpreted as proof of a buried object or material type.

### 4. Terrain and surface explanation check

Use terrain and environmental layers to test whether the anomaly may be explained by visible or natural surface structure, including:

- `TPI`;
- `TRI` / roughness;
- curvature;
- slope/aspect;
- drainage-related terrain behavior where supported;
- vegetation or moisture differences where the available indices support that interpretation.

The purpose is to reduce false positives caused by hills, depressions, ridges, drainage, vegetation, soil/surface transitions, or similar context.

### 5. Shape and compactness check

Measure whether the anomaly is compact and centered around the candidate rather than forming a long linear or edge-following pattern.

Long strips, raster-edge artifacts, road-like features, drainage-like features, or broad terrain-following responses should reduce confidence.

The implementation must derive shape/compactness from data available in the run. It must not assume that a small buried target has been physically confirmed.

## Decision outputs

Each evaluated candidate should receive one of these operator-facing results:

### PASS

Use when the candidate shows consistent localized support across multiple independent evidence groups and there is no strong surface/terrain explanation in the available data.

A `PASS` means:

> This candidate is strong enough to justify more expensive or higher-confidence follow-up.

It does **not** mean that a jar, statue, metal object, cavity, or other physical target has been confirmed.

### MIXED

Use when some evidence supports the candidate but other evidence is weak, contradictory, unavailable, or plausibly explained by surface/terrain effects.

A `MIXED` candidate may justify additional data if the expected value of follow-up is high, but it should not automatically trigger paid imagery.

### FAIL

Use when the anomaly is poorly localized, inconsistent across evidence, or strongly explained by surface/terrain/context effects in the available data.

A `FAIL` candidate should not be recommended for paid imagery based on the current run.

## Paid imagery recommendation

Paid imagery must be downstream of Candidate Validation, not triggered directly by a classifier score or notebook-derived interpretation label.

Recommended decision flow:

`Classifier / interpretation -> Candidate Focus -> Candidate Validation -> PASS / MIXED / FAIL -> follow-up recommendation`

Operator recommendation:

- `PASS` -> recommend higher-resolution paid imagery and/or field verification when practical;
- `MIXED` -> paid imagery is optional and should depend on cost, missing evidence, and expected value;
- `FAIL` -> do not recommend spending money on paid imagery for that candidate based on the current evidence.

## Critical guardrails

1. **Do not change the classifier.** Candidate Validation is an independent post-classifier stage.
2. **Do not change existing classifier scores or labels.** Preserve their current meaning and provenance.
3. **Do not change the NB depth formula as part of this feature.**
4. **Do not present NB proxy depth as calibrated or validated numerical depth.**
5. **Do not convert an interpretation label such as `jar_جرة` or `statue_تمثال` into physical confirmation.** These remain screening interpretations.
6. **Do not invent unavailable evidence.** Existing completed runs must report true candidate-level ASC/DESC consistency as unavailable under the current artifact contract.
7. **Do not silently create scientific thresholds.** PASS/MIXED/FAIL thresholds and evidence-combination rules must be explicitly designed, documented, tested, and reviewed before implementation.
8. **Keep User Focus and Candidate Focus behavior intact.** Candidate Validation extends Candidate Focus; it does not replace it.
9. **Preserve guarded/private artifact handling.** Validation outputs must follow the existing local/private output rules.
10. **Do not alter the existing combined SAR result when adding future ASC/DESC preservation.** Separate evidence products, if added, are additional validation inputs only.

## Required implementation sequence

Before code changes, define and review the exact validation contract:

1. identify which evidence groups are reliably available in completed runs;
2. define core-versus-ring/local-background measurements for each evidence group;
3. define shape/compactness metrics;
4. define handling for missing evidence, including current-run ASC/DESC `UNAVAILABLE` behavior;
5. define explicit, scientifically conservative `PASS`, `MIXED`, and `FAIL` rules;
6. define an explanation payload showing why each candidate received its result;
7. decide separately whether future runs should preserve processed ASC and DESC evidence products before radar combination;
8. add tests proving the classifier, existing combined SAR result, and depth paths are unchanged;
9. expose the result in the UI as a separate Candidate Validation section;
10. connect paid-imagery recommendation only after the validation decision.

## Intended operator-facing result

Example only; values and thresholds are not yet approved:

```text
Candidate 1 — PASS
Radar: supportive
Thermal: supportive
Terrain explanation: low
Shape: compact
ASC/DESC: unavailable for this completed run
Recommendation: higher-resolution paid imagery / further verification
```

The UI must also show the evidence behind `MIXED` and `FAIL` decisions so the operator can understand why money should or should not be spent on follow-up.

## Acceptance criteria

This feature is complete only when:

- Candidate Validation runs after Candidate Focus without modifying the classifier;
- each selected candidate receives a traceable `PASS`, `MIXED`, or `FAIL` result;
- the result includes evidence-group explanations and unavailable-data states;
- existing completed runs do not falsely claim candidate-level ASC/DESC consistency;
- if separate ASC/DESC validation is later enabled for future runs, the existing combined SAR output remains unchanged;
- the app does not claim physical confirmation or validated numerical depth;
- paid-imagery recommendation follows the validation result rather than raw classifier or interpretation score alone;
- existing User Focus, Candidate Focus, classifier, and NB/depth behavior remain backward compatible;
- automated tests protect these guardrails.
