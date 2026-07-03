# Phase 2 Item #8 — Nano / Treasure / Geophysics Stacks

Status: App-port / no exact notebook export.

## Canonical notebook cells

```text id="tr4z4g"
cell 037:
  NANO_Depth_Penetration = VV_lin / (VH_lin + 1e-6)
  NANO_Human_Geometry_Detector = VV_dB - VH_dB
  NANO_Mass_Anomaly = sqrt(VV_lin * VH_lin)
  NANO_RVI_Clean = 4 * VH_lin / (VV_lin + VH_lin + 1e-6)
  output: NANO_GEOPHYSICS_STACK_640.npy

cell 039:
  NANO_Metal_Signal_Pulse = (VH_lin * VV_lin) / (VV_lin + VH_lin + 1e-6)
  GEOPHYS_Sirdab_Cavity_Void = log(VV_lin) - log(VH_lin)
  GEOLOGIC_Chamber_Entry_Proxy = VH_lin / (VV_lin^2 + 1e-6)
  output: TREASURE_GEOPHYSICS_STACK_640.npy
```

## Export availability

The downloaded notebook export did not contain exact references for:

```text id="timatv"
NANO_GEOPHYSICS_STACK_640.npy
TREASURE_GEOPHYSICS_STACK_640.npy
```

So Full exact-file parity is blocked.

## App validation

```text id="qaf72c"
NANO_GEOPHYSICS_STACK_640.npy:
  exists
  shape: 640x640x4
  dtype: float32
  per-band NPY/TIF outputs: present
  stack-vs-band max delta: 0.0

TREASURE_GEOPHYSICS_STACK_640.npy:
  exists
  shape: 640x640x3
  dtype: float32
  per-band NPY/TIF outputs: present
  stack-vs-band max delta: 0.0
```

The valid treasure band order is:

```text id="u363xu"
1. NANO_Metal_Signal_Pulse
2. GEOPHYS_Sirdab_Cavity_Void
3. GEOLOGIC_Chamber_Entry_Proxy
```

## Decision

```text id="7jxba1"
No code patch.
Keep app implementation.
Do not mark Full exact-file parity unless exact notebook stack refs appear and private comparison passes.
```

## Corrected B1 stack/order validation

A later focused validator initially reported a TREASURE mismatch because it selected the wrong stack candidate: `NANO_GEOPHYSICS_STACK_640.npy` was included in a broad `*GEOPHYS*STACK*640*.npy` search and sorted before the actual TREASURE stack.

Corrected validation uses explicit stack paths:

```text
NANO stack:
NPY_STACKS/NANO_GEOPHYSICS_STACK_640.npy

TREASURE stack:
NPY_STACKS/TREASURE_GEOPHYSICS_STACK_640.npy
```

Corrected TREASURE band order:

```text
0. NANO_Metal_Signal_Pulse
1. GEOPHYS_Sirdab_Cavity_Void
2. GEOLOGIC_Chamber_Entry_Proxy
```

Result:

```text
NANO stack-vs-band max delta: 0.0
TREASURE stack-vs-band max delta: 0.0
Focused tests: passed
```

Decision:

```text
Item #8 internal app stack/order proof is clean.
Do not mark Full notebook numeric parity until exact frozen notebook stack outputs are compared.
```
