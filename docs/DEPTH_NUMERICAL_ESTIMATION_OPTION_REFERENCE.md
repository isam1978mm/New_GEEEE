# Numerical depth strategy — canonical option reference

## Purpose

This document fixes the permanent option numbers and short names used when discussing the numerical-depth project.

From now on, a reference such as `Option 3` means the option defined here. The option numbers must not be silently renamed or reassigned.

This document does not select an option by itself. It only defines the shared vocabulary. The active plan changes only when the user explicitly chooses an option or instructs the work to proceed under it.

## Option 1 — Global Numerical Depth

### Short name

`Option 1 — Global Depth`

### What it is

Continue the strict multi-site calibration plan. Collect independent positive sites, confirmed negative areas, measured depths, numerical uncertainty, coordinate-tied polygons, comparable radar-facing surfaces, and stable Sentinel-1 periods across train, validation, and holdout groups.

### What the user may eventually get

A transferable numerical depth estimate that may work beyond one AOI, subject to successful training and independent validation.

### What the user does not get yet

No immediate depth output. One successful site is not enough.

### Cost and risk

Highest cost, longest schedule, and highest documentary burden. The current project has zero usable calibration rows.

## Option 2 — Radar Ordering Test

### Short name

`Option 2 — Ordering Test`

### What it is

Use one site where approximate shallow and deep zones are already known, even if the evidence is not strong enough for formal model training. Run a bounded radar comparison only to answer whether the radar measurement consistently orders shallow and deep areas correctly.

### What the user gets

A feasibility result such as:

- ordering supported;
- ordering inconsistent;
- no reliable separation.

### What the user does not get

No calibrated depth, no metres or centimetres, no deployable depth model, and no claim that depth caused the radar difference.

### Decision rule

If ordering fails consistently, stop the numerical-depth plan before spending more money. If ordering succeeds, the result only justifies further investigation.

## Option 3 — Complete Candidates

### Short name

`Option 3 — Complete Candidates`

### What it is

Stop broad searches across hundreds of new sites. Work only on existing near-complete candidates that are one missing document or one decisive check away from a final answer.

Examples include Tyrone Dam 3X, Syncrude 1990, and NAS Alameda, but only when the missing evidence can be specifically identified and searched for.

### What the user gets

A final pass-or-close decision on the strongest existing candidates without restarting the broad candidate search.

### What the user does not get immediately

No app depth output unless one candidate actually passes the remaining documentary gates.

### Operating rule

Do not reopen a closed candidate merely because it was promising. Reopen only when there is a concrete missing record or decisive unresolved check.

## Option 4 — Local AOI Calibration

### Short name

`Option 4 — Local AOI Calibration`

### What it is

The operator supplies, inside one AOI:

- one known shallow numerical reference;
- one known deeper numerical reference;
- one confirmed control area.

The app creates a local relationship and estimates depth only inside that AOI, between the supplied reference depths, and under comparable surface conditions.

### What the user gets

An output labelled:

> **Locally calibrated depth estimate**  
> Valid only for this AOI, between the supplied reference depths, and under comparable surface conditions.

### What the user does not get

No global or transferable model. A calibration from one AOI cannot automatically be used elsewhere.

### Important rule

If the shallow and deep references have no numerical measured depths, the output must be called `Local relative depth ranking`, not a depth estimate.

## Option 5 — Change Measurement Target

### Short name

`Option 5 — Change Target`

### What it is

Stop treating depth in metres as the primary product. Redirect the app toward measurements the radar may support more directly, such as:

- surface disturbance;
- construction change;
- settlement or deformation indicators;
- relative anomaly;
- likelihood that two zones differ;
- shallow/deep ordering without metres.

### What the user gets

A more defensible radar product sooner, with outputs tied to change, anomaly, comparison, or ordering.

### What the user does not get

No numerical depth in metres unless a separate local or global calibration is later proven.

## Canonical comparison

| Option | Canonical name | Main result |
|---|---|---|
| 1 | Global Numerical Depth | Transferable depth model, if enough evidence is eventually collected |
| 2 | Radar Ordering Test | Cheap pass/fail feasibility test without metres |
| 3 | Complete Candidates | Finish only near-complete existing candidates |
| 4 | Local AOI Calibration | Numerical depth valid only inside one supplied AOI |
| 5 | Change Measurement Target | Disturbance, change, anomaly, comparison, settlement, or ordering |

## Usage examples

- `Proceed with Option 2` means run the bounded shallow/deep ordering feasibility route.
- `Option 3` means the complete-candidates-only strategy.
- `Switch to Option 4` means replace the global approach with local AOI calibration.
- `Pause Option 1` means stop the broad global calibration effort without deleting its records.
- `Compare Option 3 and Option 4` means compare the canonical options defined in this document.

## Current status at creation

This reference document does not change the active scientific plan.

```text
usable calibration rows = 0
numerical depth ready = no
app depth enabled = false
Earth Engine query executed = no
training started = false
```
