# NB Results Add-ons — Approved Plan

Date: 2026-08-13

Status: **DOCUMENTATION ONLY — IMPLEMENTATION NOT STARTED**

This document records the user-approved direction for adding notebook-derived result fields to the app without changing the existing classifier and without replacing the separate calibrated numerical-depth project.

## 1. Approved naming

Use these exact names in the app and documentation:

- **NB metal signature**
- **NB void signature**
- **NB ceramic signature**
- **NB mass signature**
- **NB best object interpretation**
- **NB false-signature score**
- **NB depth**

These are notebook-derived add-ons to the Results presentation.

Do not rename them to generic `metal`, `depth`, `material`, or similar terms that could be confused with confirmed physical measurements.

## 2. Relationship to the existing classifier

The existing classifier remains unchanged.

The NB fields are additive result fields only. They must not:

- replace Class A–J;
- change the current app score;
- change classifier thresholds;
- change classifier object detection;
- change classifier review order;
- change classifier API contracts unless a later implementation plan explicitly requires a separate additive artifact;
- be presented as physical confirmation.

The intended result structure is conceptually:

```text
Existing classifier result
    Class A–J
    App score
    Finding label / reason

NB add-ons
    NB metal signature
    NB void signature
    NB ceramic signature
    NB mass signature
    NB best object interpretation
    NB false-signature score
    NB depth
```

## 3. NB metal signature

The notebook metal-like signature is a weighted proxy assembled from notebook-derived signal families.

The notebook formula is:

```text
NB metal signature =
    0.40 × gold signal
  + 0.25 × silver signal
  + 0.25 × mass signal
  + 0.10 × SAR compact-scatterer signal
```

The result is constrained to the notebook's normalized 0–1 range.

Presentation requirement:

```text
NB metal signature: <score>
```

Optionally, a plain-language band such as LOW / MEDIUM / HIGH may be added later if thresholds are separately documented and approved.

Scientific boundary:

- It is a notebook-derived proxy.
- It is not confirmed metal detection.
- It is not equivalent to a metal detector, magnetometer, EM induction survey, GPR confirmation, excavation, or direct field observation.

## 4. Other approved NB signatures

### NB void signature

Notebook formula:

```text
NB void signature =
    0.45 × tunnel signal
  + 0.25 × hidden-door / entrance signal
  + 0.15 × TPI
  + 0.15 × roughness
```

This is a cavity / void-like screening signature, not physical confirmation of a tunnel, chamber, shaft, or cavity.

### NB ceramic signature

Preserve the notebook-derived ceramic / pottery proxy used by the notebook's higher-level object interpretation.

This is a screening signature only and must not be presented as confirmed ceramic material.

### NB mass signature

Preserve the notebook-derived mass / compact-anomaly proxy used by the notebook's higher-level interpretation logic.

This is not a measured physical mass.

### NB false-signature score

Preserve the notebook's false-signature / rejection support as an explicit NB result so the user can see when the notebook logic itself considers a candidate more likely to be a false pattern.

Do not hide this field when it is available.

## 5. NB best object interpretation

The notebook contains higher-level rule-based interpretations assembled from the proxy signatures.

The approved NB add-on may expose the best notebook-style interpretation while retaining the notebook's non-confirmatory status.

Examples found in the notebook include:

- jar / جرة
- chest / صندوق
- sarcophagus / تابوت
- ran / ران
- statue / تمثال
- void / فراغ
- false signature / وهم

The notebook also contains more specific subclass wording in some paths, including examples such as:

- gold / metal jar
- rock or metal sarcophagus
- open tunnel / passage
- buried stairs or entrance
- compressed chamber / royal burial
- burial shaft
- temple hall / archaeological walls
- secret door / partition wall

Implementation must not silently convert these labels into confirmed real-world object identities. They remain **NB best object interpretation** only.

## 6. NB depth — two notebook-derived values

NB depth must preserve the two distinct depth-related notebook concepts and must not merge them into one ambiguous number.

### 6.1 NANO_Depth_Penetration

The notebook defines:

```text
NANO_Depth_Penetration = VV_linear / (VH_linear + epsilon)
```

This is a radar-derived penetration proxy.

Requirements:

- preserve it as an NB depth support value;
- do not label it in metres;
- do not call it measured depth;
- do not convert it to metres unless a future validated conversion is separately approved.

Suggested presentation:

```text
NB depth — NANO penetration proxy: <value>
```

### 6.2 depth_proxy_m

The notebook's metre-valued depth proxy is:

```text
NB depth (depth_proxy_m) =
    0.6
  + 1.2 × void signature
  + 0.9 × SAR compact-scatterer
  + 0.7 × thermal inertia
  + 0.5 × thermal delta
  + 0.4 × terrain roughness
```

The notebook then clips this value to:

```text
0.4 m ≤ depth_proxy_m ≤ 5.0 m
```

This value is approved to be exposed under the exact user-facing name **NB depth**.

Required presentation boundary:

```text
NB depth: <value> m
Notebook-derived indirect proxy — not calibrated numerical depth.
```

The notebook itself describes this value as an indirect estimate rather than GPR-measured depth. That limitation must remain visible in the app or immediately adjacent documentation.

