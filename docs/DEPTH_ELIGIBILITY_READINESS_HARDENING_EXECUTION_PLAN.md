# Depth Eligibility Readiness Hardening Execution Plan

Status: implementation complete on branch `claude/depth-blocked-calibration-6kn6v4`; test execution remains pending because direct branch commits have no attached CI runner. This document does not supply private calibration records, fit a model, or enable app depth output.

## Problem

The previous readiness gate counted every row when deciding whether `train`, `validation`, and `holdout` were populated. An excluded, uncertain, weak-quality, or non-included row could therefore satisfy split coverage even though it could not be used for relative-depth research.

The repository remains blocked by missing real private calibration records. This hardening only makes the readiness decision honest.

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

## Implemented changes

### Validator

`scripts/validate_depth_calibration_pack.py` now:

1. defines one shared eligibility predicate;
2. calculates eligible positive and confirmed-negative totals;
3. calculates deterministic per-split eligible counts with explicit zero keys;
4. exposes aggregate-only eligible counts in the validator result;
5. defines one shared eligibility-readiness failure helper;
6. requires both eligible classes in every active split;
7. preserves existing raw counts and manifest semantics.

New aggregate-only output fields:

```text
eligible_positive_count
eligible_confirmed_negative_count
eligible_positive_by_split
eligible_confirmed_negative_by_split
```

### Finalizer

`scripts/finalize_depth_calibration_manifest.py` now reuses the validator eligibility aggregates and shared readiness helper. It refuses to finalize when an active split lacks an eligible positive or eligible confirmed negative, and it does not write the manifest after refusal.

### Tests

`tests/unit/test_depth_calibration_pack_tools.py` now covers:

- no eligible positive records;
- no eligible confirmed-negative records;
- an uncertain or non-included row cannot satisfy a split;
- a weak/proxy positive cannot satisfy the eligible positive gate;
- a single-class split is blocked;
- explicit zero keys exist for missing eligible classes;
- raw counts remain unchanged;
- the finalizer refuses missing eligible split coverage without writing;
- the valid six-row synthetic pack still finalizes and validates.

Direct readiness-helper tests avoid unfinished manifest fields masking the intended result. The end-to-end finalizer test verifies refusal leaves the manifest unchanged.

## Files changed

```text
docs/DEPTH_ELIGIBILITY_READINESS_HARDENING_EXECUTION_PLAN.md
scripts/validate_depth_calibration_pack.py
scripts/finalize_depth_calibration_manifest.py
tests/unit/test_depth_calibration_pack_tools.py
```

No template schema, app stage, API, frontend, model, or private data changes are part of this patch.

## Verification commands

Run from the repository root after switching to the branch:

```powershell
git switch claude/depth-blocked-calibration-6kn6v4
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

## Branch commits

```text
ac607d2f841ecedce40fe00c9c84b133308e45e7  docs: plan eligible-split depth readiness hardening
b2ee75c5dd64ecc69ed3d37a317b402fb71fa770  fix: gate depth readiness on eligible records per split
4a70af812ca62d5f9b954c3e73c5bab1b7dcc177  fix: apply eligible-split gate in depth manifest finalizer
aec640f2339358348f85aa8323b7091df2c84b3c  test: guard eligible-split depth readiness gate
```

## Checklist

- [x] Confirm the loophole.
- [x] Approve both eligible classes in all three splits.
- [x] Define shared eligibility logic.
- [x] Define deterministic aggregate fields.
- [x] Implement validator hardening.
- [x] Implement finalizer hardening.
- [x] Add regression tests.
- [x] Verify branch diff contains only the planned files.
- [ ] Run targeted tests on a repository checkout.
- [ ] Run the full unit suite.
- [ ] Record test results.
- [ ] Decide whether to merge or open a PR.

## Current decision

```text
execution_plan = documented
implementation = complete_on_branch
static_review = complete
targeted_tests = pending_external_runner
full_unit_suite = pending_external_runner
private_calibration_records = absent
scientific_validation = blocked
app_depth_output = not_available
```
