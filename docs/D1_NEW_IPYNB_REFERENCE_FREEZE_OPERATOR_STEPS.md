# D1 new.ipynb Reference Freeze — Operator Steps

## Current status

D1 reference freeze is **operator-ready, not complete**.

The repo now has a local helper that creates the outside-Git bundle skeleton:

```text
scripts/d1_init_reference_bundle.py
```

The helper writes under the Git-ignored `data/` tree by default. It does not add notebook outputs to Git.

## Checklist item from LOCAL_PRIVATE_ROADMAP_CHECKLIST.md

```text
6. D1 real new.ipynb reference freeze
Status: Open / high priority
```

## Checklist of the item

```text
[ ] Freeze the real new.ipynb outputs as the official private notebook baseline.
[ ] Keep the frozen reference outside Git.
[ ] Use this as the baseline for later parity checks.
```

## Step 1 — create the local bundle skeleton

Run from repo root:

```powershell
cd C:\Dev\New_GEE
python scripts/d1_init_reference_bundle.py `
  --bundle-id new_ipynb_d1_20260615_local `
  --notebook-version local-new-ipynb-version `
  --source-run-id local-source-run `
  --operator Maher
```

Expected local output:

```text
data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/
  artifacts/
  logs/
  manifest.local.template.json
  README.local.txt
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

After D1 freeze is done, move to:

```text
3. Frozen new.ipynb reference bundle outside Git
```

Next-step checklist:

```text
[ ] Confirm the final local bundle is complete.
[ ] Keep the bundle outside Git.
[ ] Do not commit real reference files, generated artifacts, ZIP contents, or private payloads.
[ ] Use the bundle as the truth copy for later app-vs-reference parity.
```
