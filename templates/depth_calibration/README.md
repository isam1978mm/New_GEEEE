# Private Depth Calibration Dataset Intake Scaffold

Status: empty repository-safe template pack only. It contains no real site, coordinate, source, or known-depth record.

## Plain-English purpose

Copy this entire folder into a private folder outside Git before entering any real records.

Recommended private location:

```text
C:\Dev\New_GEE_PRIVATE\DEPTH_CALIBRATION\dataset_v001\
```

The private folder remains local, outside Git, not HTTP-served, and not visible in the normal frontend.

## Copy the complete pack

Copy every file from:

```text
templates/depth_calibration\
```

into the private dataset folder.

The template pack contains:

```text
calibration_records.csv
calibration_manifest.json
feature_manifest.json
source_index.csv
exclusions.csv
DATASET_CARD.md
README.md
```

Do not enter real records into the repository copies.

## What each file does

- `calibration_records.csv`: one row per physical reference feature or confirmed no-target case.
- `calibration_manifest.json`: private dataset version, counts, split policy, hashes, and privacy settings.
- `feature_manifest.json`: exact approved feature names, units, formulas, order, preprocessing, and prohibited inputs.
- `source_index.csv`: private mapping from neutral source references to real documents or measurements.
- `exclusions.csv`: records rejected, deferred, or retained only for audit, with the reason.
- `DATASET_CARD.md`: plain-English dataset purpose, coverage, limitations, split policy, and readiness checklist.

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
3. Record a neutral source reference in `calibration_records.csv` and map it privately in `source_index.csv`.
4. Record target, soil, moisture or season, terrain, observation, and sensor details when available.
5. Keep related sites, features, and repeated dates under the same `group_id`.
6. Assign train, validation, and untouched holdout splits by physical group, not by individual row.
7. Mark uncertain or incomplete records as excluded rather than guessing missing values.
8. Calculate counts and hashes only after the private files are populated.

## Manifest rule

The repository manifest intentionally contains `null` values.

In the private copy, replace them only after the dataset is populated and checked. Do not invent record counts, versions, hashes, supported ranges, or readiness status in advance.

## Privacy boundary

The following remain only in the private dataset folder:

```text
real coordinates
real site names
source documents
private source paths
known-depth records
sensor feature rows
site-level splits
trained model files
site-level predictions
```

The repository may contain only empty templates, synthetic test fixtures, and redacted aggregate methodology.

## Private dataset checklist

- [x] Empty calibration-record CSV template exists.
- [x] Empty source-index template exists.
- [x] Empty exclusion-ledger template exists.
- [x] Calibration-manifest template exists.
- [x] Feature-manifest template exists.
- [x] Dataset-card template exists.
- [x] Private-folder location is defined.
- [x] First-record intake order is defined.
- [x] App-generated and guessed labels are prohibited.
- [ ] Copy the complete template folder into private storage.
- [ ] Enter the first independently measured or independently documented record.
- [ ] Enter confirmed no-target or background records.
- [ ] Add private source-index entries.
- [ ] Add exclusion-ledger entries for rejected or deferred records.
- [ ] Freeze the approved feature manifest.
- [ ] Assign group-separated train, validation, and holdout splits.
- [ ] Calculate counts and hashes.
- [ ] Complete the private dataset card.
- [ ] Validate the populated dataset against `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`.

## Current decision

```text
Repository intake pack: complete
Private dataset folder: not verified
Known-depth records: still absent
Dataset validation: blocked
Relative-depth fitting: blocked
Numerical-depth fitting: blocked
App depth output: not_available
```
