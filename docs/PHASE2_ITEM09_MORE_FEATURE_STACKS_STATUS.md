# Phase 2 Item #9 â€” More Feature Stacks / Rename Layers

## Classification

Status: Partial / internal app stack-order proof clean.

This item is not marked Full notebook numeric parity yet. Full parity still requires exact frozen notebook stack outputs from the same export/run and a private numeric comparison.

## Canonical app families validated

Corrected B1 validation used exact app constants instead of guessed fallback names.

```text
cell_050 -> RAD_S0_MASTER_STACK_640.npy
cell_053 -> RAD_MASTER_CUBE_640.npy
cell_051 -> GPHYS_MASTER_STACK_640.npy
cell_047 -> MASTER_RTC_REFINED_STACK_640.npy
cell_052 -> ARCH_TARGETS_STACK_640.npy
cell_054 -> ULTIMATE_GPHYS_SCAN_640.npy
```

## Corrected validator note

An earlier validator used incorrect fallback filenames for two families:

```text
RAD_MASTER_CUBE_STACK_640.npy
ULTIMATE_GPHYS_SCAN_STACK_640.npy
```

Those are not the app constants. The corrected validation used:

```text
RAD_MASTER_CUBE_640.npy
ULTIMATE_GPHYS_SCAN_640.npy
```

## Corrected B1 internal stack-vs-band result

```text
RAD_S0_MASTER max delta: 0.0
RAD_MASTER_CUBE max delta: 0.0
GPHYS_MASTER max delta: 0.0
MASTER_RTC_REFINED max delta: 0.0
ARCH_TARGETS max delta: 0.0
ULTIMATE_GPHYS_SCAN max delta: 0.0
```

Focused tests passed:

```text
tests/unit/test_forbidden_terms.py
tests/unit/test_feature_stacks.py
```

## Decision

Item #9 internal app stack/order proof is clean.

Do not mark Full notebook numeric parity until exact frozen notebook stack outputs are compared.
