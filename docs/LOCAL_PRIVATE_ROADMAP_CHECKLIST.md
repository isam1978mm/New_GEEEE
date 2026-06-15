# Local Private Roadmap Checklist

Status document for the current private/local app workflow.

This app is currently private and local operator-only.
There is no SaaS mode, no public user workflow, and no VPS deployment planned soon.

User-facing V6 wording should use the meaningful name `Paid Imagery Request Package`, but internal `v6` paths, filenames, and API compatibility should stay unchanged for now.

## Current milestone status

```text
[x] D1 real new.ipynb reference freeze is complete.
[x] Frozen reference bundle remains local/private and outside Git.
[x] Real app-vs-reference inventory coverage passed: 126/126 reference names matched.
[x] Required D1 value-parity families passed: DEM, report, private semantic, SAR/S1, PAN.
[x] SAR/S1 recovery/build is complete for the D1 parity scope.
[x] PAN recovery/build is complete for the D1 parity scope.
[x] Slice 13 current known-lead set is closed out.
[ ] H3/H4 dataset readiness remains blocked until a new independent-evidence source passes the existing Slice 13/I1/I2 path.
```

## Counting note

This checklist has 13 unique points.

`H3 training / H4 private inference` appears in both:

- Not done / still open #5
- Blocked #4

It is the same underlying issue, so it is counted once as unique point #5.

---

## 1. V6 names correction

- [x] **Status:** Done / locally E2E tested
- [x] Rename user-facing wording from `V6 package` to `Paid Imagery Request Package`.
- [x] Use user-facing label: `Paid Imagery Request Package`.
- [x] Use button/action wording: `Generate request package`.
- [x] Use button/action wording: `Review package metadata`.
- [x] Use button/action wording: `Retrieve package ZIP`.
- [x] Keep internal compatibility names unchanged.
- [x] Do not rename `private/v6/`.
- [x] Do not rename backend/API compatibility names yet.
- [x] Do not rename generated file schema just for the UI wording change.
- [x] Local E2E validation: `npm run e2e:v6` -> 9 passed.

Current status: visible UI naming is corrected, local E2E passed, and internal V6 compatibility names remain unchanged.

Plain meaning: make the visible name understandable, while keeping existing internal V6 files and paths stable.

---

# Not done / still open

## 2. VPS/private operator auth activation

- [ ] **Status:** Later / not now
- [ ] Keep this out of the immediate task list.
- [ ] Revisit only when VPS deployment is actually planned.

Plain meaning: this is mainly deployment setup. Local private operator mode is acceptable for now.

## 3. Frozen new.ipynb reference bundle outside Git

- [x] **Status:** Done as part of D1 local freeze
- [x] Collect real `new.ipynb` output files privately.
- [x] Keep the bundle outside Git.
- [x] Do not commit real reference files, generated artifacts, ZIP contents, or private payloads.
- [x] Local frozen bundle finalized with 126 artifacts across 5 families.
- [x] Local manifest validation passed with `Summary: OK`.
- [x] `git status --short` did not show private reference files.

Plain meaning: these private notebook outputs are now the local truth copy that the app must match.

## 4. Public overlay exposure review

- [ ] **Status:** Not needed now / future only
- [ ] Do not prioritize this for the private/local app.
- [ ] Revisit only if the app becomes shared, public, or SaaS-like later.

Plain meaning: because the app is private and only for Maher/operator, public exposure review is not current work.

## 5. H3 training / H4 private inference

- [ ] **Status:** Blocked / biggest remaining issue
- [x] Reuse the existing I1/I2 readiness contract and existing `dataset_pack_readiness` validator.
- [x] Do not create a duplicate H3/H4 contract.
- [x] Do not create a duplicate readiness validator.
- [x] Complete the current known-lead Slice 13 source-review closeout.
- [x] Do not start real H3 training yet.
- [x] Do not start real H4 private inference yet.
- [ ] First obtain or define a new independent-evidence source that can pass the existing Slice 13 gates.
- [ ] Shape approved labels into the existing I1/I2 training-example schema outside Git only.
- [ ] Run the existing dataset-pack readiness validator.
- [ ] Require `ready_for_private_training_later` before opening H3 training.

