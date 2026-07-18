# Depth Feature Inventory

Status: Phase 1 inventory complete for the current repository state. This document does not approve or implement a depth model.

## Scope and hard boundary

The current app cannot estimate physical depth in metres.

Names such as `NANO_Depth_Penetration`, `UGS_DeepStruct_RVI`, and `UGS_BaseDeep` are signal ratios, transforms, or threshold labels. They are not depth measurements.

Allowed current app output remains:

```text
depth_not_available
```

An experimental relative label such as `shallow-looking`, `medium-looking`, or `deep-looking` may be researched later, but it must not be shown as a validated result until known-depth calibration and held-out validation exist.

No classifier output, target mask, `REPORT_640` layer, generated depth label, PCA result, or other downstream decision layer is approved as independent depth evidence.

## Evidence reviewed

- `AUDIT_DO_NOT_BREAK_CONTRACTS.md`
- `docs/LOCAL_PRIVATE_CORE_CLASSIFIER_EXECUTION_PLAN_2026-07-15.md`
- `docs/DEPTH_ESTIMATION_EXECUTION_PLAN_2026-07-17.md`
- `docs/PRD_v0.5.md` as historical context only
- `docs/Notebook_Cells_E.md`
- `docs/PHASE2_ITEM08_NANO_GEOPHYSICS_STATUS.md`
- `docs/PLAN_B_NOT_DONE_NOTEBOOK_FEATURES_TO_APP.md`
- `app/pipeline/stages/sar_rtc.py`
- `app/pipeline/stages/feature_stacks.py`
- `app/pipeline/stages/s2_indices.py`
- `app/pipeline/stages/thermal.py`
- `app/pipeline/stages/dem.py`
- `app/pipeline/stages/dem_derivatives.py`
- `app/pipeline/stages/object_extract.py`
- `app/pipeline/stages/focus_mask.py`
- `app/pipeline/parity/ai_tensor_builder.py`

The separately supplied 19-cell paid-imagery shortlist notebook is not the historical 244-cell source notebook described by the repository inventory and contains no physical-depth formula. Canonical depth-related notebook evidence therefore comes from the repository's notebook inventory and previously inspected canonical-cell records.

## Classification rules

- **Measured sensor input**: comes directly from a sensor product or acquisition metadata.
- **Derived sensor feature**: deterministic transform of measured bands; it is not independent of its source bands.
- **Heuristic label**: threshold, rule, or name that implies meaning not established by calibration.
- **Downstream decision output**: PCA, classifier, target mask, report layer, or visualization result.
- **Quality gate**: describes data usability; suitable for abstention but not as physical depth evidence.

## Primary measured inputs

