# Depth Public Source Eligibility Matrix — 2026-07-21

Status: public evidence consolidated; no calibration record approved and app depth remains disabled.

This matrix consolidates the public-only search into one decision table. It is a source-screening artifact, not a calibration dataset. It contains no private coordinates, feature values, or source-document paths.

## Decision meanings

```text
ground_method_truth = useful for GPR, excavation, engineering, or method validation
context_only = useful for confounder, construction-date, geometry, or provenance research
relative_depth_candidate = may become eligible only if all missing contract fields are recovered publicly
sentinel_1_calibration = directly eligible for the app's Sentinel-1 depth research
```

## Matrix

| ID | Public source | Independent physical depth | Depth-to-top definition | Numerical uncertainty | Public raw or machine-readable data | Independent physical-site groups | Confirmed negative/background | Sentinel-1 scale/support | Current use | Direct private-pack import |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | TU1208 / IFSTTAR Nantes | Yes, surveyed placement | Yes for verified subset | Missing | Yes, raw GPR | One compact site | Same-site background only | No target-level support | Ground-method truth | No |
| P2 | IAG/USP controlled site | Yes, installed and surveyed | Yes | Missing | Target table public; raw package not found | One compact site | Pre-installation ground data | No target-level support | Ground-method truth | No |
| P3 | TAMUCC test site | Yes, installed known geometry | Partially resolved | Missing | Public paper; complete table/raw package not found | One 50×50 m site | Pre-installation survey | Whole-site exploratory screen only | Site-level change research | No |
| P4 | Ahmadu Bello test site | Yes, installed targets | Yes, eight depth-to-top values | Missing | Table public; raw files not public | One 55×55 m site | Pre-burial ground investigation | Whole-site scale only | Ground-method truth | No |
| P5 | Guangzhou GPR dataset | Not visible in public package | Not established | Missing | Yes, raw GPR | Several field contexts, grouping incomplete | Not established | No | Method research | No |
| P6 | Hacimusalar multi-method survey | Interpreted, not independently confirmed | Approximate interpreted depth | Missing | Yes | One site | Not established | No | Cross-method context | No |
| P7 | Morocco utilities and voids | Detection labels only | No independent numerical depth | Missing | Yes, image dataset | Multiple sites | Intact-zone labels, not contract-confirmed negatives | No | Detection benchmark | No |
| P8 | MERL-GPR | Simulated | Exact simulation geometry | Simulation-defined | Yes | Simulated scenes only | Simulated | No real-field support | Software testing | No |
| P9 | Sense-City | Installed known geometry | Unresolved top versus axis | Missing | Raw archive not found | One compact site | Same-site no-pipe trench only | No target-level support | Ground-method truth | No |
| P10 | Teoloyucan test site | Constructed known geometry | Complete table required | Missing | Public paper; raw data not public | One 24×36 m site | Pre-construction characterization | Whole-site screen only | Ground-method research | No |
| P11 | Netherlands trial-trench dataset | Yes, excavation verified | Measurements appear in activity ground-truth material | Published machine-readable uncertainty not found | Yes, 959 radargrams across 13 projects | Yes, project groups | Excavated free-subsoil areas | Utilities too small for target-level Sentinel-1 | Strong GPR ground truth | No |
| P12 | OpenTrench3D | Yes, utilities physically exposed | Geometry visible in open trenches | Not established | Yes, 310 point clouds across seven areas | Yes | Open-trench non-utility areas only | Buried-state Sentinel-1 linkage absent | Geometry and segmentation research | No |
| P13 | Taipei/public sewer schemas | Yes, engineering cover/elevation fields | Yes for pipe top or soil cover in some schemas | Missing | Yes, public GIS/table data | Many network sections | Not established | Individual pipes are sub-resolution | Engineering context | No |
| P14 | Connecticut UST registry | Registered installed assets | No site-specific burial depth | Missing | Yes, public API with dates, capacity, material and coordinates | Many facilities | Not established | Facility disturbance possible; depth unsupported | Construction-date context | No |
| P15 | Public large-tunnel projects | Project engineering depth ranges | Surface-to-tunnel-top reported for some projects | Survey uncertainty not recovered | Public project records; exact segment table not recovered | Several independent projects | Pre-construction period may exist but is not a confirmed negative by itself | Structures are satellite scale, but depth domain is 10–40 m | Large-area construction context | No |
| P16 | 2026 purpose-built tunnel GPR dataset | Yes, three tunnels at 1.5–3 m | Reported tunnel depth; exact reference/uncertainty still needs package review | Not recovered | Public dataset and code referenced | One physical site | Same-site anomaly-free ground | No Sentinel-1 linkage or demonstrated scale | GPR method research | No |
| P17 | Public landfill inventories | Engineering capacity/volume and dates | No cell-level depth-to-top | Missing | Yes, public boundaries and tables | Many sites | No confirmed empty cell holdout | Yes, site scale; depth label missing | Large-area context | No |

