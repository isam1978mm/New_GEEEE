# Radar linear support stack parity result

Status: closed / contract clarified.

This document records a safe docs-only summary from a local comparison of the D1C notebook radar stack reference against the app radar support stack artifacts.

No manifest bodies, CSV rows, image identifiers, raster payloads, NPY payloads, coordinates, or per-pixel values are included.

## Scope

App run:

```text
a11309bf-ed47-4bf5-bbf4-f755b904065c
```

Notebook/reference root:

```text
D1C_NEW_IPYNB_REFERENCE_2026_06_10
```

Reference stack candidate located:

```text
NPY_STACKS/RADAR_STACK_HWC_640_..._DBONLY_LOCALDEM_v5.npy
shape: 640 x 640 x 4
```

App stack artifacts checked:

```text
stacks/tensor_support/radar_linear_support_stack.npy
stacks/tensor_support/radar_db_support_stack.npy
NPY_STACKS/RADAR_STACK_HWC_640_app.npy
```

All app paths existed and all stack shapes were:

```text
640 x 640 x 4
```

## Contract clarification

The app has two separate radar support stack contracts:

```text
radar_db_support_stack:
  VV_dB
  VH_dB
  logRatio_dB
  incidence/angle

radar_linear_support_stack:
  VV_dB converted to linear
  VH_dB converted to linear
  logRatio_dB converted to linear
  incidence/angle copied through unchanged
```

The notebook D1C `RADAR_STACK_HWC_640` reference is a raw dB stack, not a linear stack.

Therefore, comparing `radar_linear_support_stack` directly to the notebook raw dB stack is expected to match only the incidence channel and fail the converted radar channels.

## Safe comparison results

Raw dB stack parity:

```text
app_notebook_alias_vs_reference_raw_db:
  matching_percent: 99.99993896484375
  mean_abs_diff: 2.80010094133587e-07
  max_abs_diff: 6.67572021484375e-06

app_radar_db_vs_reference_raw_db:
  matching_percent: 99.99993896484375
  mean_abs_diff: 2.80010094133587e-07
  max_abs_diff: 6.67572021484375e-06
```

Direct linear-vs-raw comparison, retained only as the explanation for the previous 25 percent diagnostic:

```text
app_radar_linear_vs_reference_raw_db:
  matching_percent: 25.0
  mean_abs_diff: 5.588461368247964
```

This 25 percent result is expected because one of four channels, incidence/angle, is already in the same units.

Linear contract parity after converting the notebook raw dB reference into the app linear contract:

```text
app_radar_linear_vs_reference_converted_to_linear_contract:
  matching_percent: 99.99664306640625
  mean_abs_diff: 1.5195995558769937e-07
  max_abs_diff: 2.6702880859375e-05
```

Channel-level linear contract results:

```text
VV_or_vv_linear:
  matching_percent: 100.0
  mean_abs_diff: 1.1780448403442278e-08
  max_abs_diff: 4.76837158203125e-07

VH_or_vh_linear:
  matching_percent: 100.0
  mean_abs_diff: 3.8234907151490914e-09
  max_abs_diff: 1.1920928955078125e-07

logRatio_or_ratio_linear:
  matching_percent: 99.986572265625
  mean_abs_diff: 5.920775583945215e-07
  max_abs_diff: 2.6702880859375e-05

incidence_or_angle:
  matching_percent: 100.0
  mean_abs_diff: 1.5832483768463136e-10
  max_abs_diff: 3.814697265625e-06
```

## Decision

```text
radar_db_support_stack vs D1C raw RADAR_STACK_HWC reference: closed / passed within numeric tolerance
RADAR_STACK_HWC_640_app notebook alias vs D1C raw RADAR_STACK_HWC reference: closed / passed within numeric tolerance
radar_linear_support_stack vs raw dB reference: expected unit-contract mismatch / not a failure
radar_linear_support_stack vs D1C reference converted to linear contract: closed / passed within numeric tolerance
```

## Safety boundary

```text
No manifest bodies were committed.
No SAR JSON bodies were committed.
No CSV rows were committed.
No image identifiers were committed.
No raster or NPY payloads were committed.
No per-pixel values were committed.
Only safe aggregate status counts, pass/fail classifications, and aggregate metrics were recorded.
No public downloads, HTTP table/array serving, or map overlays were enabled.
```