| feature_name | notebook_cell | app_file | source_sensor | source_bands | exact_formula | unit | spatial_resolution | acquisition_dependency | nodata_behavior | normalization | expected_depth_relationship | known_confounders | independent_sensor_evidence | allowed_for_depth_research | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `VV_dB` | 21/24 and later reuses | `app/pipeline/stages/sar_rtc.py` | Sentinel-1 GRD IW SAR | VV | dB backscatter after local DEM/incidence correction; linear conversion is `10^(VV_dB/10)` | dB | 10 m app GRID | selected ascending/descending pairs, orbit, date window, speckle filtering, RTC | invalid source, angle, or DEM pixels become GRID nodata | none in canonical raster | unknown; may contain depth-correlated response only after calibration | surface roughness, soil moisture, vegetation, target size/material, incidence angle, orbit, speckle, terrain | yes | yes, as a raw candidate and confounder-controlled input | genuine sensor measurement, but not a depth measurement |
| `VH_dB` | 21/24 and later reuses | `app/pipeline/stages/sar_rtc.py` | Sentinel-1 GRD IW SAR | VH | dB backscatter after local DEM/incidence correction; linear conversion is `10^(VH_dB/10)` | dB | 10 m app GRID | same as VV | same as VV | none in canonical raster | unknown | same as VV, with additional cross-polarization sensitivity | yes | yes, as a raw candidate and confounder-controlled input | genuine sensor measurement, but not a depth measurement |
| `incidence` | 21/24 | `app/pipeline/stages/sar_rtc.py` | Sentinel-1 acquisition metadata | angle | sampled acquisition angle, retained where finite | degrees | 10 m app GRID | orbit geometry and selected scenes | invalid angle becomes GRID nodata | none | not a depth signal; required geometry/confounder control | terrain, orbit, layover/shadow geometry | yes | yes, as a control feature only | must control SAR geometry before interpreting ratios |
| Sentinel-2 reflectance source bands | 76/77/81 and core S2 stage | `app/pipeline/stages/s2_indices.py` | Sentinel-2 SR Harmonized | B2, B3, B4, B8, B11, B12, B1 | median composite; reflectance scale constant `0.0001` is recorded | scaled reflectance / dimensionless | resampled to 10 m app GRID; native bands differ | 2022-01-01 to 2026-02-28, cloud filter, seasonal composition | zero-valid source bands or zero shared-valid pixels fail the stage | no normalization in core source cube | no established direct depth relation; useful for surface, soil, moisture, vegetation, and material confounders | clouds, season, illumination, vegetation, soil type, moisture, mixed pixels, resampling | yes, independent of SAR | yes, mainly as context/confounder features | independent sensor evidence, but surface-dominated |
| `lst` | 145/146 and thermal stage | `app/pipeline/stages/thermal.py` | Landsat 8/9 Collection 2 L2 | ST_B10 | `ST_B10 * 0.00341802 + 149.0`, cloud/shadow/cirrus masked, temporal median | kelvin | resampled to 10 m app GRID; source is coarser | 2022-01-01 to 2026-02-28, L8/L9 availability and cloud mask | invalid pixels become GRID nodata; minimum valid fraction enforced | none in canonical `lst` | unproven; thermal inertia/anomaly may be context-dependent, not direct depth | time of acquisition, season, surface material, moisture, vegetation, weather, source resolution | yes, independent of SAR | yes, as an exploratory context feature | independent sensor source with strong confounding |
| `dem` | 15/104/107/109 | `app/pipeline/stages/dem.py` | Copernicus DEM GLO-30 | DEM | source elevation sampled to authoritative GRID | metres elevation | 10 m app GRID from approximately 30 m source | DEM product/version and resampling | invalid pixels become GRID nodata; minimum valid fraction enforced | none | no direct depth relation; terrain control only | DEM error, resampling, slope, aspect, terrain scale | yes, independent of SAR/optical | yes, as a control feature only | required to separate terrain effects from apparent signal changes |

## Derived sensor features worth controlled investigation

All rows below are derived features. A `yes` in `allowed_for_depth_research` means offline investigation only, with known-depth calibration, grouped validation, confounder controls, and abstention. It does not approve app output.

