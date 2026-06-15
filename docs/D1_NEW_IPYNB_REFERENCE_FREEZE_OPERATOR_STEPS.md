# D1 new.ipynb Reference Freeze — Operator Steps

## Current status

D1 reference freeze is **local skeleton created, not complete**.

The repo has a local helper that creates the outside-Git bundle skeleton:

```text
scripts/d1_init_reference_bundle.py
```

The helper writes under the Git-ignored `data/` tree by default. It does not add notebook outputs to Git.

## Local validation recorded

```text
python -m pytest tests/unit/test_d1_init_reference_bundle.py tests/unit/test_d1_validate_reference_manifest.py -q
```

Result:

```text
27 passed, 1 pytest cache warning
```

The warning was a local `.pytest_cache` permission warning, not a D1 test failure.

## Local skeleton recorded

The local skeleton was created at:

```text
data/private_references/notebook_frozen/new_ipynb_d1_20260615_local
```

Current local manifest state:

```text
manifest.local.template.json
finalized_manifest: False
```

This means the folder exists, but the real notebook outputs have not yet been frozen into a final `manifest.local.json`.

## Checklist item from LOCAL_PRIVATE_ROADMAP_CHECKLIST.md

```text
6. D1 real new.ipynb reference freeze
Status: Local skeleton created / waiting for real notebook outputs
```

## Checklist of the item

```text
[x] Add local bundle initializer: scripts/d1_init_reference_bundle.py.
[x] Add operator steps: docs/D1_NEW_IPYNB_REFERENCE_FREEZE_OPERATOR_STEPS.md.
[x] Add unit coverage for the local bundle initializer.
[x] Local validation: D1 initializer and manifest validator tests -> 27 passed, 1 pytest cache warning.
[x] Local bundle skeleton created.
[ ] Freeze the real new.ipynb outputs as the official private notebook baseline.
[ ] Keep the frozen reference outside Git.
[ ] Use this as the baseline for later parity checks.
```

## Step 1 — create the local bundle skeleton

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

Output:

```text
OK: D1 local reference bundle skeleton created
bundle_root: data/private_references/notebook_frozen/new_ipynb_d1_20260615_local
manifest_path: data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/manifest.local.template.json
finalized_manifest: False
```

## Step 2 — place real notebook outputs locally

Place real `new.ipynb` outputs under:

```text
data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/artifacts/
```

Suggested family folders:

```text
artifacts/dem/
artifacts/report/
artifacts/private_semantic/
artifacts/sar/
artifacts/pan/
```

Do not commit anything under `data/private_references/`.

## Step 3 — create the final local manifest

After placing outputs, rerun the helper with artifact paths that are relative under `artifacts/`.

Example shape:

```powershell
python scripts/d1_init_reference_bundle.py `
  --bundle-id new_ipynb_d1_20260615_local `
  --notebook-version local-new-ipynb-version `
  --source-run-id local-source-run `
  --operator Maher `
  --artifact-family dem `
  --artifact-family report `
  --artifact-path dem/reference_dem.tif `
  --artifact-path report/reference_report.json
```

This writes:

```text
data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/manifest.local.json
```

## Step 4 — validate the local manifest

```powershell
python scripts/d1_validate_reference_manifest.py `
  --manifest data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/manifest.local.json `
  --strict
```

Expected result:

```text
Summary: OK
```

## Step 5 — confirm nothing private is staged

```powershell
git status --short
```

Expected result: no files under `data/private_references/` appear.

## Done condition for D1 freeze

D1 freeze is done only when:

```text
[ ] Real new.ipynb outputs are placed under the local bundle artifacts folder.
[ ] manifest.local.json exists locally.
[ ] Local manifest validation passes in strict mode.
[ ] git status shows no private reference files staged.
```

## Next step

Move real `new.ipynb` outputs into the local bundle artifacts folder.

Next-step checklist:

```text
[ ] Identify the real output files from the completed new.ipynb run.
[ ] Copy them into the matching artifacts/ family folders.
[ ] Do not paste or commit private artifact contents.
[ ] Re-run the initializer with --artifact-path entries to create manifest.local.json.
[ ] Validate manifest.local.json with --strict.
```
