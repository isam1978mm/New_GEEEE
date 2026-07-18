# Depth Eligibility Readiness Hardening Execution Plan

Status: approved execution plan for validator and finalizer hardening. This document does not supply private calibration records, fit a model, or enable app depth output.

## Problem

The current readiness gate counts every row when deciding whether `train`, `validation`, and `holdout` are populated. An excluded, uncertain, weak-quality, or non-included row can therefore satisfy split coverage even though it cannot be used for relative-depth research.

The repository remains blocked by missing real private calibration records. This change only makes the readiness decision honest.

## Eligibility definition

A row is eligible for readiness only when all are true:

```text
reference_status = known_depth_positive or confirmed_no_target
label_quality is one of the fit-eligible independent quality levels
include_for_relative_depth = true
split = train, validation, or holdout
```

## Hardened minimum

Each active split must contain:

```text
at least one eligible known-depth positive
and
at least one eligible confirmed negative
```

This creates a six-record technical floor across at least three group-separated physical sites. It is only a contract and pipeline dry-run floor, not enough evidence for scientific model fitting or release.

## Implementation

### Validator

Update `scripts/validate_depth_calibration_pack.py` to:

1. add one shared eligibility predicate;
2. calculate eligible positive and confirmed-negative totals;
3. calculate deterministic per-split eligible counts with explicit zero keys;
4. expose aggregate-only eligible counts in the validator result;
5. add one shared eligibility readiness failure helper;
6. require both eligible classes in every active split;
7. preserve existing raw counts and manifest semantics.

### Finalizer

Update `scripts/finalize_depth_calibration_manifest.py` to reuse the validator eligibility aggregates and shared readiness helper. The finalizer must refuse incomplete eligible split coverage without printing private rows or identifiers.

### Tests

Update `tests/unit/test_depth_calibration_pack_tools.py` to cover:

- no eligible positive records;
- no eligible confirmed-negative records;
- an uncertain or non-included row cannot satisfy a split;
- a single-class split is blocked;
- explicit zero keys exist for missing eligible classes;
- raw counts remain unchanged;
- the finalizer refuses missing eligible split coverage;
- the valid six-row synthetic pack still finalizes and validates.

Direct readiness-helper tests should avoid unfinished manifest fields masking the intended result. End-to-end finalizer tests must verify refusal does not write the manifest.

## Files in scope

```text
scripts/validate_depth_calibration_pack.py
scripts/finalize_depth_calibration_manifest.py
tests/unit/test_depth_calibration_pack_tools.py
```

No template schema, app stage, API, frontend, model, or private data changes are part of this patch.

## Verification

```powershell
python -m pytest tests/unit/test_depth_calibration_pack_tools.py -v
python -m pytest tests/unit -q
```

A scratch private-pack test should also confirm:

```text
empty pack -> not_ready_no_records
valid rows before finalization -> not_ready_contract_errors
finalizer --write -> validation_passed
ineligible holdout -> validator and finalizer refuse
```

## Commit order

1. `fix: gate depth readiness on eligible records per split`
2. `test: guard eligible-split depth readiness gate`

## Checklist

- [x] Confirm the loophole.
- [x] Approve both eligible classes in all three splits.
- [x] Define shared eligibility logic.
- [x] Define deterministic aggregate fields.
- [x] Define validator and finalizer behavior.
- [x] Define regression tests.
- [ ] Implement validator hardening.
- [ ] Implement finalizer hardening.
- [ ] Add regression tests.
- [ ] Run targeted tests.
- [ ] Run the full unit suite.
- [ ] Verify branch commits.

## Current decision

```text
execution_plan = documented
implementation = starting
private_calibration_records = absent
scientific_validation = blocked
app_depth_output = not_available
```