## Why every row remains blocked for calibration

A source can be valuable without being calibration-ready. The current blockers fall into five recurring categories:

```text
B1 = missing numerical depth-reference uncertainty
B2 = missing or ambiguous depth-to-top definition
B3 = no reliable Sentinel-1-scale sensor linkage
B4 = no independently confirmed negative/background site
B5 = insufficient independent site groups for train/validation/holdout
```

| Source IDs | Main blockers |
|---|---|
| P1, P2, P4 | B1, B3, B5 |
| P3, P10 | B1, B2 or incomplete table, B4, B5 |
| P5, P6, P7 | B1, B2, B3, B4 |
| P8 | simulated data cannot replace real scientific calibration |
| P9 | B1, B2, B3, B4, B5 |
| P11 | B1, B3; negatives need contract-level review |
| P12 | B1, B2, B3, B4 |
| P13 | B1, B3, B4 |
| P14 | B1, B2, B3, B4 |
| P15 | B1, exact segment depth table missing, shallow-domain mismatch, B4 |
| P16 | B1, B3, B5 |
| P17 | B1, B2, B4 |

## Allowed use by source class

### Ground-method validation

Allowed candidates:

```text
P1 P2 P4 P5 P9 P10 P11 P12 P16
```

These sources may support GPR, excavation, geometry, or method research. Their labels must not be copied into the Sentinel-1 calibration pack without a separate scale and sensor-linkage decision.

### Public engineering and confounder context

Allowed candidates:

```text
P13 P14 P15 P17
```

These sources may support construction-date screening, surface-disturbance analysis, asset context, and confounder research. They do not provide current app depth truth.

### Detection-only or interpreted evidence

Restricted candidates:

```text
P6 P7
```

These may be used only for clearly separated exploratory detection or cross-method work. They cannot be labelled as known-depth positives.

### Software-only testing

Restricted candidate:

```text
P8
```

Simulated data may test file handling, algorithms, and synthetic failure cases. It cannot count toward scientific validation.

## Calibration readiness totals

```text
screened_public_source_classes = 17
public_sources_with_some_independent_physical_depth = 11
public_sources_with_some_raw_or_machine_readable_data = 13
public_sources_with_multiple_site_or_project_groups = 6
public_sources_directly_eligible_for_sentinel_1_calibration = 0
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
```

The counts above describe source classes, not independent calibration rows.

## Enforcement rule

No source in this matrix may enter `calibration_records.csv` unless a later source-specific review demonstrates all required contract fields, including:

```text
known_depth_top_m
depth_reference_uncertainty_m
depth_reference_method
evidence_source_reference
site_id
feature_id
group_id
observation dates
sensor acquisition linkage
scale/support assessment
split eligibility
```

Records that remain useful but ineligible must stay in a source register or exclusion ledger rather than being silently discarded or promoted to training truth.

## Current decision

```text
public_source_matrix_status = complete_for_current_search_pass
calibration_dataset_status = not_populated
relative_depth_baseline_status = not_fitted
numerical_depth_status = not_available
app_depth_enabled = false
```