Plain meaning: D1 proves app output reproduction. Current known leads did not pass Slice 13. H3/H4 still need approved independent evidence; app candidates or D1 layers alone are not training truth.

## 6. D1 real new.ipynb reference freeze

- [x] **Status:** Done / local private reference frozen outside Git
- [x] Add local bundle initializer: `scripts/d1_init_reference_bundle.py`.
- [x] Add local bundle finalizer: `scripts/d1_finalize_reference_bundle.py`.
- [x] Add operator steps: `docs/D1_NEW_IPYNB_REFERENCE_FREEZE_OPERATOR_STEPS.md`.
- [x] Add unit coverage for the local bundle initializer/finalizer.
- [x] Local validation: D1 initializer/finalizer/manifest tests -> 30 passed, 1 pytest cache warning.
- [x] Local bundle skeleton created.
- [x] Freeze the real `new.ipynb` outputs as the official private notebook baseline.
- [x] Keep the frozen reference outside Git.
- [x] Use this as the baseline for later parity checks.
- [x] Finalized local manifest with 126 artifact paths across 5 families.
- [x] Strict manifest validation passed with `Summary: OK`.
- [x] `git status --short` did not show private reference files.

Current status: D1 local private baseline is frozen outside Git and the required app parity families have passed against it.

Plain meaning: the exact private notebook outputs are now the official local reference bundle.

## 7. DEM/report/private semantic/SAR/PAN parity verification

- [x] **Status:** Done for the required D1 value-parity families
- [x] Do not claim byte-for-byte parity for every manifest artifact.
- [x] Compare app outputs against frozen notebook outputs.
- [x] Add DEM value parity wrapper: `scripts/d1_compare_dem_value_parity.py`.
- [x] Add unit coverage for DEM value parity wrapper.
- [x] Local DEM value comparator tests passed.
- [x] Run DEM value parity locally.
- [x] DEM value parity status: passed.
- [x] Add report value parity wrapper: `scripts/d1_compare_report_value_parity.py`.
- [x] Add unit coverage for report value parity wrapper.
- [x] Run report value parity locally.
- [x] Report value parity status: passed.
- [x] Add private semantic value parity wrapper.
- [x] Align private semantic expected outputs to the secret-layer contract.
- [x] Run private semantic value parity locally.
- [x] Private semantic value parity status: passed.
- [x] Recover and capture SAR/S1 expected outputs privately.
- [x] Export matching app-side SAR/S1 notebook-compatible outputs.
- [x] Run SAR/S1 parity locally.
- [x] SAR/S1 value parity status: passed.
- [x] Recover and capture PAN expected outputs privately.
- [x] Export matching app-side PAN notebook-compatible outputs.
- [x] Run PAN parity locally.
- [x] PAN value parity status: passed.

Plain meaning: DEM, report, private semantic secret layers, SAR/S1, and PAN are proven for the frozen local D1 baseline. This does not assert byte-for-byte parity for every one of the 126 manifest artifacts.

---

# Parked

## 8. D1/D2/D3 operator-only private preview artifacts

- [ ] **Status:** Parked
- [ ] Keep parked as GitHub issue #2.
- [ ] Do not reopen unless Maher explicitly asks.

Plain meaning: the private preview/export artifact work is paused on purpose.

## 9. External V6 notebook/source-lock/package track

- [ ] **Status:** Parked
- [ ] Keep separate from `new.ipynb` parity.
- [ ] Do not mix this with D1/new.ipynb reference work.
- [ ] Keep the current working V6 package flow intact.

Plain meaning: V6 app package flow is working, but external V6 notebook/source-lock proof is separate and paused.

---

# Completed after D1 parity closeout

## 10. Real app-vs-reference parity

- [x] **Status:** Done for the D1 accepted scope
- [x] Start only after the frozen `new.ipynb` reference exists.
- [x] Add safe inventory comparator: `scripts/d1_compare_app_reference_inventory.py`.
- [x] Add unit coverage for the inventory comparator.
- [x] Add operator steps: `docs/REAL_APP_VS_REFERENCE_PARITY_OPERATOR_STEPS.md`.
- [x] Local inventory comparator tests passed.
- [x] Local inventory comparison against the frozen D1 manifest passed.
- [x] Inventory summary: 126 reference artifacts, 126 matched reference names, 0 missing reference names.
- [x] Required value parity passed for DEM, report, private semantic, SAR/S1, and PAN.

