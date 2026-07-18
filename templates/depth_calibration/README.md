# Private Depth Calibration Dataset Intake Scaffold

Status: empty repository-safe template pack only. It contains no real site, coordinate, source, or known-depth record.

## Plain-English purpose

Copy this entire folder into a private folder outside Git before entering any real records.

Recommended private location:

```text
C:\Dev\New_GEE_PRIVATE\DEPTH_CALIBRATION\dataset_v001\
```

The private folder remains local, outside Git, not HTTP-served, and not visible in the normal frontend.

## Safe initialization command

From the repository root, run:

```powershell
python .\scripts\init_depth_calibration_pack.py
```

The command:

- copies all empty template files to the default private folder;
- refuses to write inside the repository;
- refuses to overwrite a non-empty destination;
- writes no records, coordinates, depths, or model files.

To use another private folder:

```powershell
python .\scripts\init_depth_calibration_pack.py --destination "C:\private\depth_dataset_v001"
```

## Validate the private pack

After adding or editing private records, run:

```powershell
python .\scripts\validate_depth_calibration_pack.py
```

Or specify another private folder:

```powershell
python .\scripts\validate_depth_calibration_pack.py --dataset-dir "C:\private\depth_dataset_v001"
```

The validator prints aggregate counts and issue codes only. It does not print rows, IDs, coordinates, source paths, depth values, or feature values.

Validation checks include:

- required files and columns;
- valid statuses, split names, and label-quality values;
- positive depth and uncertainty rules;
- no depth values on confirmed negative rows;
- source-index linkage;
- duplicate record or source identifiers;
- site, feature, and group leakage across splits;
- frozen feature-manifest requirements;
- prohibited classifier, PCA, target-mask, and generated-label inputs;
- manifest privacy flags, counts, and optional hashes.

A successful dataset-contract check does not prove that depth estimation works. Scientific holdout validation remains a later phase.

## Calculate manifest counts and hashes

After the private rows pass the structural checks, preview the derived manifest values:

```powershell
python .\scripts\finalize_depth_calibration_manifest.py `
  --dataset-id "depth-calibration-v001" `
  --dataset-version "v001"
```

The preview does not write anything.

To update only the private `calibration_manifest.json` file:

```powershell
python .\scripts\finalize_depth_calibration_manifest.py `
  --dataset-id "depth-calibration-v001" `
  --dataset-version "v001" `
  --write
```

The finalizer calculates aggregate counts, split totals, depth-range summaries, file hashes, the combined content hash, and the manifest hash. It does not print private rows or start model work.

Run the validator again after finalization:

```powershell
python .\scripts\validate_depth_calibration_pack.py
```

## Template pack contents

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
- `calibration_manifest.json`: dataset version, counts, split policy, hashes, privacy settings, and limitations.
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

The repository may contain only empty templates, synthetic test fixtures, tooling, and redacted aggregate methodology.

## Checklist

- [x] Empty calibration-record CSV template exists.
- [x] Empty source-index template exists.
- [x] Empty exclusion-ledger template exists.
- [x] Full calibration-manifest template exists.
- [x] Feature-manifest template exists.
- [x] Dataset-card template exists.
- [x] Safe private-pack initializer exists.
- [x] Aggregate-only validator exists.
- [x] Manifest count-and-hash finalizer exists.
- [x] Synthetic tests cover initialization, empty state, valid data, leakage, repository-path rejection, dry-run finalization, and manifest writing.
- [ ] Run the initializer on the owner computer.
- [ ] Enter the first independently measured or independently documented record.
- [ ] Enter confirmed no-target or background records.
- [ ] Add private source-index entries.
- [ ] Add exclusion-ledger entries for rejected or deferred records.
- [ ] Freeze the approved feature manifest.
- [ ] Assign group-separated train, validation, and holdout splits.
- [ ] Run the aggregate validator.
- [ ] Run the manifest finalizer in dry-run mode.
- [ ] Write the private manifest counts and hashes.
- [ ] Complete the private dataset card.
- [ ] Run the aggregate validator again.
- [ ] Validate the populated dataset against `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`.

## Current decision

```text
Repository intake pack: complete
Private-pack initializer: implemented
Aggregate validator: implemented
Manifest finalizer: implemented
Private dataset folder: not verified
Known-depth records: still absent
Dataset scientific validation: blocked
Relative-depth fitting: blocked
Numerical-depth fitting: blocked
App depth output: not_available
```
