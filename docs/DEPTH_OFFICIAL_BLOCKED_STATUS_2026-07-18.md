# Official Depth Blocked Status — 2026-07-18

## Status

The depth-estimation work is officially blocked at the private calibration-data stage.

This is not a software failure. The repository-side planning, templates, initialization tooling, structural validator, manifest finalizer, privacy guards, split-leakage checks, feature-manifest checks, and targeted synthetic tests are complete for the current stage.

The project cannot honestly proceed to relative-depth fitting, numerical-depth fitting, backend implementation, frontend implementation, or depth activation until real private calibration records exist and pass validation.

## Plain-English explanation

The software is ready to receive and check calibration records, but the private dataset contains zero records.

The required records cannot be generated from the notebook, classifier, PCA outputs, target masks, satellite visual guesses, or depth-named signal proxies. They must come from independently measured or independently documented reference cases.

Because those records are absent, there is nothing valid to train or test a depth method against.

## Verified owner-computer execution

The owner ran the following command from `C:\Dev\New_GEE`:

```powershell
python .\scripts\init_depth_calibration_pack.py
```

Observed result:

```text
status = empty_private_pack_initialized
file_count = 7
real_records_written = false
depth_model_started = false
destination_outside_repository = true
```

The following files were created in the private pack:

```text
calibration_records.csv
calibration_manifest.json
feature_manifest.json
source_index.csv
exclusions.csv
DATASET_CARD.md
README.md
```

The owner then ran:

```powershell
python .\scripts\validate_depth_calibration_pack.py
```

Observed result:

```text
status = validation_failed
readiness_decision = not_ready_no_records
record_count = 0
positive_count = 0
negative_count = 0
included_relative_count = 0
included_numerical_count = 0
training_started = false
scientific_validation_run = false
app_depth_enabled = false
```

The owner also tested the manifest finalizer in preview and write modes:

```powershell
python .\scripts\finalize_depth_calibration_manifest.py `
  --dataset-id "depth-calibration-v001" `
  --dataset-version "v001"

python .\scripts\finalize_depth_calibration_manifest.py `
  --dataset-id "depth-calibration-v001" `
  --dataset-version "v001" `
  --write
```

Both commands correctly refused to finalize the empty dataset:

```text
status = manifest_finalize_failed
error = private pack has contract issues: {"no_records": 1}
```

A final validation again returned `not_ready_no_records`, confirming that no false manifest state was written.

## Exact blocker

```text
known_depth_records = absent
confirmed_background_records = absent
private_source_index_entries = absent
approved_frozen_feature_manifest = absent
train_validation_holdout_groups = absent
calibration_dataset_status = not_ready_no_records
relative_depth_fitting = blocked
numerical_depth_fitting = blocked
backend_depth_implementation = blocked
frontend_depth_implementation = blocked
depth_activation = not_approved
app_depth_output = not_available
```

## Completed work

### Planning

- [x] Define depth as depth to the top of the independently documented reference feature.
- [x] Inventory current depth-related signals and separate proxies from measurements.
- [x] Define the calibration dataset contract.
- [x] Define the relative-depth baseline method.
- [x] Define numerical depth-range research rules.
- [x] Define confounder controls.
- [x] Define backend architecture.
- [x] Define easy-English presentation.
- [x] Define validation gates.
- [x] Define rollout and completion order.

### Repository implementation

- [x] Create the empty calibration-record template.
- [x] Create the calibration-manifest template.
- [x] Create the feature-manifest template.
- [x] Create the private source-index template.
- [x] Create the exclusion-ledger template.
- [x] Create the dataset-card template.
- [x] Implement the safe private-pack initializer.
- [x] Implement the aggregate-only validator.
- [x] Implement the manifest count-and-hash finalizer.
- [x] Reject repository-local private dataset paths.
- [x] Reject empty datasets.
- [x] Reject split leakage.
- [x] Reject incomplete or prohibited feature definitions.
- [x] Reject missing or mismatched manifest integrity fields.
- [x] Preserve private rows, coordinates, source paths, depth values, and feature values from normal output.

### Testing

- [x] Targeted synthetic calibration-tooling tests passed.
- [x] Empty dataset refusal was verified on the owner computer.
- [x] Manifest preview refusal was verified on the owner computer.
- [x] Manifest write refusal was verified on the owner computer.
- [x] No model training started.
- [x] No depth output was enabled.

## Work that must not start while blocked

Do not begin any of the following merely to bypass the missing data:

- fitting shallow, medium, or deep categories;
- choosing category boundaries in metres;
- fitting a numerical depth model;
- converting `NANO_Depth_Penetration` or another radar ratio into metres;
- using classifier scores, classes, probabilities, PCA decisions, target masks, or generated labels as depth truth;
- implementing an app stage that produces apparent depth values without an approved model package;
- adding a frontend depth result that implies the capability exists;
- inventing records, counts, versions, hashes, uncertainty, supported ranges, or scientific metrics.

## Only permitted unblocking work

The next permitted work is private dataset population and review outside Git.

Required actions:

1. Enter independently measured or independently documented known-depth-to-top records.
2. Enter independently confirmed no-target or background records.
3. Add neutral source references to `calibration_records.csv` and map them privately in `source_index.csv`.
4. Record reference uncertainty and the method used to establish each depth.
5. Record available finding-family, target-size, material or structure, soil, moisture or season, terrain, observation, and sensor information.
6. Freeze the approved non-circular feature manifest.
7. Assign related physical sites, features, and repeated observations to one `group_id`.
8. Separate groups into `train`, `validation`, and untouched `holdout` splits.
9. Run the aggregate validator and resolve every issue.
10. Run the manifest finalizer in preview mode, then with `--write`.
11. Run the validator again.
12. Begin relative-depth research only if the final private dataset passes the contract.

## Unblocking condition

The block may be removed only when the private dataset has real records and the validator returns:

```text
status = validation_passed
readiness_decision = ready_for_relative_depth_research
```

This result will mean only that the dataset contract passed. It will not mean that depth estimation is scientifically validated or approved for the app.

## Official decision

```text
official_depth_status = blocked_missing_private_calibration_records
block_type = required_external_private_data
software_bug = false
repository_setup = complete_for_current_stage
private_pack_initialized = true
private_pack_record_count = 0
relative_depth_release = not_approved
numerical_depth_release = not_approved
current_app_depth_output = not_available
```

Planning completion is not product completion. The project remains blocked until the required private reference evidence is supplied and validated.