Plain meaning: the app run contains all 126 reference filenames, and the required D1 value-parity families passed. This is not a claim of byte-for-byte parity for every artifact.

## 11. SAR/S1 recovery/build

- [x] **Status:** Done for the D1 parity scope
- [x] Do not guess SAR/S1 outputs.
- [x] Recover exact Sentinel-1 expected output contract before building.
- [x] Capture expected SAR/S1 reference outputs privately.
- [x] Export matching app-side SAR/S1 notebook-compatible outputs.
- [x] Run SAR/S1 contract readiness check.
- [x] Run SAR/S1 value parity.
- [x] SAR/S1 value parity passed.

Plain meaning: the app reproduced the notebook-compatible SAR/S1 outputs needed for D1 parity without changing production SAR math.

## 12. PAN recovery/build

- [x] **Status:** Done for the D1 parity scope
- [x] Recover exact PAN/optical notebook output expectations.
- [x] Capture expected PAN reference outputs privately.
- [x] Build the matching app writer/recovery path only after the expected output is clear.
- [x] Export matching app-side PAN notebook-compatible outputs.
- [x] Run PAN component parity.
- [x] Run PAN stack parity.
- [x] PAN value parity passed.

Plain meaning: the app reproduced the notebook-compatible PAN outputs needed for D1 parity without aliasing unrelated optical outputs.

---

# Blocked

## Blocked #4. H3/H4

- [ ] **Status:** Same blocker as point #5, not a new unique point
- [x] Treat as the same issue as `H3 training / H4 private inference`.
- [x] Reuse the existing I1/I2 contract and dataset-pack readiness validator.
- [x] Complete the existing Slice 13 source-review path for current known leads.
- [x] Review the second known lead through the six gates.
- [x] Close out Slice 13 by recording that all current known leads are rejected/deferred.
- [x] Do not start training or inference until the existing validator allows it.
- [ ] Find or provide a new independent-evidence source that can pass Slice 13.

Plain meaning: this is the same real ML blocker. No approved independent-evidence source means no real training and no private inference.

## 13. Public location-bearing downloads

- [ ] **Status:** Not needed now for private local app / blocked only for public or shared mode
- [ ] Private operator files are okay when kept private.
- [ ] Do not expose sensitive downloads publicly.
- [ ] Revisit only if the app becomes shared/public later.

Plain meaning: this is not a current blocker for Maher-only private local use. It matters only for public/shared exposure.

---

# Immediate order

- [x] 1. V6 names correction.
- [x] 2. D1 real `new.ipynb` reference freeze.
- [x] 3. Frozen `new.ipynb` reference bundle outside Git.
- [x] 4. Real app-vs-reference parity for the D1 accepted scope.
- [x] 5. DEM/report/private semantic/SAR/PAN parity verification.
- [x] 6. PAN recovery/build.
- [x] 7. SAR/S1 recovery/build.
- [ ] 8. H3/H4 dataset readiness.
- [ ] 9. VPS/private operator auth activation later.
- [ ] 10. Public overlay exposure review future-only.
- [ ] 11. Public location-bearing downloads future-only for public/shared mode.
- [ ] 12. D1/D2/D3 private preview artifacts remain parked.
- [ ] 13. External V6 notebook/source-lock/package track remains parked.

---

# Do not do now

- Do not prioritize VPS deployment.
- Do not build SaaS/public auth.
- Do not prioritize public overlay exposure review.
- Do not expose sensitive downloads publicly.
- Do not rename internal `v6` paths/files/API names yet.
- Do not mix external V6 notebook/source-lock work with `new.ipynb` parity.
- Do not reopen D1/D2/D3 private preview artifacts unless Maher explicitly asks.
- Do not commit private reference bundles, generated ZIPs, or private generated artifacts.
- Do not create a duplicate H3/H4 dataset-readiness contract.
- Do not create a duplicate H3/H4 readiness validator.
- Do not start H3 training or H4 private inference until the existing readiness validator allows it.
