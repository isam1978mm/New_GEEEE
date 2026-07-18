# Private Depth Calibration Dataset Card

Status: template only. Complete this file only in the private dataset folder outside Git.

## Dataset identity

```text
dataset_version:
schema_version: depth_calibration_dataset_v1
created_at:
owner_reference:
```

## Plain-English purpose

This dataset is intended to test whether approved satellite and terrain features can support broad relative-depth categories and, only later if validated, estimated depth ranges to the top of an independently measured or independently documented reference feature.

It is not proof that an underground feature exists, and it must not use app or notebook predictions as the true depth label.

## Storage boundary

```text
filesystem_only: true
http_servable: false
frontend_visible: false
downloadable_via_api: false
```

Private coordinates, source documents, site identifiers, feature rows, and model artifacts remain outside Git.

## Record summary

```text
total_records:
known_depth_positive_records:
confirmed_no_target_records:
uncertain_records:
excluded_records:
train_group_count:
validation_group_count:
holdout_group_count:
```

## Depth coverage

```text
minimum_known_depth_top_m:
maximum_known_depth_top_m:
reference_uncertainty_summary:
```

Do not fill these values until they are calculated from the populated private records.

## Supported conditions represented

Document the actual coverage for:

- finding families;
- target sizes and structures;
- soil or surface types;
- moisture and seasons;
- terrain classes;
- radar viewing geometry;
- sensor sources and acquisition periods;
- valid-pixel and data-quality conditions.

## Known limitations

Record missing depth bands, weak subgroups, unsupported conditions, uncertain references, and any site concentration or leakage risk.

## Split policy

Explain how physical sites, related features, and repeated dates are grouped so no related `group_id` crosses training, validation, or untouched holdout.

## Label provenance

Confirm that every included positive depth label comes from independent measurement or documentation and not from:

- notebook outputs;
- app classifier outputs;
- PCA or target-mask outputs;
- generated or guessed depth values;
- unknown-provenance arrays.

## Hashes and versions

```text
calibration_records_sha256:
source_index_sha256:
exclusions_sha256:
feature_manifest_version:
pipeline_commit:
split_policy_version:
```

## Readiness checklist

- [ ] Real private records have been entered.
- [ ] Every included positive has a traceable known depth to the top.
- [ ] Reference uncertainty is recorded.
- [ ] Confirmed no-target records are documented separately.
- [ ] Source references are indexed privately.
- [ ] Excluded records and reasons are retained.
- [ ] Physical groups are separated across splits.
- [ ] Feature inputs are frozen and non-circular.
- [ ] Counts, ranges, versions, and hashes are calculated.
- [ ] The dataset passes `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`.

Until every applicable item passes:

```text
dataset_status = not_ready
relative_depth_fitting = blocked
numerical_depth_fitting = blocked
```
