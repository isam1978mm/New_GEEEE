# D1D object-table verifier result

Status: passed.

This document records the safe docs-only result for D1D object-table real app-vs-reference parity.

No CSV rows, object patches, masks, raster/NPY payloads, coordinate-bearing values, verifier report payloads, or private reference files are included in this document.

## Scope

D1D covers the notebook object-table outputs:

```text
objects_index.csv
clusters_summary.csv
```

The D1C bundle did not contain these files and did not mention them in `reference_manifest.json`. The matching private reference was found in the D1 reference root:

```text
D1_NEW_IPYNB_REFERENCE_2026_06_10
```

Notebook phase evidence associates these outputs with the object-extraction/object-classification family:

```text
Cell 68: PCA CANDIDATE LABELS TO OBJECT TABLE emits objects_index.csv
Cell 69: AI OBJECT CLASSIFY + CLUSTER SUMMARY writes classified CSV + cluster summary
Cell 71: AUTO OBJECT EXTRACTION FROM SCIENTIFIC HYPERCUBE writes proposals, binary mask, labels, object index, and per-object NPY patches
```

## Matching app run

The matching app run is:

```text
e11d3280-a7b7-4c7c-a761-8b08ac9452f2
```

The app run `a11309bf-ed47-4bf5-bbf4-f755b904065c` also contains object-table outputs, but it is not the D1D parity match for these reference files.

## Safe comparison result

```text
overall_status: passed
reference_root_name: D1_NEW_IPYNB_REFERENCE_2026_06_10
app_run: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
expected_count: 2
passed_count: 2
```

### objects_index.csv

```text
reference_exists: true
app_exists: true
reference_length: 43626
app_length: 43626
reference_sha256: AF571804AC6087E0CC1C5A2B173E75CF1765C4DB35C5A223890E9CB889458235
app_sha256: AF571804AC6087E0CC1C5A2B173E75CF1765C4DB35C5A223890E9CB889458235
hash_match: true
schema_match: true
row_count_match: true
reference_row_count: 816
app_row_count: 816
reference_column_count: 11
app_column_count: 11
```

Columns:

```text
object_id
cluster_id
row_min
row_max
col_min
col_max
row_center
col_center
area_px
mean_anomaly
max_anomaly
```

### clusters_summary.csv

```text
reference_exists: true
app_exists: true
reference_length: 8696
app_length: 8696
reference_sha256: 552BB1104FEB428E21BB66B20C3BBFACC335E55FEE5E8750CECFE1D0178345CA
app_sha256: 552BB1104FEB428E21BB66B20C3BBFACC335E55FEE5E8750CECFE1D0178345CA
hash_match: true
schema_match: true
row_count_match: true
reference_row_count: 454
app_row_count: 454
reference_column_count: 5
app_column_count: 5
```

Columns:

```text
cluster_id
object_count
total_area_px
mean_object_area_px
max_object_anomaly
```

## Safety boundary

```text
No CSV rows were committed.
No object patches were committed.
No object_mask.npy or object patch NPY payloads were committed.
No coordinate-bearing row values were exposed in docs.
Only file identity, sizes, hashes, row counts, column names, and pass/fail status were recorded.
No public downloads, HTTP table/array serving, or map overlays were enabled.
```

## Decision

```text
D1D object-table real app-vs-reference parity: closed / passed
```

## Next recommended gate

```text
SAR/S1 remaining support, intermediate, and QA/provenance outputs outside S1-1 and filtered stack
```
