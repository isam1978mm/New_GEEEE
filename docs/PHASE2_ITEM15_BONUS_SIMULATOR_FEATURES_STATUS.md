# Phase 2 Item #15 â€” Bonus / Simulator Features

## Classification

Status: Partial / internal app stack-order proof clean.

This item is not marked Full notebook numeric parity yet. Full parity still requires exact frozen notebook stack outputs from the same export/run and a private numeric comparison.

## Canonical app families validated

```text
cell_072 -> AUX_BONUS_FEATURES_STACK_640.npy
cell_073 -> SIM_GEOPHYSICAL_STACK_640.npy
```

## B1 internal stack-vs-band result

```text id="vr7n5m"
AUX_BONUS_FEATURES max delta: 0.0
SIM_GEOPHYSICAL max delta: 0.0
```

Validated stack shapes:

```text id="807odw"
AUX_BONUS_FEATURES_STACK_640.npy -> 640 x 640 x 3, float32
SIM_GEOPHYSICAL_STACK_640.npy -> 640 x 640 x 4, float32
```

Focused tests passed:

```text id="awey6l"
tests/unit/test_forbidden_terms.py
tests/unit/test_feature_stacks.py
```

## Decision

Item #15 internal app stack/order proof is clean.

Do not mark Full notebook numeric parity until exact frozen notebook stack outputs are compared.
