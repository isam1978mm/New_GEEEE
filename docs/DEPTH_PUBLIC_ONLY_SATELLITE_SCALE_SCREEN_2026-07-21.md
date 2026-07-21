# Depth Public-Only Satellite-Scale Screening — 2026-07-21

Status: public-only evidence screening continued. No people were contacted, no private survey was requested, no calibration row was approved, and app depth remains disabled.

## Current decision

```text
public_only_search = continued
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

## Scientific screening rule

For this project, a source is not sufficient merely because it reports a buried feature and uses Sentinel-1. A usable calibration source must provide:

1. independently documented physical depth;
2. an explicit depth reference such as depth to target top;
3. a defensible uncertainty value or policy;
4. a physical scale compatible with the Sentinel-1 analysis unit;
5. enough site-level separation to avoid treating nearby targets as independent sites;
6. matched acquisition dates and a stable feature contract;
7. confirmed negative or background evidence that is independent of the same unknown signal.

## Candidate S1-P1 — Qubbet el-Hawa Sentinel-1 archaeology study

Source:

- arXiv `2101.11170`

Verified facts:

- the study uses Sentinel-1 and Sentinel-2 at an archaeological site in Egypt;
- it reports sensitivity mainly to exposed structures, excavation disturbance, surface texture, and very shallow dry-sand effects;
- the paper states that buried structures much deeper than roughly 5 cm are not expected to be directly delineated by Sentinel-1 C-band;
- the work does not publish an independently measured target-depth calibration table, uncertainty values, or a reusable matched feature dataset.

Classification:

```text
sentinel_1_used = yes
independent_numerical_depth_table = no
published_penetration_boundary = very_shallow_surface_response
source_evidence_usable = yes_for_surface_disturbance_monitoring
relative_depth_calibration_usable = no
private_pack_import_approved = no
```

## Candidate S1-P2 — Buto integrated Sentinel-1, ERT, and excavation study

Source:

- DOI `10.1007/s11600-026-01809-4`

Verified facts:

- the open study uses one Sentinel-1 GRD acquisition dated 2018-05-05;
- Sentinel-1 processing was multilooked to approximately 20 m resolution;
- the reported Sentinel-1 anomaly is approximately 128 m by 62 m;
- ERT and excavation identify archaeological structures at approximately 3 to 3.5 m below the local surface, with deeper ERT anomalies extending toward 6 m;
- the article contains an internally inconsistent depth argument: it reports excavation reaching elements at 3 m, then uses differing elevation references to state that remains started at 6 m, followed by a claim of about 2 m Sentinel-1 penetration;
- the same discussion cites approximate C-band penetration limits of about 5 cm in clay and 50 cm in dry sand;
- no reusable code or source dataset is released in the article's data-availability statement;
- the study uses Sentinel-1 primarily as a large-scale anomaly guide, followed by ERT and excavation for subsurface interpretation.

Classification:

```text
sentinel_1_used = yes
large_site_anomaly = yes
excavation_ground_truth = yes
exact_sentinel_1_depth_relationship = not_demonstrated
published_depth_reasoning_consistent = no
reusable_dataset = no
source_evidence_usable = yes_as_detection_claim_requiring_replication
relative_depth_calibration_usable = no
private_pack_import_approved = no
```

Use boundary:

The Buto study must not be converted into a numerical Sentinel-1 depth row. It may be cited as a large-area integrated remote-sensing case, but the satellite signal cannot be separated from surface topography, soil texture, stratigraphy, moisture, and other site-scale effects using the released material.

## Candidate GPR-P11 — Purpose-built known-depth tunnel field study

Source:

- arXiv `2607.04882`

Verified public facts:

- a purpose-built field site contains three tunnels reported at depths from 1.5 m to 3 m;
- the evaluation covers 55 GPR survey lines and 1,600 test windows;
- training uses normal GPR radargrams and the study evaluates tunnel detection using depth-restricted anomaly scoring;
- the public preprint does not provide a matched Sentinel-1 calibration package;
- no open raw dataset or independent numerical placement-uncertainty package was found during this pass.

Classification:

```text
known_depth_field_targets = yes
sensor = ground_penetrating_radar
sentinel_1_included = no
raw_public_dataset_confirmed = no
method_research_usable = promising
sentinel_1_depth_calibration_usable = no
private_pack_import_approved = no
```

## Candidate GPR-P12 — 2026 low-frequency ground and UAV GPR release

Source:

- Zenodo `18769571`

Verified public facts:

- the dataset contains low-frequency GPR acquired using ground-based and UAV platforms;
- three sites are included in the first release;
- GeoTable and SEG-Y formats are provided with acquisition metadata;
- the release reports an approximate investigation depth of 7.5 m depending on local conditions;
- the public description does not establish independently installed target depths, target-top references, confirmed negatives, or reference uncertainty for calibration.

Classification:

```text
raw_public_gpr = yes
multiple_sites = yes_three
independent_known_target_depths = not_confirmed
confirmed_negatives = not_confirmed
sentinel_1_included = no
method_research_usable = yes
relative_depth_calibration_usable = no_current_evidence
private_pack_import_approved = no
```

## Candidate GEO-P1 — Open seismic tunnel and underground-tube dataset

Source:

- open paper and dataset described in `Near-Surface Seismic Measurements in Gravel Pit, over Highway Tunnel and Underground Tubes with Ground Truth Information as an Open Data Set`

Verified public facts:

- the open dataset includes measurements above a highway tunnel and underground tubes;
- approximate tunnel depth and near-surface tube depths are documented as ground truth;
- the source is valuable for validating seismic inversion and ground-method workflows;
- it is not a Sentinel-1 backscatter calibration dataset and does not establish transferability to the app's VV/VH feature family.

Classification:

```text
independent_ground_truth = yes_approximate
open_ground_sensor_data = yes
sentinel_1_included = no
method_research_usable = yes
sentinel_1_depth_calibration_usable = no
private_pack_import_approved = no
```

## Mining and deformation sources

Public Sentinel-1 mining studies and datasets were also screened. They can measure surface displacement caused by underground activity using InSAR. They are not usable for this app's backscatter depth calibration because:

1. their measured quantity is surface deformation, not direct depth response;
2. the causal structures are often hundreds of metres deep;
3. the feature family is interferometric phase/displacement rather than the current neutral VV/VH backscatter statistics;
4. transfer to compact buried objects would be scientifically unsupported.

Classification:

```text
sentinel_1_available = yes
known_underground_activity = sometimes
measurement_mode = InSAR_surface_deformation
direct_backscatter_depth_calibration = no
domain_transfer_to_compact_targets = prohibited_without_new_evidence
```

## Result of this search pass

The search found:

- stronger public examples of Sentinel-1-guided subsurface investigation;
- open ground-sensor datasets with known or approximate depth;
- large mining datasets with Sentinel-1 deformation measurements;
- no public source that links the app's Sentinel-1 VV/VH backscatter features to independently measured buried-object depth across multiple physical sites.

The current boundary therefore remains:

```text
current_site_status = unexplained_radar_anomaly_research_case
relative_depth = blocked_missing_compatible_known_depth_calibration_sites
numerical_depth = blocked_missing_model_and holdout_validation
confidence_percentage = not_available
app_depth_enabled = false
```

## Next public-only work

1. continue searching for large benign engineered subsurface sites with published as-built depths and public acquisition dates;
2. prioritize public before/after construction cases whose affected area is large enough for independent Sentinel-1 windows;
3. inspect open archives for machine-readable construction tables, numerical uncertainty, and site-level grouping;
4. retain GPR, seismic, ERT, and InSAR datasets for method validation only unless a source-backed transfer contract is established;
5. do not contact authors, request private surveys, or ask the user to perform research.
