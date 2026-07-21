# Depth Public-Only Evidence Search Pass — 2026-07-21

Status: public online search continued without author contact, user survey work, or external field work. No calibration record was approved and app depth remains disabled.

This document supplements:

- `docs/DEPTH_PUBLIC_EVIDENCE_CANDIDATE_REGISTER_2026-07-18.md`
- `docs/DEPTH_ONLINE_EVIDENCE_ACQUISITION_UPDATE_2026-07-20.md`
- `docs/DEPTH_REMAINING_BLOCKERS_AND_UNBLOCKING_PLAN_2026-07-20.md`

## Search boundary

The search was restricted to material already public on official repositories, institutional pages, open journals, and government data portals.

No emails were sent. No source owner was contacted. The user is not required to perform surveys, research, review, or outreach.

## Current decision

```text
public_only_search_status = additional_sources_screened
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

The new sources improve the evidence map but still do not provide a complete calibration package with independent depth truth, depth-reference definition, numerical uncertainty, raw compatible sensor data, acquisition dates, multiple physical-site groups, and defensible negative records.

## Candidate P11 — National Buried Infrastructure Facility controlled utility pit

Primary public sources:

- University of Birmingham NBIF facility page
- Afrasiabi et al., *Optimising Ground Penetrating Radar data interpretation: A hybrid approach with AI-assisted Kalman Filter and Wavelet Transform for detecting and locating buried utilities*, Journal of Applied Geophysics 232 (2025), article 105567

Verified public facts:

- controlled concrete-lined test pit approximately 10 m by 5.8 m and 5 m deep;
- compacted-sand host material;
- a 2 m diameter HDPE pipe with reported cover depth of approximately 0.30 m;
- a simulated void with reported cover depth of approximately 0.17 m;
- additional buried pipes of different materials and sizes were used;
- GPR data were collected with commercial multi-frequency systems;
- no openly downloadable raw-data package, construction table, placement uncertainty, or complete target-to-profile map was found during this pass.

Current classification:

```text
physical_depth_provenance = controlled_installation
reference_definition = cover_depth_reported_for_subset
reference_uncertainty_m = not_reported
raw_public_dataset_confirmed = no
real_field_data = yes
benign_targets = yes
multiple_physical_sites = no_single_compact_site
sentinel_1_target_level_support = no
source_evidence_usable = yes_for_ground_method_truth
private_pack_import_approved = no
```

Reason not approved:

- incomplete public target table;
- no numerical uncertainty;
- no public raw package;
- one compact physical site;
- target scale is not defensible for individual Sentinel-1 calibration rows.

## Candidate P12 — Full-scale buried flexible-pipe field measurements

Public dataset:

- DOI `10.17632/g2ypdpsxck.1`
- Mendeley Data, *Soil Stress and Pipe Deflection in Buried Flexible Pipes*
- CC BY 4.0

Verified public facts:

- open spreadsheet dataset;
- 18 buried flexible pipes under controlled embankment conditions;
- two pipe materials: PVC and HDPE;
- six structural types;
- pipe inner diameters of 762, 1067, and 1524 mm;
- two reported burial depths: 6.1 m and 12.2 m;
- 293 measurement records;
- records include fill height above the pipe crown, pipe deflection, and soil stresses;
- the public package is an engineering instrumentation dataset rather than a geophysical or satellite observation package.

Current classification:

```text
physical_depth_provenance = controlled_full_scale_installation
reference_definition = burial_depth_and_fill_height_above_pipe_crown
reference_uncertainty_m = not_visible_in_public_metadata
raw_engineering_measurements = yes
raw_geophysical_or_satellite_measurements = no
exact_site_coordinates = not_visible_in_public_metadata
installation_and_acquisition_dates = not_visible_in_public_metadata
multiple_physical_sites = not_established
source_evidence_usable = yes_for_engineering_depth_context
private_pack_import_approved = no
```

Reason not approved:

- no matched approved sensor observations;
- no public spatial/acquisition mapping suitable for the current feature extractor;
- no numerical reference uncertainty found;
- independent physical-site grouping is not established.

## Candidate P13 — USGS Boulder Geophysical Test Site aeromagnetic survey

Public dataset:

- DOI `10.5066/P92MXMM5`
- U.S. Geological Survey raw and processed UAS aeromagnetic data
- public-domain/CC0-compatible government release

Verified public facts:

- four repeat aeromagnetic surveys acquired on 2019-09-25;
- survey area approximately 150 m by 150 m;
- central 100 m by 100 m area was the main focus;
- nominal flight heights of 25 m and 40 m;
- raw and processed magnetic data are openly available;
- the USGS describes the broader site as a geophysical test site used to calibrate and assess instruments;
- no public target construction map, independent target depths, or confirmed-negative map was found during this pass.

Current classification:

```text
raw_public_sensor_data = yes
sensor_type = UAS_aeromagnetic
acquisition_date = 2019-09-25
site_scale = 150_m_by_150_m
known_depth_target_table = not_found
reference_uncertainty_m = not_applicable_without_target_truth
source_evidence_usable = yes_for_sensor_repeatability_and_method_testing
private_pack_import_approved = no
```

Reason not approved:

The public release is strong sensor data but does not expose the independent buried-target truth needed for a known-depth calibration record.

## Candidate P14 — USDA multi-site agricultural drainage-pipe studies

Primary public sources:

- USDA Agricultural Research Service publication records on GPR detection of subsurface drainage pipes

Verified public facts:

- GPR was tested at eleven field plots in Ohio;
- plots covered different soil conditions;
- installed agricultural drainage pipes were detected to depths around 1 m;
- the literature represents multiple physical field plots rather than repeated profiles from one compact test site;
- no public raw GPR archive, exact pipe-depth table, installation map, uncertainty table, or acquisition package was found during this pass.

Current classification:

```text
multiple_physical_sites = yes_eleven_field_plots
known_installed_drainage = yes
approximate_depth_support = around_1_m
raw_public_dataset_confirmed = no
machine_readable_depth_table = not_found
reference_uncertainty_m = not_reported
source_evidence_usable = literature_only
private_pack_import_approved = no
```

Reason not approved:

The multi-site design is scientifically attractive, but the public material currently lacks the record-level data and provenance needed by the calibration contract.

## Existing candidate re-checks

### P7 — Morocco utilities, voids, and intact zones

Public dataset DOI `10.17632/ww7fd9t325.1` remains useful for detection and background-image method research because it includes 2,239 GPR images from multiple infrastructure projects and labels for utilities, voids, and intact zones.

No independent numerical depth table, construction truth, or confirmed-negative verification package was found. `intact_zone` labels therefore remain detection labels, not approved `confirmed_no_target` calibration truth.

### P6 — Hacimusalar multi-method dataset

Public dataset DOI `10.17632/27wsdn3mc2.1` provides raw and processed GPR, ERT, and magnetometry data under CC BY 4.0.

The reported approximately 1.2 m wall depth remains a geophysical interpretation. No independent excavation, engineering, or survey reference confirming depth to top was found. The source remains unsuitable as `known_depth_positive` truth.

## Rejected or method-only public results

The following types were screened out:

- synthetic GPR datasets: useful for software tests but prohibited as real calibration truth;
- soil-depth and stratigraphy datasets: depth labels do not represent the buried-object target required by this project;
- pipe engineering tables without matched geophysical or satellite observations: useful context but not trainable records;
- raw sensor datasets without independent target maps or depth references: useful for method testing only;
- papers that provide only interpreted depths from the same sensor response: not independent ground truth.

## Public-only search result

The strongest public packages now fall into separate incomplete categories:

```text
TU1208 = open raw GPR plus independently surveyed target geometry, but missing numerical uncertainty and satellite-scale support
Morocco = open multi-project GPR detection data, but missing independent numerical depth and confirmed-negative truth
Hacimusalar = open multi-method raw data, but depth remains interpreted rather than independently confirmed
Boulder USGS = open repeat aeromagnetic data, but missing public buried-target truth
Flexible-pipe field data = open controlled engineering depth records, but missing matched approved sensor observations
NBIF = controlled known cover depths, but no public raw package or uncertainty
USDA drainage plots = multiple physical sites, but no public record-level raw package
```

No source should be imported by combining missing fields from unrelated sources.

## Next public-only execution sequence

1. inspect open repository file listings for machine-readable construction tables hidden inside existing candidate archives;
2. search government and institutional data portals for large controlled civil-infrastructure sites with public as-built depth tables and acquisition dates;
3. search for independently verified pre-construction or empty-site datasets that can qualify as negatives;
4. screen any new source for physical-site independence and Sentinel-1 support before record construction;
5. keep simulated, interpreted-only, and detection-only datasets outside the calibration pack;
6. do not contact source owners unless the user explicitly changes the public-only boundary.

## Current checklist

- [x] Continue online research without user field work.
- [x] Keep author contact disabled.
- [x] Screen additional official and open-repository sources.
- [x] Add NBIF controlled-pit candidate.
- [x] Add full-scale flexible-pipe engineering candidate.
- [x] Add USGS Boulder open sensor-data candidate.
- [x] Add USDA multi-site drainage-pipe literature candidate.
- [x] Re-check Morocco and Hacimusalar against the independent-truth rule.
- [ ] Find a public package with record-level independent depth, uncertainty, and compatible sensor acquisition mapping.
- [ ] Find approved confirmed-negative records.
- [ ] Populate the private calibration pack only after the contract passes.
- [ ] Keep app depth disabled.