## 7. Remove the notebook's fake/default 3.0 m fallback

One notebook output / visualization path substitutes:

```text
depth = 3.0
```

when no usable depth column exists.

This fallback is **not approved for the app**.

The app behavior must instead be:

```text
if depth_proxy_m can be calculated:
    NB depth = calculated depth_proxy_m
else:
    NB depth = NOT AVAILABLE
```

Never silently output 3.0 m because a depth value is missing.

If a later map / 3D visualization requires a vertical placement value, the UI must either use the calculated NB depth or clearly use a separate non-depth display constant that cannot be mistaken for a result.

## 8. Separation from the calibrated numerical-depth project

**NB depth and Numerical Depth Estimate are different systems and must remain separate.**

### NB depth

- notebook-derived heuristic;
- can be calculated from notebook-style proxy layers when the required inputs exist;
- includes NANO penetration proxy and `depth_proxy_m`;
- `depth_proxy_m` is limited to 0.4–5.0 m by the notebook formula;
- not calibrated against measured reference depth;
- not validated physical depth.

### Numerical Depth Estimate

- separate calibration-based project;
- intended to use measured reference depths and validated calibration;
- current project status remains unchanged;
- current usable calibration rows remain 0;
- numerical depth remains blocked until the calibration requirements are satisfied.

Adding NB depth must **not** be described as unblocking Numerical Depth Estimate.

## 9. Source-input integrity requirement

Implementation must use the notebook's actual source signal families or an explicitly documented equivalent that is proven to reproduce the notebook calculation.

Do not derive NB metal signature or NB depth directly from the existing Class E score.

Do not invent substitute weights from the current classifier.

Relevant notebook-style source families already represented in repository notebook-parity infrastructure include items such as:

- Secret Gold Halo
- Secret Silver Oxide
- Secret Tunnel Ceiling
- Secret Thermal Inertia
- Secret Hidden Doors
- Mass Report
- Pottery Report
- DEM slope
- DEM TPI
- DEM roughness

Before implementation, the current app/run pipeline must be mapped against every required NB source to determine:

1. already available source;
2. equivalent but renamed source;
3. missing source;
4. unsafe / scientifically unsupported source;
5. required fallback behavior.

Missing required inputs must produce `NOT AVAILABLE`; they must not be replaced with arbitrary constants.

## 10. Required result behavior

For each detected object / finding, the intended additive output is:

```text
NB metal signature: <score or NOT AVAILABLE>
NB void signature: <score or NOT AVAILABLE>
NB ceramic signature: <score or NOT AVAILABLE>
NB mass signature: <score or NOT AVAILABLE>
NB best object interpretation: <label or NOT AVAILABLE>
NB false-signature score: <score or NOT AVAILABLE>

NB depth
  NANO penetration proxy: <value or NOT AVAILABLE>
  NB depth: <depth_proxy_m> m or NOT AVAILABLE
```

No field may silently fabricate a result when its inputs are unavailable.

## 11. UI wording guardrails

Allowed examples:

```text
NB metal signature: 0.78
NB best object interpretation: chest / صندوق
NB depth: 2.65 m
NB method — indirect notebook proxy
```

Disallowed examples:

```text
Metal detected
Chest confirmed
Tunnel confirmed
Depth measured: 2.65 m
GPR depth: 2.65 m
```

The NB prefix is mandatory on the notebook-derived result group to distinguish these outputs from other app results.

## 12. Implementation scope control

This document does not authorize implementation yet.

When implementation is explicitly approved, the work must be scoped so that it does not change:

- the existing classifier algorithm;
- existing Class A–J definitions;
- the current classifier score;
- Option 5 scientific logic;
- calibrated numerical-depth gates;
- existing measured-depth evidence requirements;
- previously completed depth research campaigns.

The preferred implementation is an additive NB results artifact / calculation and additive UI presentation.

## 13. Required implementation sequence after explicit approval

1. Inventory every source layer required by the notebook formulas.
2. Map those sources to current app artifacts.
3. Identify missing inputs and define `NOT AVAILABLE` behavior.
4. Implement NB signature calculations separately from the core classifier.
5. Implement both NB depth values separately:
   - NANO penetration proxy;
   - `depth_proxy_m`.
6. Explicitly remove / prohibit the 3.0 m fallback.
7. Add per-object NB output fields.
8. Add NB result presentation as an add-on to the Results page.
9. Add tests proving:
   - existing classifier outputs are unchanged;
   - numerical-depth status is unchanged;
   - no fake 3.0 m fallback exists;
   - missing NB inputs yield `NOT AVAILABLE`;
   - NB labels remain visibly distinct from confirmed measurements.
10. Validate on a real completed run before merge.

## 14. Current status at documentation time

- Existing classifier: preserved.
- NB result add-ons: approved in concept and documented here.
- NB implementation: **NOT STARTED**.
- Numerical Depth Estimate: **STILL BLOCKED** under its existing calibration requirements.
- No code change is authorized by this document alone.

## 15. Next action

Wait for explicit user approval to proceed from documentation into implementation planning / source-layer mapping.
