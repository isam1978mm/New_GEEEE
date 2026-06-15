# Real App-vs-Reference Parity — Operator Steps

## Current status

Real app-vs-reference parity is **started, not proven**.

D1 local reference freeze is complete outside Git. The next safe step is an inventory bridge that confirms the frozen D1 manifest can be compared against an app output folder without reading artifact contents.

## Checklist item from LOCAL_PRIVATE_ROADMAP_CHECKLIST.md

```text
10. Real app-vs-reference parity
Status: Unblocked by D1 freeze / next major work
```

## Checklist of the item

```text
[x] D1 frozen local reference exists outside Git.
[x] Add safe D1 inventory comparator: scripts/d1_compare_app_reference_inventory.py.
[x] Add unit coverage for the D1 inventory comparator.
[ ] Run inventory comparison locally.
[ ] Build/verify the app output manifest against the frozen notebook reference manifest.
[ ] Run value parity verifiers for implemented families.
[ ] Keep SAR/S1 and PAN recovery separate until exact contracts are clear.
```

## Important boundary

The inventory comparator:

```text
- reads manifest.local.json;
- scans app output file names;
- writes only a local report if requested;
- does not read artifact file contents;
- does not expose or commit private reference files;
- does not prove notebook-value parity.
```

## Step 1 — run unit tests

```powershell
cd C:\Dev\New_GEE
python -m pytest tests/unit/test_d1_compare_app_reference_inventory.py -q
```

## Step 2 — run the safe local inventory comparison

Use the frozen D1 manifest and the app run folder that produced the current candidate outputs:

```powershell
python scripts/d1_compare_app_reference_inventory.py `
  --reference-manifest data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/manifest.local.json `
  --app-output-dir data/runs/a11309bf-ed47-4bf5-bbf4-f755b904065c `
  --report data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/parity_inventory.local.json
```

Expected safe output shape:

```text
status: passed OR incomplete
reference_artifact_count: 109
app_file_count: <local count>
matched_reference_name_count: <local count>
missing_reference_name_count: <local count>
note: inventory-only; not notebook-value parity
```

## Step 3 — validate Git safety

```powershell
git status --short
```

Expected: no files under `data/private_references/` appear.

Existing unrelated local Git noise should stay separate and should not be mixed into parity work.

## Done condition for this slice

```text
[ ] D1 inventory comparator tests pass locally.
[ ] Inventory comparator runs locally against the frozen D1 manifest.
[ ] Local inventory report is written only under data/private_references/.
[ ] git status does not show data/private_references/ files.
```

## Next step after inventory bridge

Move from inventory-only to verifier-backed parity:

```text
[ ] Choose the first implemented family to verify by value.
[ ] Prefer DEM/report/private semantic first.
[ ] Keep SAR/S1 source recovery separate.
[ ] Keep PAN recovery/build separate.
[ ] Do not claim final notebook-value parity until value comparators pass.
```
