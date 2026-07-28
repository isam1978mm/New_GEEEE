# Option 2 — Rocky Mountain Arsenal radar-ordering test protocol — 2026-07-28

## Purpose

Run one bounded `Option 2 — Ordering Test` to answer only:

> Does the selected Sentinel-1 radar score consistently rank the mapped 3-foot cover above the mapped 2-foot cover?

This is not numerical-depth calibration. The result must not be reported in metres or centimetres and must not be added to the normal app.

## Candidate

Rocky Mountain Arsenal Integrated Cover System, Colorado.

The official 2022–2025 Annual Covers Reports establish:

- completed construction before the Sentinel-1 observation period;
- large coordinate-labelled 2-foot and 3-foot soil-cover polygons;
- shared vegetation assessment for the 2-foot and 3-foot covers;
- recurring inspection and maintenance records;
- sufficient clean interior width for a bounded comparison.

The site failed the formal calibration gate because the public record provides maintained cover categories rather than coordinate-tied final measured absolute depths, and because final construction equivalence and numerical survey uncertainty remain incomplete. Those failures are accepted for Option 2 only; they remain fatal for formal training.

## Frozen comparison zones

One conservative interior square is selected inside the mapped Shell 2-Foot Soil Cover and one equal-size conservative interior square is selected inside the mapped South Plants 3-Foot Soil Cover.

Each square is approximately 180 feet by 180 feet, or about 55 metres by 55 metres. The squares are positioned away from the mapped cover boundary, roads, buildings, monuments, lysimeters, drainage channels, and recorded 2025 maintenance areas.

Exact execution coordinates remain outside the public repository and must be supplied to the isolated test at runtime.

## Frozen observation period

Primary period:

```text
2022-01-01 through 2024-09-30
```

Reason:

- both covers were already complete;
- the period precedes the maintenance activities mapped in the 2025 report;
- recent annual reports support continuing inspection and vegetation management;
- the period is long enough to test repeated ordering rather than one image.

## Frozen Sentinel-1 selection

Use `COPERNICUS/S1_GRD` with:

- instrument mode `IW`;
- both `VV` and `VH` polarizations;
- images covering both frozen zones;
- one orbit direction and relative orbit selected solely by the largest acquisition count over the period;
- no selection based on zone values;
- the same selected orbit group for both zones;
- zone medians at the native 10-metre analysis scale;
- acquisition date, relative orbit, orbit direction, incidence angle, and valid-pixel count retained for QA.

## Primary score and expected order

Primary score:

```text
VV_to_VH_linear_ratio = 10 ** ((VV_dB - VH_dB) / 10)
```

This is the neutral name for the existing ratio historically labelled `NANO_Depth_Penetration`. It is not a depth measurement.

Frozen expected order:

```text
median ratio in mapped 3-foot zone > median ratio in mapped 2-foot zone
```

The direction is fixed before any radar values are inspected. It must not be reversed after results are known.

## Secondary diagnostics

The following are diagnostic only and cannot replace the primary score after results are seen:

- `VV_dB`;
- `VH_dB`;
- `VV_dB - VH_dB`;
- incidence-angle difference;
- valid-pixel counts;
- orbit and seasonal summaries.

## Monthly aggregation

For every usable acquisition, calculate the deep-minus-shallow primary-score difference. Aggregate acquisition differences by calendar month using the median.

A month is usable only when both zones have sufficient valid pixels and valid VV, VH, and incidence summaries.

## Frozen decision rule

### Ordering supported

Report `ordering_supported` only when all conditions pass:

1. at least 18 usable monthly comparisons;
2. at least 75 percent of usable months have the frozen expected order;
3. the lower bound of a two-sided 95-percent Wilson interval for the positive-month proportion is greater than 0.50;
4. the median monthly deep-minus-shallow difference is greater than zero;
5. at least three of four meteorological seasons have a positive median difference;
6. incidence-angle and valid-pixel QA do not show a systematic zone imbalance.

### Ordering inconsistent

Report `ordering_inconsistent` when either condition occurs:

- fewer than 55 percent of usable months have the frozen expected order; or
- at least two seasons have a non-positive median difference.

### No reliable separation

Report `no_reliable_separation` for every result between the two rules above, or when there are too few usable months.

## Stop rule

If the result is `ordering_inconsistent`, stop the numerical-depth plan before paid imagery or model training.

If the result is `no_reliable_separation`, do not claim depth feasibility. Reconsider the numerical-depth plan before spending money.

If the result is `ordering_supported`, it only justifies further investigation. It does not create a calibration row and does not enable app depth.

## Required output wording

Allowed:

```text
Option 2 radar ordering: supported / inconsistent / no reliable separation
```

Not allowed:

```text
calibrated depth
estimated depth in metres
validated depth model
```

## Repository and app safety

- Use an isolated draft PR.
- Do not merge experimental credentials or execution geometry.
- Do not modify production app code.
- Do not run training.
- Do not enable app depth.
- Keep exact execution polygons and raw feature rows out of public outputs.
