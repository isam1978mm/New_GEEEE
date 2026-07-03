# Plan C App Hardening Inventory Result

## Date

2026-07-03

## Scope

Read-only inventory for Option C app hardening.

No app behavior was changed. No raw arrays, coordinates, or private file contents are included in this public repo document.

## Inventory summary

```text
app_python_files: 200
docs_markdown_files: 325
scripts_python_files: 54
notebooks_ipynb_files: 1
test_file_count: 242
entry_point_candidate_count: 23
run_artifact_family_count: 17
artifact_families_with_private_or_redaction_required_outputs: 9
private_or_redaction_required_artifact_count: 41
review_required_binary_or_structured_output_count: 604
redaction_risk_file_count: 115
```

## First hardening candidates found

```text id="l1hw6l"
- Redaction risk allowlist/denylist test
- Document one canonical local run command
- Public-safe vs private-only artifact contract
- Artifact contract test review
```

## Selected first item

```text id="r3ex3y"
C1 ??? Redaction risk allowlist/denylist test
```

## Reason

The inventory found existing private-path and coordinate-like risk patterns in docs/source/tests and private/redaction-required artifact families in the current run output.

The first hardening item should prevent accidental public exposure while preserving private/local-only research behavior.

## Non-goals for C1

```text id="1ymcpv"
No app behavior change.
No artifact movement.
No raw array inspection.
No exact coordinate exposure.
No private target geometry exposure.
No Earth Engine rerun.
No notebook parity claim.
```

## C1 next step

Inspect the existing redaction/public-safety tests, then add or extend the smallest test contract that separates:

```text id="hwgh38"
public-safe files
private/local-only files
allowed test fixtures
blocked accidental public leaks
```

The test should fail only on unintended exposure, not on approved private/local-only documentation.
