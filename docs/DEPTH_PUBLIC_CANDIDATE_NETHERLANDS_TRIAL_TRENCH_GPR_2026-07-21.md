# Public Candidate Qualification — Netherlands Trial-Trench GPR Dataset — 2026-07-21

Status: high-priority public extraction candidate. No record is approved for the private calibration pack and app depth remains disabled.

## Source

- Dataset: *Ground Penetrating Radar dataset with ground-truth data of utility surveying activities*
- Dataset DOI: `10.4121/96303227-5886-41c9-8607-70fdd2cfe7c1.v1`
- Data article DOI: `10.1016/j.dib.2024.110329`
- Repository: 4TU.ResearchData
- Dataset licence: CC0
- Article licence: CC BY 4.0

## Why this candidate is stronger

The public package combines real-world raw GPR with physical trial-trench verification across multiple construction projects:

```text
construction_project_count = 13
surveying_activity_count = 125
raw_radargram_count = 959
raw_radar_format = SEG-Y
radar_frequency_mhz = 500
ground_truth_method = excavated_trial_trenches
project_period = 2020-04_to_2021-03
```

The package publicly lists:

- thirteen project ZIP archives;
- `Metadata.csv`;
- `Codebook.pdf`;
- `Readme.txt`;
- raw radargrams;
- per-activity survey maps;
- per-activity trial-trench cross-sections or exposed-utility images.

## Independent positive truth

Trial trenches were excavated by the construction organisations. Utility locations were then measured using either:

- tape measures and water levels, recording relative utility location and depth; or
- GNSS measurements recording x, y, and z coordinates.

This is independent physical verification rather than a depth label interpreted only from the GPR response.

The utility set covers water, electricity, oil/gas/chemicals, sewage, and telecommunications, with reported diameters from 16 mm to 1326 mm.

## Potential negative truth

The stated trial-trench objectives included pinpointing free, unoccupied subsoil areas as well as verifying utilities.

This is the strongest public negative lead found so far because the absence of a utility may be physically checked by excavation rather than assumed from a quiet radar response.

However, no `confirmed_no_target` record is approved yet. Each candidate negative must be linked to:

1. an excavated free-subsoil trial trench;
2. the corresponding GPR survey activity;
3. a defensible surveyed area or line segment;
4. the project/site group;
5. evidence that the record is not merely an undocumented empty-looking radargram.

## Public file inventory

The repository exposes sixteen files totalling approximately 402.6 MB uncompressed:

```text
01.zip through 013.zip
Metadata.csv
Codebook.pdf
Readme.txt
```

The thirteen ZIP files correspond to the thirteen construction projects.

## Important limitations

### Numerical depths are not yet machine-readably confirmed

The published metadata description says the CSV records whether utility depth was known. It does not establish that `Metadata.csv` contains each numerical measured depth.

Measured depths may instead appear in the per-activity trial-trench cross-section images. Archive-level extraction is therefore required before constructing records.

### Ground-truth georeferencing is withheld

The trial-trench CAD files and ground-truth georeferencing were omitted for confidentiality. Radargrams are generally georeferenced, although some survey-line mappings are inaccurate or missing where buildings obstructed GNSS.

A record may be used only if the public survey map and cross-section permit an honest activity-level or line-level match without reconstructing withheld private locations.

### Measurement uncertainty is not published as a numerical field

The source describes analogue and GNSS measurement methods but no public numerical uncertainty value has been verified.

No uncertainty may be invented. Records must either retain a source-supported method-specific uncertainty policy approved by the dataset contract or remain ineligible.

### Leakage control

The unit for splitting is the construction project, not the radargram or surveying activity. All activities and radargrams from one project must remain in the same train, validation, or holdout split.

## Current classification

```text
candidate_id = P15
physical_depth_provenance = excavated_trial_trench_measurement
reference_definition = relative_utility_depth_or_GNSS_xyz_pending_per_record_extraction
reference_uncertainty_m = not_reported
real_field_data = yes
raw_public_sensor_data = yes
raw_sensor_format = SEG-Y
multiple_physical_sites = yes_13_construction_projects
positive_truth_available = yes_pending_record_extraction
potential_confirmed_negatives = yes_free_unoccupied_trial_trenches_pending_mapping
machine_readable_numeric_depth_table = not_confirmed
ground_truth_georeferencing_public = no_confidentiality_omission
radargram_georeferencing = generally_yes_with_some_missing_or_inaccurate_maps
source_evidence_usable = yes
method_research_usable = yes
private_pack_import_approved = no_pending_archive_extraction_uncertainty_and_mapping
priority = highest_public_only_candidate
app_depth_enabled = false
```

## Extraction gates

Before any record can enter the private pack:

1. enumerate all project ZIP contents;
2. identify activities with trial-trench cross-sections containing numerical depths;
3. distinguish utility-positive trenches from physically verified free-subsoil trenches;
4. map each retained ground-truth image to the corresponding radargrams and survey map;
5. record target discipline, material, diameter, depth reference, and measurement method;
6. exclude activities with no defensible ground-truth-to-radargram mapping;
7. assign one stable group ID per construction project;
8. define or reject a source-supported uncertainty policy;
9. run the approved sensor and scale compatibility screen;
10. keep detailed locations and withheld geometry out of Git and public output.

## Current decision

```text
public_candidate_search = advanced
best_public_positive_candidate = Netherlands_trial_trench_GPR
best_public_negative_lead = excavated_free_subsoil_activities_in_same_dataset
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
training_started = false
app_depth_enabled = false
```

This dataset materially improves the path to a calibration pack, but archive extraction and contract validation are still required before training.
