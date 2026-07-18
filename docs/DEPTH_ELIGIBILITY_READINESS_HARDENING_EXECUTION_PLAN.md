# Depth Eligibility Readiness Hardening Execution Plan

Status: implementation and targeted testing complete on branch `claude/depth-blocked-calibration-6kn6v4`; the full unit suite requires one retest after a C1 redaction-baseline remediation. This document does not supply private calibration records, fit a model, or enable app depth output.

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

## First test execution

The owner ran:

```powershell
python -m pytest tests/unit/test_depth_calibration_pack_tools.py -v
```

Observed result:

```text
19 passed
1 pytest cache warning
```

The warning was limited to pytest being unable to write `.pytest_cache`; it did not affect the test results.

The owner then ran:

```powershell
python -m pytest tests/unit -q
```

Observed result:

```text
923 passed
2 failed
5 warnings
```

Both failures came from `tests/unit/test_plan_c_redaction_risk_allowlist.py`. They were not readiness-logic failures. The C1 scanner found the generic default private root in:

```text
scripts/init_depth_calibration_pack.py
scripts/validate_depth_calibration_pack.py
```

## Collateral C1 remediation

The initializer now derives its default adjacent private folder from `REPO_ROOT` instead of storing the absolute root as a source-code literal. This preserves the effective default location for a checkout at `C:\Dev\New_GEE` while removing the unapproved literal from that script.

The validator retains its deliberate default private dataset location. One occurrence is now explicitly approved in the existing C1 redaction-risk allowlist, following the repository's established allowlist policy. No private row, coordinate, source path, depth value, or user-specific home path was added.

Required retest:

```powershell
python -m pytest tests/unit/test_plan_c_redaction_risk_allowlist.py -v
python -m pytest tests/unit -q
```

## Files changed

```text
docs/DEPTH_ELIGIBILITY_READINESS_HARDENING_EXECUTION_PLAN.md
scripts/init_depth_calibration_pack.py
scripts/validate_depth_calibration_pack.py
scripts/finalize_depth_calibration_manifest.py
tests/unit/test_depth_calibration_pack_tools.py
tests/fixtures/plan_c_c1_redaction_risk_allowlist.json
```

No template schema, app stage, API, frontend, model, or private data changes are part of this patch.

## Verification commands

Run from the repository root after updating the branch:

```powershell
git pull --ff-only
python -m pytest tests/unit/test_plan_c_redaction_risk_allowlist.py -v
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
a5eba9a2413543b07ad9d3f9d8754ff3584248f0  docs: record depth readiness hardening implementation status
1dff738b31f7a7f6ebd900ec36da40fe31e260a8  fix: derive private calibration path from repo location
478326222260f269dc1419f0df3986a6c027820e  test: approve depth validator private-root default
```

## Checklist

- [x] Confirm the loophole.
- [x] Approve both eligible classes in all three splits.
- [x] Define shared eligibility logic.
- [x] Define deterministic aggregate fields.
- [x] Implement validator hardening.
- [x] Implement finalizer hardening.
- [x] Add regression tests.
- [x] Run the targeted depth-calibration tests: 19 passed.
- [x] Run the first full unit-suite attempt: 923 passed, 2 C1 failures.
- [x] Diagnose the C1 failures.
- [x] Commit the C1 remediation.
- [ ] Rerun the C1 redaction-risk tests.
- [ ] Rerun the full unit suite.
- [ ] Record the final passing result.
- [ ] Decide whether to merge or open a PR.

## Current decision

```text
execution_plan = documented
implementation = complete_on_branch
static_review = complete
targeted_depth_tests = passed_19_of_19
first_full_unit_run = 923_passed_2_c1_failed
c1_remediation = committed
full_unit_retest = pending_owner_runner
private_calibration_records = absent
scientific_validation = blocked
app_depth_output = not_available
```
