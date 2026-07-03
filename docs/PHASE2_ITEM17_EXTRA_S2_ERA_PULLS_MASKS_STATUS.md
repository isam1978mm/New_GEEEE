# Phase 2 Item #17 â€” Extra S2 Era Pulls / Masks

## Classification

Status: Partial / internal app stack-order proof clean.

This item is not marked Full notebook numeric parity yet. Full parity still requires exact frozen notebook stack outputs from the same export/run and a private numeric comparison.

## App owner

```text
app/pipeline/stages/s2_indices.py
```

## Canonical app output validated

```text id="53e6ch"
AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640.npy
```

## B1 internal stack-vs-band result

```text id="di7b4t"
stack shape: 640 x 640 x 13
dtype: float32
all_stack_matches_band_npy: True
max_abs_delta: 0.0
```

Validated bands:

```text id="niffm4"
0. AIX_2022_2026_CLOUDLT3_Jan_IronOxideProxy_Norm01
1. AIX_2022_2026_CLOUDLT3_Jan_MineralAlterationProxy_Norm01
2. AIX_2022_2026_CLOUDLT3_Jan_ThermalAnomaly_Norm01
3. AIX_2022_2026_CLOUDLT3_Apr_IronOxideProxy_Norm01
4. AIX_2022_2026_CLOUDLT3_Apr_MineralAlterationProxy_Norm01
5. AIX_2022_2026_CLOUDLT3_Apr_ThermalAnomaly_Norm01
6. AIX_2022_2026_CLOUDLT3_Aug_IronOxideProxy_Norm01
7. AIX_2022_2026_CLOUDLT3_Aug_MineralAlterationProxy_Norm01
8. AIX_2022_2026_CLOUDLT3_Aug_ThermalAnomaly_Norm01
9. AIX_2022_2026_CLOUDLT3_Elevation_Norm01
10. AIX_2022_2026_CLOUDLT3_Slope_Norm01
11. AIX_2022_2026_CLOUDLT3_Aspect_Norm01
12. AIX_2022_2026_CLOUDLT3_Hillshade_Norm01
```

Focused tests passed:

```text id="sjpb2j"
tests/unit/test_forbidden_terms.py
tests/unit/test_s2_indices.py
tests/unit/test_full_job_artifact_inventory.py
```

## Decision

Item #17 internal app stack/order proof is clean.

Do not mark Full notebook numeric parity until exact frozen notebook stack outputs are compared.
