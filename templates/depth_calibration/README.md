# Private Depth Calibration Dataset Intake Scaffold

Status: empty repository-safe template only. It contains no real site, coordinate, source, or known-depth record.

## Plain-English purpose

Copy this template into a private folder outside Git before entering any real records.

Recommended private location:

```text
C:\Dev\New_GEE_PRIVATE\DEPTH_CALIBRATION\dataset_v001\
```

The folder remains local, private, outside Git, not HTTP-served, and not visible in the normal frontend.

## Start the private dataset pack

Copy:

```text
templates/depth_calibration/calibration_records.csv
```

into the private dataset folder, then add these private files beside it:

```text
calibration_manifest.json
feature_manifest.json
source_index.csv
exclusions.csv
DATASET_CARD.md
```

Do not enter real records into the repository copy.

## What one valid positive record means

One row represents one physical reference feature whose depth to the top is independently measured or independently documented.

The depth label must not come from:

- the notebook;
- the app classifier;
- classifier scores or classes;
- PCA outputs;
- target masks;
- generated depth labels;
- a visually guessed satellite result;
- an unknown-provenance depth array.

## First-record intake order

1. Assign neutral `record_id`, `site_id`, `feature_id`, and `group_id` values that do not contain coordinates.
2. Record `known_depth_top_m`, the reference uncertainty, and how the depth was established.
3. Record a private source reference in the private dataset pack.
4. Record target, soil, moisture or season, terrain, observation, and sensor details when available.
5. Set the split by physical group so related sites, features, and dates cannot leak across train, validation, and holdout.
6. Mark uncertain or incomplete records as excluded rather than guessing missing values.

## Minimum private manifest

`calibration_manifest.json` should eventually identify:

```text
schema_version
dataset_version
created_at
record_count
included_relative_count
included_numerical_count
excluded_count
split_policy_version
feature_manifest_version
records_sha256
source_index_sha256
exclusions_sha256
```

The manifest counts and hashes must be calculated from the populated private files. Do not invent them in advance.

## Source index

`source_index.csv` should privately map the neutral source reference used in `calibration_records.csv` to the real document or measurement source.

Suggested header:

```text
source_reference,source_type,source_version,private_location,review_status,review_notes
```

The real source location remains outside Git.

## Exclusion ledger

`exclusions.csv` should record every rejected or deferred record.

Suggested header:

```text
record_id,site_id,feature_id,exclusion_reason,decision_date,reviewer_reference,notes
```

Do not silently delete weak records. Keep the reason they were not used.

## Private dataset checklist

- [x] Empty CSV schema template exists in Git.
- [x] Private-folder location is defined.
- [x] Required private pack files are listed.
- [x] First-record intake order is defined.
- [x] App-generated and guessed labels are prohibited.
- [ ] Copy the template into the private folder.
- [ ] Enter the first independently measured or independently documented record.
- [ ] Enter confirmed no-target or background records.
- [ ] Create the private source index.
- [ ] Create the private exclusion ledger.
- [ ] Assign group-separated train, validation, and holdout splits.
- [ ] Calculate counts and hashes.
- [ ] Validate the populated dataset against `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`.

## Current decision

```text
Repository intake scaffold: ready
Private dataset folder: not verified
Known-depth records: still absent
Dataset validation: blocked
Relative-depth fitting: blocked
Numerical-depth fitting: blocked
App depth output: not_available
```
