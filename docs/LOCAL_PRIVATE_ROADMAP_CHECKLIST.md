# Local Private Roadmap Checklist

Status document for the current private/local app workflow.

This app is currently private and local operator-only.
There is no SaaS mode, no public user workflow, and no VPS deployment planned soon.

User-facing V6 wording should use the meaningful name `Paid Imagery Request Package`, but internal `v6` paths, filenames, and API compatibility should stay unchanged for now.

## Counting note

This checklist has 13 unique points.

`H3 training / H4 private inference` appears in both:

- Not done / still open #4
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

- [ ] **Status:** Open / high priority after V6 names correction
- [ ] Collect real `new.ipynb` output files privately.
- [ ] Keep the bundle outside Git.
- [ ] Do not commit real reference files, generated artifacts, ZIP contents, or private payloads.

Plain meaning: these private notebook outputs become the truth copy that the app must match.

## 4. Public overlay exposure review

- [ ] **Status:** Not needed now / future only
- [ ] Do not prioritize this for the private/local app.
- [ ] Revisit only if the app becomes shared, public, or SaaS-like later.

Plain meaning: because the app is private and only for Maher/operator, public exposure review is not current work.

## 5. H3 training / H4 private inference

- [ ] **Status:** Blocked / biggest issue
- [ ] Do not start real training yet.
- [ ] Do not start real private inference yet.
- [ ] First define or obtain an approved real dataset.

Plain meaning: no approved real dataset means no honest real ML training or private inference.

## 6. D1 real new.ipynb reference freeze

- [ ] **Status:** Open / high priority
- [ ] Freeze the real `new.ipynb` outputs as the official private notebook baseline.
- [ ] Keep the frozen reference outside Git.
- [ ] Use this as the baseline for later parity checks.

Plain meaning: decide which exact private notebook outputs are the official reference.

## 7. DEM/report/private semantic/SAR/PAN parity verification

- [ ] **Status:** Blocked until D1 freeze
- [ ] Do not attempt final parity verification before D1 freeze exists.
- [ ] After D1 freeze, compare app outputs against frozen notebook outputs.
- [ ] Verify DEM outputs.
- [ ] Verify report outputs.
- [ ] Verify private semantic outputs.
- [ ] Verify SAR/PAN outputs only after their expected contracts are clear.

Plain meaning: the app cannot prove it matches the notebook until the frozen notebook reference exists.

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

# Blocked

## 10. Real app-vs-reference parity

- [ ] **Status:** Blocked until D1 freeze
- [ ] Start only after the frozen `new.ipynb` reference exists.
- [ ] Then prove the app-generated outputs match the notebook reference with tests/verifiers.

Plain meaning: D1 freeze unlocks this work, but tests still need to prove the match.

## 11. SAR/S1 recovery/build

- [ ] **Status:** Blocked until D1 freeze + exact radar source recovery
- [ ] Do not guess SAR/S1 outputs.
- [ ] Recover exact Sentinel-1 inputs, dates, bands, filters, grid, metadata, writer paths, and expected output files first.

Plain meaning: the app must reproduce the notebook radar outputs, but only after the exact source/output contract is known.

## 12. PAN recovery/build

- [ ] **Status:** Blocked / big issue
- [ ] Recover exact PAN/optical notebook output expectations.
- [ ] Build the matching app writer/recovery path only after the expected output is clear.
- [ ] Verify against frozen references later.

Plain meaning: the app still needs to reproduce the notebook PAN/optical outputs. This is one of the larger technical gaps.

## Blocked #4. H3/H4

- [ ] **Status:** Same blocker as point #5, not a new unique point
- [ ] Treat as the same issue as `H3 training / H4 private inference`.
- [ ] Solve dataset readiness first.

Plain meaning: this is the same real ML blocker. No approved real dataset means no real training and no private inference.

## 13. Public location-bearing downloads

- [ ] **Status:** Not needed now for private local app / blocked only for public or shared mode
- [ ] Private operator files are okay when kept private.
- [ ] Do not expose sensitive downloads publicly.
- [ ] Revisit only if the app becomes shared/public later.

Plain meaning: this is not a current blocker for Maher-only private local use. It matters only for public/shared exposure.

---

# Immediate order

- [x] 1. V6 names correction.
- [ ] 2. D1 real `new.ipynb` reference freeze.
- [ ] 3. Frozen `new.ipynb` reference bundle outside Git.
- [ ] 4. Real app-vs-reference parity.
- [ ] 5. DEM/report/private semantic/SAR/PAN parity verification.
- [ ] 6. PAN recovery/build.
- [ ] 7. SAR/S1 recovery/build.
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
- Do not reopen D1/D2/D3 preview artifacts unless Maher explicitly asks.
- Do not commit private reference bundles, generated ZIPs, or private generated artifacts.
