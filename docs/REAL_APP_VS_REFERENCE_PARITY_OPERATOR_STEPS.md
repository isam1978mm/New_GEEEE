# Real App-vs-Reference Parity — Operator Steps

## Current status

Real app-vs-reference parity is **DEM value parity passed; remaining families open**.

D1 local reference freeze is complete outside Git. The inventory bridge passed, and the first value slice, DEM, passed locally.

## Checklist item from LOCAL_PRIVATE_ROADMAP_CHECKLIST.md

```text
10. Real app-vs-reference parity
Status: DEM value parity passed / remaining families open
```

## Checklist of the item

```text
[x] D1 frozen local reference exists outside Git.
[x] Add safe D1 inventory comparator.
[x] Add unit coverage for the D1 inventory comparator.
[x] Run inventory comparison locally.
[x] Add DEM value parity wrapper.
[x] Add unit coverage for the DEM value parity wrapper.
[x] Run DEM value parity locally.
[ ] Build/verify the app output manifest against the frozen notebook reference manifest.
[ ] Run remaining value parity verifiers for implemented families.
[ ] Keep SAR/S1 and PAN recovery separate until exact contracts are clear.
```

## Completed inventory step

```text
unit tests: 3 passed, 1 pytest cache warning
status: passed
reference_artifact_count: 109
app_file_count: 449
matched_reference_name_count: 109
missing_reference_name_count: 0
```

## Completed DEM value step

```text
unit tests: 4 passed, 1 pytest cache warning
status: passed
pass_count: 4
fail_count: 0
missing_count: 0
dem_matches: True
```

The DEM report was written only to ignored local storage. Git status did not show those files.

Existing unrelated local Git noise should stay separate and should not be mixed into parity work.

## Done condition for DEM value slice

```text
[x] DEM value comparator tests pass locally.
[x] DEM value comparator runs locally.
[x] Local DEM report is written only under ignored local storage.
[x] Git status does not show ignored local reference files.
[x] DEM value parity status is recorded.
```

## Next step after DEM value parity

```text
[ ] Choose report or private semantic next.
[ ] Keep SAR/S1 source recovery separate.
[ ] Keep PAN recovery/build separate.
[ ] Do not claim final notebook-value parity until all required value comparators pass.
```
