# Depth Eligibility Readiness Hardening Execution Plan

Status: implementation and verification complete on branch `claude/depth-blocked-calibration-6kn6v4`. The branch is ready for integration. This work does not supply private calibration records, fit a model, or enable app depth output.

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

`scripts/finalize_depth_calibration_manifest.py` reuses the validator eligibility aggregates and shared readiness helper. It refuses to finalize when an active split lacks an eligible positive or eligible confirmed negative, and it does not write the manifest after refusal.

### Tests

`tests/unit/test_depth_calibration_pack_tools.py` covers:

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

The first targeted run returned:

```text
19 passed
1 pytest cache warning
```

The first full unit-suite run returned:

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

The validator retains its deliberate default private dataset location. One occurrence is explicitly approved in the existing C1 redaction-risk allowlist, following the repository's established policy. No private row, coordinate, source path, depth value, or user-specific home path was added.

## Final verification

The owner updated the branch and ran:

```powershell
python -m pytest tests/unit/test_plan_c_redaction_risk_allowlist.py -v
python -m pytest tests/unit/test_depth_calibration_pack_tools.py -v
python -m pytest tests/unit -q
```

Observed results:

```text
C1 redaction-risk tests: 3 passed
Depth calibration tooling tests: 19 passed
Full unit suite: 925 passed
Full unit suite failures: 0
Full unit suite warnings: 4
```

The remaining warnings were non-failing runtime or environment warnings:

- two NumPy entropy warnings in the existing feature-stack test;
- one Rasterio missing-georeference warning in the existing parity test;
- one pytest cache access warning.

The warnings do not indicate a failure in the eligibility gate, finalizer, privacy guard, or manifest behavior.

## Local working-tree note

The owner checkout contained five untracked `.webm` files before the final verification. They were not part of this branch, were not modified, were not committed, and did not affect the test results.

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

## Verification conclusion

```text
eligibility_loophole = fixed
eligible_positive_and_negative_required_per_split = true
ineligible_rows_can_satisfy_split = false
zero_included_rows_can_reach_readiness = false
weak_or_proxy_positive_can_satisfy_gate = false
finalizer_uses_same_gate = true
finalizer_refusal_writes_manifest = false
privacy_regression_tests = passed
full_unit_suite = passed_925_of_925
branch_integration_status = ready
```

## Checklist

- [x] Confirm the loophole.
- [x] Approve both eligible classes in all three splits.
- [x] Define shared eligibility logic.
- [x] Define deterministic aggregate fields.
- [x] Implement validator hardening.
- [x] Implement finalizer hardening.
- [x] Add regression tests.
- [x] Run targeted depth-calibration tests: 19 passed.
- [x] Diagnose and remediate the initial C1 failures.
- [x] Rerun C1 redaction-risk tests: 3 passed.
- [x] Rerun targeted depth-calibration tests: 19 passed.
- [x] Run the final full unit suite: 925 passed.
- [x] Record the final passing result.
- [ ] Decide whether to merge directly or open a pull request.

## Current decision

```text
execution_plan = documented
implementation = complete_on_branch
static_review = complete
targeted_depth_tests = passed_19_of_19
c1_redaction_tests = passed_3_of_3
full_unit_suite = passed_925_of_925
branch_integration_status = ready
private_calibration_records = absent
scientific_validation = blocked
app_depth_output = not_available
```

The readiness hardening is complete. The larger depth project remains officially blocked by missing real private calibration records.