| feature_name | notebook_cell | app_file | source_sensor | source_bands | exact_formula | unit | spatial_resolution | acquisition_dependency | nodata_behavior | normalization | expected_depth_relationship | known_confounders | independent_sensor_evidence | allowed_for_depth_research | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `logRatio_dB` / `NANO_Human_Geometry_Detector` | 24/28/31 and 37 | `sar_rtc.py`, `feature_stacks.py` | Sentinel-1 | VV, VH | `VV_dB - VH_dB` | dB difference | 10 m | inherits SAR acquisition | nodata unless both VV and VH valid | none | unknown | all VV/VH confounders | no; derived from VV/VH | yes | interpretable radar contrast, but not depth |
| `NANO_Depth_Penetration` | 37 | `app/pipeline/stages/feature_stacks.py` | Sentinel-1 | VV, VH | `VV_lin / (VH_lin + 1e-6)` | dimensionless ratio | 10 m | inherits SAR acquisition | output is GRID nodata unless both source bands are valid and result is finite | none in feature stack; later AI tensor may apply within-run p2/p98 normalization | unproven | moisture, roughness, vegetation, incidence, orbit, material, target size, denominator instability | no; derived from VV/VH | yes, but only under its neutral description `VV_to_VH_linear_ratio` | the name is misleading; investigate the ratio, never its claimed depth meaning |
| `NANO_Mass_Anomaly` | 37 | `feature_stacks.py` | Sentinel-1 | VV, VH | `sqrt(VV_lin * VH_lin)` | dimensionless backscatter combination | 10 m | inherits SAR acquisition | GRID nodata unless both bands valid | none | unknown | absolute calibration, terrain, moisture, material, target size | no | yes, exploratory only | may summarize joint return strength; not mass or depth |
| `NANO_RVI_Clean` | 37 | `feature_stacks.py` | Sentinel-1 | VV, VH | `4 * VH_lin / (VV_lin + VH_lin + 1e-6)` | dimensionless | 10 m | inherits SAR acquisition | GRID nodata unless both bands valid | none | unknown | vegetation, moisture, roughness, polarization response | no | yes, mainly as vegetation/structure context | radar vegetation-style index, not depth |
| `GEOPHYS_Sirdab_Cavity_Void` | 39 | `feature_stacks.py` | Sentinel-1 | VV, VH | `log(VV_lin) - log(VH_lin)` | log ratio, dimensionless | 10 m | inherits SAR acquisition | GRID nodata unless both bands valid | none | algebraically related to VV/VH ratio; no proven depth relation | same SAR confounders | no | yes only under a neutral log-ratio name | redundant with polarization ratio; the domain label is unsupported |
| `NANO_Metal_Signal_Pulse` | 39 | `feature_stacks.py` | Sentinel-1 | VV, VH | `(VH_lin * VV_lin) / (VV_lin + VH_lin + 1e-6)` | dimensionless | 10 m | inherits SAR acquisition | GRID nodata unless both bands valid | none | unknown | material, moisture, roughness, size, incidence | no | conditional | joint return transform; no metal or depth validation |
| `GEOLOGIC_Chamber_Entry_Proxy` | 39 | `feature_stacks.py` | Sentinel-1 | VV, VH | `VH_lin / (VV_lin^2 + 1e-6)` | dimensionless | 10 m | inherits SAR acquisition | GRID nodata unless both bands valid | none | unknown and potentially unstable at low VV | denominator sensitivity and all SAR confounders | no | conditional, low priority | weak interpretability; misleading domain name |
| `RAD_S0_VH_VV_Ratio_lin` | 50 | `feature_stacks.py` | Sentinel-1 | VV, VH | `10^((VH_dB - VV_dB)/10)` | dimensionless | 10 m | inherits SAR acquisition | GRID nodata unless VV/VH valid | none | unknown | same SAR confounders | no | yes | conventional polarization ratio form |
| `RADM_VH_VV_Ratio_lin` | 53 | `feature_stacks.py` | Sentinel-1 | VV, VH | `VH_lin / (VV_lin + 1e-10)` | dimensionless | 10 m | inherits SAR acquisition | GRID nodata unless VV/VH valid | none | unknown | same SAR confounders | no | yes | nearly duplicates other VH/VV ratios; collinearity must be controlled |
| `RAD_MasterVH_VV_Ratio_lin` | 47 | `feature_stacks.py` | Sentinel-1 | VV, VH | `VH_lin / (VV_lin + 1e-6)` | dimensionless | 10 m | inherits SAR acquisition | GRID nodata unless VV/VH valid | none | unknown | same SAR confounders | no | yes | duplicate ratio variant; do not treat duplicates as independent evidence |
| `AUX_VH_to_VV_MoistureProxy_lin` | 72 | `feature_stacks.py` | Sentinel-1 | VV, VH | `VH_lin / max(VV_lin, 1e-6)` | dimensionless | 10 m | inherits SAR acquisition | GRID nodata unless VV/VH valid | none | primarily a moisture/roughness proxy candidate, not depth | moisture, vegetation, roughness, incidence | no | yes as a confounder only | useful to test whether apparent depth signal is actually moisture |
| Core S2 indices | core S2 stage | `s2_indices.py` | Sentinel-2 | B2/B3/B4/B8/B11/B12 | NDVI `(B8-B4)/(B8+B4)`; NDWI `(B3-B8)/(B3+B8)`; NDMI `(B8-B11)/(B8+B11)`; NBR `(B8-B12)/(B8+B12)`; IRONOX `B4/B3`; IRON_SWIR `(B11-B12)/(B11+B12)`; BSI `((B11+B4)-(B8+B2))/((B11+B4)+(B8+B2))` | dimensionless | 10 m app GRID | inherits S2 composite | division by zero, nonfinite values, or nodata produce GRID nodata; zero-valid indices fail | none in canonical outputs | no proven direct depth relation | season, clouds, vegetation, soil, moisture, illumination, source resolution | yes relative to SAR | yes as independent context/confounder features | independent sensor family; retain core formulas, not target-like derived reports |
| `Secret_Thermal_Inertia` formula family | 145/thermal parity path | `thermal.py` | Landsat 9 | ST_B10 | `ST_B10 / (focal_mean_500m(ST_B10) + 1e-6)` | dimensionless relative thermal ratio | 10 m app GRID from coarser source | temporal median and cloud mask | unmasked values become GRID nodata | relative local ratio | unknown | surface material, weather, season, moisture, vegetation, resolution | yes relative to SAR | conditional; prefer canonical `lst` first | potentially useful only if separated from target-report logic |
| DEM derivatives | 104/107 and app stage | `dem_derivatives.py` | Copernicus DEM | DEM | slope from first gradients; aspect from `atan2`; curvature `d2z/dx2 + d2z/dy2`; TPI `DEM - local_mean_100m`; roughness local std; TRI local mean absolute deviation; TWI app formula `log((max(local_mean-DEM,0)+1)/max(tan(slope),1e-6))` | mixed: degrees, metres, inverse-distance-like curvature, dimensionless/log-like TWI | 10 m app GRID | DEM version/resampling only | source-invalid or nonfinite outputs become GRID nodata | none | no direct depth relation | terrain morphology and DEM error | yes | yes as confounder controls only | helps detect terrain-driven false relationships |

