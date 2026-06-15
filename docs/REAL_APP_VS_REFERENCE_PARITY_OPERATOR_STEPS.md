# Real App-vs-Reference Parity — Operator Steps

## Current status

Real app-vs-reference parity is **inventory bridge passed, value parity not proven**.

D1 local reference freeze is complete outside Git. The safe inventory bridge confirms the frozen D1 manifest can be compared against the current app output folder without reading artifact contents.

## Checklist item from LOCAL_PRIVATE_ROADMAP_CHECKLIST.md

```text
10. Real app-vs-reference parity
Status: Inventory bridge passed / value parity not proven
```

## Checklist of the item

```text
[x] D1 frozen local reference exists outside Git.
[x] Add safe D1 inventory comparator: scripts/d1_compare_app_reference_inventory.py.
[x] Add unit coverage for the D1 inventory comparator.
[x] Run inventory comparison locally.
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

## Step 1 — unit tests

Command:

```powershell
cd C:\Dev\New_GEE
python -m pytest tests/unit/test_d1_compare_app_reference_inventory.py -q
```

Result:

```text
3 passed, 1 pytest cache warning
```

The warning was local `.pytest_cache` permission noise, not a comparator failure.

## Step 2 — safe local inventory comparison

Command:

```powershell
python scripts/d1_compare_app_reference_inventory.py `
  --reference-manifest data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/manifest.local.json `
  --app-output-dir data/runs/a11309bf-ed47-4bf5-bbf4-f755b904065c `
  --report data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/parity_inventory.local.json
```

Safe result:

```text
status: passed
reference_artifact_count: 109
app_file_count: 449
matched_reference_name_count: 109
missing_reference_name_count: 0
note: inventory-only; not notebook-value parity
```

## Step 3 — Git safety

`git status --short` did not show `data/private_references/` files.

Existing unrelated local Git noise should stay separate and should not be mixed into parity work:

```text
frontend-v2/dist changes
frontend-v2/test-results/
graphify-out/
.pytest-tmp-* folders
```

## Done condition for this slice

```text
[x] D1 inventory comparator tests pass locally.
[x] Inventory comparator runs locally against the frozen D1 manifest.
[x] Local inventory report is written only under data/private_references/.
[x] git status does not show data/private_references/ files.
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
