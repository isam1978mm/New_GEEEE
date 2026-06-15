# D1 new.ipynb Reference Freeze — Operator Steps

## Current status

D1 reference freeze is **complete locally and outside Git**.

The repo has local helpers for the outside-Git D1 bundle:

```text
scripts/d1_init_reference_bundle.py
scripts/d1_finalize_reference_bundle.py
scripts/d1_validate_reference_manifest.py
```

The helpers write under the Git-ignored `data/` tree by default. They do not add notebook outputs to Git.

## Local validation recorded

```text
python -m pytest tests/unit/test_d1_finalize_reference_bundle.py tests/unit/test_d1_init_reference_bundle.py tests/unit/test_d1_validate_reference_manifest.py -q
```

Result:

```text
30 passed, 1 pytest cache warning
```

The warning was a local `.pytest_cache` permission warning, not a D1 test failure.

## Local frozen baseline recorded

The local frozen bundle exists at:

```text
data/private_references/notebook_frozen/new_ipynb_d1_20260615_local
```

Final local manifest:

```text
data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/manifest.local.json
```

Safe summary:

```text
artifact_count: 109
family_count: 4
strict manifest validation: Summary: OK
git status: no data/private_references/ files shown
```

No real artifacts, artifact contents, private payloads, or final local manifest are committed.

## Checklist item from LOCAL_PRIVATE_ROADMAP_CHECKLIST.md

```text
6. D1 real new.ipynb reference freeze
Status: Done / local private reference frozen outside Git
```

## Checklist of the item

```text
[x] Add local bundle initializer: scripts/d1_init_reference_bundle.py.
[x] Add local bundle finalizer: scripts/d1_finalize_reference_bundle.py.
[x] Add operator steps: docs/D1_NEW_IPYNB_REFERENCE_FREEZE_OPERATOR_STEPS.md.
[x] Add unit coverage for the local bundle initializer/finalizer.
[x] Local validation: D1 initializer/finalizer/manifest tests -> 30 passed, 1 pytest cache warning.
[x] Local bundle skeleton created.
[x] Freeze the real new.ipynb outputs as the official private notebook baseline.
[x] Keep the frozen reference outside Git.
[x] Use this as the baseline for later parity checks.
[x] Finalized manifest.local.json with 109 artifact paths across 4 families.
[x] Strict manifest validation passed with Summary: OK.
[x] git status --short did not show data/private_references/ files.
```

## Completed steps

### Step 1 — create the local bundle skeleton

Done.

Command used:

```powershell
cd C:\Dev\New_GEE
python scripts/d1_init_reference_bundle.py `
  --bundle-id new_ipynb_d1_20260615_local `
  --notebook-version local-new-ipynb-version `
  --source-run-id local-source-run `
  --operator Maher
```

### Step 2 — place real notebook outputs locally

Done.

The real notebook output files were copied under:

```text
data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/artifacts/
```

### Step 3 — create the final local manifest automatically

Done.

Command used:

```powershell
python scripts/d1_finalize_reference_bundle.py `
  --bundle-root data/private_references/notebook_frozen/new_ipynb_d1_20260615_local `
  --notebook-version local-new-ipynb-version `
  --source-run-id a11309bf-ed47-4bf5-bbf4-f755b904065c `
  --operator Maher
```

Safe result:

```text
OK: D1 local reference manifest finalized
artifact_count: 109
family_count: 4
```

### Step 4 — validate the local manifest

Done.

Command used:

```powershell
python scripts/d1_validate_reference_manifest.py `
  --manifest data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/manifest.local.json `
  --strict
```

Result:

```text
Summary: OK
```

### Step 5 — confirm nothing private is staged

Done.

`git status --short` did not show `data/private_references/` files.

There is unrelated local Git noise that should be handled separately before any future commit:

```text
frontend-v2/dist changes
test-results/
graphify-out/
.pytest-tmp-* folders
```

## Done condition for D1 freeze

```text
[x] Real new.ipynb outputs are placed under the local bundle artifacts folder.
[x] manifest.local.json exists locally.
[x] Local manifest validation passes in strict mode.
[x] git status shows no private reference files staged.
```

## Next step

Move to:

```text
10. Real app-vs-reference parity
```

Next-step checklist:

```text
[ ] Use the frozen D1 local reference as the baseline.
[ ] Do not expose or commit private reference files.
[ ] Build/verify the app output manifest against the frozen notebook reference manifest.
[ ] Run parity verifiers for families that already have implemented app outputs.
[ ] Keep SAR/S1 and PAN recovery separate until their exact contracts are clear.
```
