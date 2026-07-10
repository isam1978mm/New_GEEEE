# Local Private Roadmap Checklist

Status document for the current private/local app workflow.

This app is currently private and local operator-only. There is no SaaS mode, no public user workflow, and no VPS deployment planned soon.

User-facing package wording should use:

```text
Paid Imagery Export Package
```

Internal `V6` / `v6_*` paths, filenames, generated package names, and API compatibility names should stay unchanged for now unless a dedicated migration plan is created.

## Current milestone status

```text
[x] D1 real new.ipynb reference freeze is complete.
[x] Frozen reference bundle remains local/private and outside Git.
[x] Real app-vs-reference inventory coverage passed for the accepted scope.
[x] Required D1 value-parity families passed: DEM, report, private semantic, SAR/S1, PAN.
[x] Paid Imagery Export Package app flow implemented.
[x] Paid Imagery Export Package audit reliability/provenance/raster hardening completed.
[x] Browser package panel remains metadata-only.
[ ] H3/H4 dataset readiness remains blocked until a positive independent-evidence source passes the existing Slice 13/I1/I2 path.
```

## Paid Imagery Export Package

- [x] Visible/user-facing name is `Paid Imagery Export Package`.
- [x] App UI/backend flow implemented.
- [x] Generate / review metadata / retrieve ZIP exists.
- [x] Package readiness is validation-gated.
- [x] ZIP/report generations are paired by token.
- [x] Package provenance, score basis, geometry basis, fallback labels, and placeholder-map labels are recorded.
- [x] Metadata-only browser behavior.
- [x] Keep internal compatibility names unchanged.
- [x] Do not rename `private/v6/` yet.
- [x] Do not rename backend/API compatibility names yet.
- [x] Do not rename generated file schema just for UI wording.

Plain meaning: make the visible name understandable, while keeping existing internal V6 files and paths stable.

## External V6 notebook/source-lock/package track

- [ ] Status: unresolved / separate from `new.ipynb` parity.
- [ ] Keep separate from D1/new.ipynb reference work.
- [ ] Do not claim frozen external V6 notebook parity from the app package alone.
- [ ] Reopen only after the operator supplies the separate originating V6 notebook/export source or a verified frozen package.

Plain meaning: the app package flow is active and hardened, but the external V6 notebook/source-lock proof is still separate and unresolved.

## H3/H4 dataset readiness

- [ ] Status: blocked on positive independent evidence.
- [x] Reuse the existing I1/I2 readiness contract and existing `dataset_pack_readiness` validator.
- [x] Do not create a duplicate H3/H4 contract.
- [x] Do not create a duplicate readiness validator.
- [x] Do not start real H3 training yet.
- [x] Do not start real H4 private inference yet.
- [ ] Complete C01 operator/source-specific answer, or provide another positive independent-evidence source.
- [ ] Re-review C01 or the new positive source through all six gates.
- [ ] Shape approved labels into the existing I1/I2 training-example schema outside Git only.
- [ ] Run the existing dataset-pack readiness validator.
- [ ] Require `ready_for_private_training_later` before opening H3 training.

Plain meaning: D1 proves app output reproduction. It does not by itself approve real ML training or private inference.

## Public/shared/deployment work

Later only:

```text
[ ] VPS/private operator auth activation
[ ] Public overlay exposure review
[ ] Public location-bearing downloads
[ ] Production deployment hardening
[ ] External provider ordering/payment integration
```

These are not current blockers for the private/local app.
