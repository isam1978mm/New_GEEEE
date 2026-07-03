# Plan C ??? App Hardening Start

## Date

2026-07-03

## Status

Option C is now the active next track.

```text
Active track: app hardening
Deferred track: frozen-reference notebook numeric parity
```

## Why Option C is active

B1 late Phase 2 app-porting and cleanup work is closed.

The remaining frozen-reference parity pass is blocked because the required exact notebook reference exports are not currently available.

Already documented:

```text id="8wioan"
Strict frozen-reference audit:
  expected_outputs: 18
  outputs_with_strict_notebook_refs: 0

Raw notebook/export source-recovery scan:
  total_hits: 0
```

This means no remaining B1 Partial item can be promoted to Full notebook numeric parity from the currently available local/private files.

## Deferred, not abandoned

Frozen-reference parity remains possible later.

To resume it, one of these must happen:

```text id="ra8rpx"
1. Exact frozen notebook reference exports are supplied, or
2. The notebook/export process is rerun to generate those exact references, or
3. A verified private archive containing the exact notebook outputs is recovered.
```

Once references exist, rerun the frozen-reference comparison only for the matching outputs.

Do not patch formulas or rerun Earth Engine just to force parity.

## Deferred items

```text id="subifh"
#8  Nano / treasure / geophysics stacks
#9  More feature stacks / rename layers
#15 Bonus / simulator features
#17 Extra S2 era pulls / masks
#29 AI tensor builder
```

Special case:

```text id="ea51xv"
#20 Fusion intelligence tensors
```

#20 is not a normal frozen-reference issue. It remains blocked by source-provenance mismatch and needs notebook-equivalent local S2/L9 inputs before a fair parity comparison.

## App hardening focus

Plan C should focus on production/local app quality:

```text id="m68c9m"
1. Redaction and privacy controls
2. Artifact inventory and output contracts
3. Local workflow reliability
4. UI/app entry-point hardening
5. Packaging and repeatable run commands
6. Test coverage for app behavior
7. Clear separation between public-safe outputs and private/local-only outputs
```

## Rule for future parity return

Do not reopen B1 parity work unless exact reference files are present.

When reopened, start with inventory first, then compare, then document. No guessing.

<!-- PLAN_C_INVENTORY_RESULT_START -->
## App hardening inventory result ??? 2026-07-03

The read-only Option C inventory is complete.

```text id="bj22q8"
selected_first_item: C1 ??? Redaction risk allowlist/denylist test
redaction_risk_file_count: 115
artifact_families_with_private_or_redaction_required_outputs: 9
```

Frozen-reference parity remains deferred. Plan C now proceeds with C1, using a docs/test-first approach and no app behavior change until the public/private safety contract is clear.
<!-- PLAN_C_INVENTORY_RESULT_END -->