## Quality and acquisition metadata

These fields are allowed for gating, stratification, and abstention. They are not physical depth predictors by themselves.

| feature_name | source | exact meaning | allowed use |
|---|---|---|---|
| SAR per-band valid fraction | `sar_rtc.py` | finite non-nodata fraction for VV, VH, log ratio, and incidence | require minimum usability; abstain on poor coverage |
| SAR selected pair metadata | `sar_rtc.py` | selected ascending/descending scene IDs and time differences | stratify by orbit/time geometry; detect unstable acquisition sets |
| S2 per-source-band valid fraction | `s2_indices.py` | valid fraction for each required S2 band | gate unusable optical input |
| S2 shared-valid fraction | `s2_indices.py` | pixels valid across all required bands or all indices | gate formulas that would otherwise use mismatched masks |
| Thermal valid fraction | `thermal.py` | valid fraction for LST and raw thermal arrays | gate thermal feature availability |
| DEM valid fraction and nodata fraction | `dem.py` | usable DEM coverage | gate terrain controls |
| GRID alignment metadata | stage sidecars and alignment QA | CRS, transform, size, nodata consistency | mandatory before comparing spatial features |

## Rejected circular, generated, or misleading inputs

| feature_or_family | notebook_cell / app_file | classification | reason rejected for depth research |
|---|---|---|---|
| Classifier scores, class labels, finding family probabilities, summaries | classifier stages and outputs | downstream decision output | would teach a depth model to reproduce classifier rules rather than independent depth evidence |
| `REPORT_640_*` layers | cells 97/99 and `s2_indices.py` / `focus_mask.py` | threshold-derived report/decision layers | target-like generated layers; explicitly circular |
| PCA anomaly raster/raw score | cells 66/67 and PCA stage | downstream anomaly score | combines current features and may contain target-like leakage; not independent depth evidence |
| Object mask and thresholded connected components | cells 68/71 and `object_extract.py` | target mask | derived from PCA thresholding; not independent sensor evidence |
| Current object `area_px`, bounding box, centroid, anomaly mean/max | `object_extract.py` | threshold-derived geometry/score | current geometry depends on the PCA target mask. It may be reconsidered later only as a confounder after candidate selection is frozen independently. The current app does not compute perimeter, compactness, solidity, or physical object size. |
| Focus mask and 17 m focus outputs | cell 119 and `focus_mask.py` | display/analysis selection mask | spatial selection mechanism, not depth evidence |
| `NANO_Depth_Penetration` name | cell 37 | misleading label | formula is only a VV/VH linear ratio; never treat the name as evidence |
| `UGS_DeepStruct_RVI` | cell 54 and `feature_stacks.py` | heuristic transform | app formula uses gain-scaled dB values in `4*VH/(VV+VH+1e-6)`; no calibration or physical depth unit |
| `UGS_BaseDeep` | cell 54 and `feature_stacks.py` | heuristic threshold label | binary rule `-12 < 1.45*VV_dB < -7`; a thresholded dB band, not depth |
| `SIM_GPR_VoidScan_lin` | cell 73 and `feature_stacks.py` | simulated/misnamed SAR transform | formula is `log10(abs(VV_lin-VH_lin)+1e-6)`; it is not ground-penetrating radar |
| `SIM_MagneticAnomalies_lin` | cell 73 and `feature_stacks.py` | simulated/misnamed SAR texture | local Laplacian magnitude of VV; no magnetic sensor input |
| `SIM_EMI_Conductivity_lin` | cell 73 and `feature_stacks.py` | simulated/misnamed SAR ratio | formula is VH/VV; no EMI sensor input |
| `SIM_MicroGravity_Density_lin` | cell 73 and `feature_stacks.py` | simulated/misnamed SAR inverse-return transform | formula is inverse mean of VV/VH linear returns; no gravity sensor input |
| `TGT_*`, `ARCH_TARGETS_*`, `AI_BEH_*`, secret layers, full AI tensors | cells 52/95/97/148 and app parity/stack files | heuristic or target-oriented derived layers | contain threshold rules, target semantics, normalized mixtures, or downstream reports; not independent depth evidence |
| AI tensor p2/p98 normalized channels | `ai_tensor_builder.py` | within-run display/model normalization | destroys absolute scale and can make runs incomparable without a saved transform; not suitable as the authoritative calibration input |
| Cell 155 “depth-safe” KMZ fix and 3D KMZ altitude fields | notebook visualization cells | display-only | visualization geometry/altitude handling does not measure subsurface depth |
| Cell 214 `depth_file` arrays | notebook cell 214 | unknown-provenance input | no proven sensor source, formula, unit, calibration, or app equivalent; reject until provenance is recovered |
| Generated `shallow`, `medium`, `deep`, or numerical depth labels | future outputs | generated label | feeding a prior prediction back into the model is circular |

