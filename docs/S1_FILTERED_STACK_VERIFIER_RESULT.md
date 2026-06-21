# S1 filtered stack verifier result

Status: passed.

This document records the safe docs-only result for the separate S1 filtered stack tensor gate.

No NPY payloads, verifier report payloads, raster payloads, or reference files are included in this document.

## Verifier

S1 filtered stack verifier used:

```text
app.pipeline.parity.s1_filtered_stack_verify.verify_s1_filtered_stack_parity
```

Verifier run id:

```text
s1-filtered-stack-d1c-a11309bf-final
```

## Final summary

```text
overall_status: passed
status: passed
output_name: S1_FILTERED_LAYERS_STACK_640.npy
app_exists: true
reference_exists: true
shape_match: true
dtype_match: true
hash_match: true
runtime_output_verified: true
notebook_value_parity_verified: true
```

Value comparison summary:

```text
count_compared_values: 1638400
count_nan_or_nodata_values: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

## Output covered

```text
NPY_STACKS/S1_FILTERED_LAYERS_STACK_640.npy: passed
```

## Scope boundary

This result closes only the separate S1 filtered stack tensor gate.

It does not broaden S1-1 or SAR/S1 parity to unrelated outputs.

Important boundary:

```text
S1-1 per-band ASC/DESC filtered outputs were closed separately.
This stack gate covers only S1_FILTERED_LAYERS_STACK_640.npy.
Final app RTC outputs are not treated as this stack equivalent.
RADAR_*_640_app aliases are not treated as this stack equivalent.
radar_db_support_stack.npy and radar_linear_support_stack.npy are not treated as this stack equivalent.
No public downloads, HTTP array serving, or map overlays were enabled.
No NPY payloads were committed.
No verifier tolerance relaxation was used.
```

## Decision

```text
S1 filtered stack tensor real app-vs-reference parity: closed / passed
```

## Next recommended gate

```text
Choose the next source-recovery or parity family explicitly.
Recommended candidates:
- PAN/optical component and stack parity
- AI_READY remaining support families
- D1D object-table outputs
- SAR/S1 remaining support, intermediate, and QA/provenance outputs outside S1-1 and the filtered stack
```
