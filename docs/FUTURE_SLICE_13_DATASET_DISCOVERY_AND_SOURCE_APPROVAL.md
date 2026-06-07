# Future Slice 13 — Dataset Discovery and Source Approval for H3/H4

## Scope

Future Slice 13 is dataset discovery and source-approval policy only. It defines how
candidate datasets for future H3 baseline training and H4 private inference are
found, vetted, and either rejected or routed to the I2 validator.

Slice 13 does not create or commit a dataset. It does not download data or weights.
It does not scrape the web into the repo. It does not train. It does not run
inference. It does not add ML dependencies. It does not call Earth Engine. It does
not generate rasters, NPY files, or map artifacts. It does not change raster, math,
or classifier runtime logic. It does not expose overlays or coordinates publicly.

It is the missing precondition before H3/H4: the next blocker is data discovery and
approval, not code.

## Relationship To Existing Gates

The binding gates remain in `docs/ML_DATA_TRAINING_READINESS_PLAN.md`. The dataset
contract remains in `docs/SPECIAL_TRACK_I_DATASET_TRAINING_DESIGN.md`. The
machine-checkable validator remains `app/pipeline/parity/dataset_pack_readiness.py`
(Future Slice 08 / I2). Where wording differs, the strictest gate applies.

Slice 13 sits *before* I2: it decides whether a candidate is even allowed to be
assembled into a private dataset pack and handed to the I2 validator. I2 then decides
`ready_for_private_training_later`. Only after that can an H3 training slice be opened,
and only after H3 beats the Phase F baseline by the preregistered margin on the
untouched holdout can H4 private inference be opened.

```text
candidate source
  -> Slice 13 discovery + source approval   (this doc)
  -> I2 dataset-pack validator              (dataset_pack_readiness.py)
  -> H3 baseline training                   (blocked until I2 = ready_for_private_training_later)
  -> H4 private CLI inference               (blocked until H3 beats Phase F baseline gate)
```

No dataset is approved just because it is published, public, or cited.

## Candidate Lifecycle

Every candidate dataset starts as `unverified_lead`. It may only advance one state at
a time, and any gate failure sends it to `rejected`.

```text
unverified_lead
  -> under_review
  -> rejected
     | conditionally_approved_for_I2
        -> (I2 validator) ready_for_private_training_later | not_ready | ...
```

`conditionally_approved_for_I2` is not training approval. It only means the candidate
cleared the Slice 13 gates and may be assembled, outside git, into a pack for the I2
validator. Training stays blocked until I2 returns `ready_for_private_training_later`.

## Rejection Gates (Ordered)

Reject immediately if any gate fails. Sensitivity/misuse is evaluated first and can
reject a candidate on its own, before license or validator-fit are even considered.

1. **Sensitivity / misuse review (first, standalone reject).**
   If the dataset reveals sensitive locations — for example coordinates of preserved
   or undefended sites whose exposure would enable harm — it can be rejected here
   regardless of license or quality. A dataset whose labels *are* sensitive
   coordinates raises the misuse bar to maximum and must not produce any
   coordinate-bearing output. This gate ranks first by design.
2. **Independent-evidence review.**
   Labels must be independent of our heuristic AND independent of the same input
   stack being modeled. See the definition below. Imagery-derived labels on a stack
   similar to ours do not qualify as independent evidence.
3. **Provenance / labeling-method review.**
   The source must document how labels were produced. Unclear or undocumented
   labeling method fails this gate. An abstract is not a methods section.
4. **License / access-terms review.**
   Source, license, version, and access terms must be acceptable and recorded with a
   content hash. Unlicensed, unclear, or non-redistributable terms fail this gate.
5. **Storage / redaction review.**
   The candidate must be storable as `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY`, outside
   git, with `http_servable=false`, `frontend_visible=false`,
   `downloadable_via_api=false`, and a redaction policy for any coordinate proxies. A
   candidate that cannot satisfy this fails.
6. **I2 validator compatibility.**
   The candidate must be expressible in the I1 dataset-manifest and
   training-example schema so the I2 validator can evaluate it. If it cannot be
   shaped into a valid pack, it fails.

## Key Definition

```text
independent evidence =
  independent of our heuristic
  AND independent of the same input stack being modeled
```

A different sensor (for example PlanetScope versus our Sentinel/Landsat/S1-SAR/DEM
stack) helps the input-stack axis but does not by itself satisfy independence. If the
labels were produced by visual interpretation of imagery similar to ours, they remain
correlated with the prediction target and are not reviewed-tier evidence on their own.

## Candidate Register (External, Not Committed)

Discovery findings, candidate provenance, license notes, and review decisions are
recorded in a private candidate register kept **outside git** under the operator's
private dataset root, alongside the eventual I2 pack. This doc does not store the
register. No coordinates, local paths, private hashes, or raw site labels appear in
any committed file or public summary.

## Illustrative Worked Examples (Unverified Leads — Not Approved)

These public, cited datasets are recorded here only to demonstrate the gates biting.
Listing a citation is not approval. Both remain `unverified_lead` and would require
the full Slice 13 review before any assembly into an I2 pack.

- `arXiv:2602.19608` — satellite-based looted-site detection; ~1,943 Afghanistan
  sites (looted and preserved), PlanetScope ~4.7 m, multi-year imagery.
  - Gate 1 (sensitivity): maximal — preserved-site coordinates are misuse-sensitive.
    Likely binding on its own.
  - Gate 2 (independence): different sensor helps the input-stack axis; the
    labeling method must be confirmed independent of imagery interpretation.
  - Gate 3 (provenance): label-production method not establishable from the abstract.
- `arXiv:2409.09432` / DAFA-LS (public repository) — satellite image time series for
  looting detection; ~675 Afghan sites, multi-year monthly imagery.
  - Gate 1 (sensitivity): same maximal concern as above.
  - Gate 4 (license): public repository makes license and method checkable, which is
    a precondition, not approval.

Status for both: `unverified_lead`. No download, assembly, training, or inference is
authorized by this listing.

## Safety Boundary

Future Slice 13 does not:

- create, download, scrape, or commit a dataset, chips, labels, or coordinate-bearing metadata
- train a model or run inference
- download model weights
- add PyTorch, TensorFlow, CUDA, or other heavy ML dependencies
- generate rasters, NPY files, or map artifacts
- call Earth Engine or start backend runs
- change raster, math, or classifier runtime logic
- connect any output to API or frontend
- expose public overlays, coordinates, or change artifact-serving policy
- implement H2, H3, H4, or G2 work

## Stop Conditions

Discovery does not advance a candidate past `under_review` if:

- sensitivity / misuse risk is unacceptable
- labels are not independent of our heuristic and its input stack
- labeling method / provenance is unclear
- license / access terms are unacceptable
- storage/redaction cannot satisfy `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY`
- it cannot be shaped into a valid I2 pack

If no candidate passes all gates, training stays blocked and private inference stays
blocked. H3 and H4 remain unopened.
