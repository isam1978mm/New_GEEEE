# Real App-vs-Reference Parity — Operator Steps

## Current status

Real app-vs-reference parity is **inventory bridge passed; DEM value parity ready for local run**.

D1 local reference freeze is complete outside Git. The safe inventory bridge passed against the current app output folder.

The first value slice is DEM value parity:

```text
scripts/d1_compare_dem_value_parity.py
```

## Checklist item from LOCAL_PRIVATE_ROADMAP_CHECKLIST.md

```text
10. Real app-vs-reference parity
Status: Inventory bridge passed / DEM value parity ready for local run
```

## Checklist of the item

```text
[x] D1 frozen local reference exists outside Git.
[x] Add safe D1 inventory comparator: scripts/d1_compare_app_reference_inventory.py.
[x] Add unit coverage for the D1 inventory comparator.
[x] Run inventory comparison locally.
[x] Add DEM value parity wrapper: scripts/d1_compare_dem_value_parity.py.
[x] Add unit coverage for the DEM value parity wrapper.
[ ] Run DEM value parity locally.
[ ] Build/verify the app output manifest against the frozen notebook reference manifest.
[ ] Run remaining value parity verifiers for implemented families.
[ ] Keep SAR/S1 and PAN recovery separate until exact contracts are clear.
```

## Important boundary

The inventory comparator checks file-name presence only. It does not prove notebook-value parity.

The DEM value comparator reads DEM raster values locally and reports safe metrics only. It proves DEM value parity only, not full notebook parity.

## Completed inventory step

Unit test result:

```text
3 passed, 1 pytest cache warning
```

Inventory result:

```text
status: passed
reference_artifact_count: 109
app_file_count: 449
matched_reference_name_count: 109
missing_reference_name_count: 0
note: inventory-only; not notebook-value parity
```

## Step 1 — DEM value parity unit tests

```powershell
cd C:\Dev\New_GEE
python -m pytest tests/unit/test_d1_compare_dem_value_parity.py -q
```

## Step 2 — DEM value parity local run

```powershell
python scripts/d1_compare_dem_value_parity.py `
  --app-output-dir data/runs/a11309bf-ed47-4bf5-bbf4-f755b904065c `
  --reference-dem-root data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/artifacts/dem `
  --report data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/dem_value_parity.local.json
```

Expected safe output shape:

```text
status: passed OR failed OR incomplete OR comparison_unavailable
pass_count: <local count>
fail_count: <local count>
missing_count: <local count>
dem_matches: True OR False
note: DEM value parity only; not full notebook parity
```

## Step 3 — Git safety

```powershell
git status --short
```

Expected: no files under `data/private_references/` appear.

Existing unrelated local Git noise should stay separate and should not be mixed into parity work:

```text
frontend-v2/dist changes
frontend-v2/test-results/
graphify-out/
.pytest-tmp-* folders
```

## Done condition for DEM value slice

```text
[ ] DEM value comparator tests pass locally.
[ ] DEM value comparator runs locally against the frozen D1 DEM root.
[ ] Local DEM report is written only under data/private_references/.
[ ] git status does not show data/private_references/ files.
[ ] DEM value parity status is recorded.
```

## Next step after DEM value parity

Move to the next implemented family only after DEM is recorded:

```text
[ ] Choose report or private semantic next.
[ ] Keep SAR/S1 source recovery separate.
[ ] Keep PAN recovery/build separate.
[ ] Do not claim final notebook-value parity until all required value comparators pass.
```