## Missing inputs and evidence

The following are absent or insufficient in the current app and block numerical depth estimation:

1. Known-depth calibration records with traceable top and bottom depth.
2. Held-out physical sites not used for fitting.
3. Soil/surface type, moisture, and season metadata tied to each reference case.
4. Target size, material/structure family, and reference-depth uncertainty.
5. Sentinel-1 coherence or another genuine multi-date phase/stability product. Repository search found no implemented SAR coherence feature.
6. Explicit temporal SAR stability features calculated from repeated acquisitions rather than a median composite alone.
7. Observation count and temporal-dispersion fields for each sensor composite.
8. Native-resolution and resampling provenance stored per feature.
9. Independently defined candidate geometry if object size/shape is to be tested without circular PCA-mask dependence.
10. Site-grouped validation, negative/no-target examples, and out-of-distribution checks.
11. A versioned feature manifest that excludes target-like and downstream-generated layers.

## Feature decision

### Allowed for later controlled depth research

- Raw Sentinel-1 `VV_dB`, `VH_dB`, and incidence angle.
- A small nonduplicative set of neutral SAR transforms, including VV/VH or VH/VV ratio, log ratio, and RVI.
- Core Sentinel-2 source bands or core indices as independent surface/confounder evidence.
- Canonical Landsat `lst` and, secondarily, a clearly named relative thermal-inertia feature.
- DEM elevation and terrain derivatives as confounder controls.
- Valid-pixel, acquisition, and alignment metrics as quality gates.

Duplicate algebraic variants must not be counted as separate independent evidence.

### Rejected now

- Classifier outputs and probabilities.
- PCA anomaly and target masks.
- `REPORT_640`, `TGT_*`, `ARCH_TARGETS_*`, `AI_BEH_*`, secret, and full AI tensor layers.
- `UGS_DeepStruct_RVI`, `UGS_BaseDeep`, and all simulated geophysical layers as physical depth evidence.
- Cell 214 `depth_file` until source provenance is recovered.
- Any existing or generated depth label.

## Relative-depth research decision

Broad relative-depth categories are technically worth testing **offline only** after a known-depth dataset exists.

Recommended first test:

- predict depth to the top of the reference feature;
- use three broad ordered classes;
- use a simple interpretable baseline;
- group validation by physical site;
- compare against majority-class and random baselines;
- report per-class confusion and abstention;
- block output when sensor coverage or calibration similarity is insufficient.

Without known-depth calibration, the current signals are not sufficient to justify even a user-facing `shallow-looking`, `medium-looking`, or `deep-looking` label.

## Phase 1 conclusion

The app has several measurable sensor inputs and many derived ratios, but no existing feature measures physical depth.

The strongest inventory candidates are raw SAR plus incidence angle, independent optical/thermal context, terrain controls, and quality metadata. The feature named `NANO_Depth_Penetration` is only a dimensionless radar ratio proxy.

Numerical depth in metres is not currently possible, and no implementation should begin until the calibration-data phase is explicitly approved.