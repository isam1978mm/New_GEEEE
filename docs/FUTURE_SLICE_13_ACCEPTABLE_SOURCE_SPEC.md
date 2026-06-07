# Future Slice 13 — Gate-1-Acceptable Operator-Provided Independent-Evidence Source Spec

Design-only. This spec defines the minimum a candidate data source must satisfy to
have a real chance of clearing Slice 13 review — especially Gate 1 (sensitivity /
misuse), the gate that rejected both known public looting-site leads
(`arXiv:2602.19608` and `arXiv:2409.09432` / DAFA-LS).

This document authorizes nothing. It does not acquire data, create a dataset,
download, scrape, label, train, run inference, add ML dependencies, or expose
anything. It only describes what a source must be **before** a Slice 13 review begins.

## Relationship To Existing Slice 13 Artifacts

```text
docs/FUTURE_SLICE_13_DATASET_DISCOVERY_AND_SOURCE_APPROVAL.md  (governance contract)
docs/FUTURE_SLICE_13_EXECUTION_CHECKLIST.md                    (operator-facing run plan)
app/pipeline/parity/dataset_source_review.py                   (gate review logic)
app/pipeline/parity/dataset_source_sensitivity_decision.py     (Gate 1 decision logic)
app/pipeline/parity/dataset_source_candidate_register.py       (register scaffold)
app/pipeline/parity/dataset_source_approval_closeout.py        (closeout logic)
```

Where this spec and the gate definitions in the governance contract or review modules
differ, the stricter wording applies. The authoritative I1/I2 schema remains
`app/pipeline/parity/dataset_pack_readiness.py` and
`docs/SPECIAL_TRACK_I_DATASET_TRAINING_DESIGN.md`.

## 0. The One-Line Test

```text
A source is worth entering into Slice 13 only if its labels are not, and cannot
become, a targeting map of vulnerable sites — AND its labels were produced
independently of our heuristic and its input stack.
```

If either half fails, do not open a review.

## 1. Gate 1 — Sensitivity / Misuse (binding)

A source is Gate-1-acceptable only if all of the following hold:

```text
[ ] The operator is authorized to use the data for this purpose
    (ownership, data-use agreement, or authoritative permission on file).
[ ] Exact coordinates/footprints/masks can be reduced to redacted proxies
    (area_id / group_id / chip_id) BEFORE any model-facing use.
[ ] Raw coordinates never leave LOCAL_SENSITIVE storage and never appear in any
    model output, DTO, log, summary, or artifact.
[ ] Even a perfectly working model cannot act as a "where to act" map:
    output stays probability/score + neutral label, CLI-only, no geometry.
[ ] The labels' value is NOT primarily "the locations themselves."
```

Reject at Gate 1 if the dataset's worth is the sensitive coordinates and redaction
cannot neutralize the misuse vector.

Lower-risk source shapes that tend to pass Gate 1:

```text
- Operator-owned field-survey records the operator is licensed to use.
- Authoritative heritage/government records under a data-use agreement, where
  exposure risk is already managed and coordinates are redactable.
- Already-public-or-destroyed sites only if a written sensitivity/misuse rationale
  says exposure adds no new risk.
- Non-sensitive land-cover / terrain / background reference data
  (useful for negatives and hard negatives).
```

A published, licensed, or public source can still be rejected at Gate 1.

## 2. Gate 2 — Independent Evidence

```text
independent of our heuristic
AND independent of the same input stack being modeled
```

```text
[ ] Labels were produced by a method other than our pipeline's output.
[ ] Labels are NOT merely visual interpretation of the same
    Sentinel / Landsat / S1-SAR / DEM / Phase-C signal.
[ ] Evidence type is one of:
       field_validation
       authoritative_external_dataset
       expert_adjudication_independent_evidence
       independently_produced_reference
[ ] NOT acceptable as sole evidence:
       unknown_or_missing, weak_heuristic_hint, synthetic_proxy,
       notebook outputs, Phase F outputs.
```

A different sensor helps the input-stack axis but does not by itself prove
independence. The labeling method decides it.

## 3. Gate 3 — Provenance / Method

```text
[ ] Documented who produced the labels.
[ ] Documented how (reproducible rule or procedure).
[ ] Label dates and source versions recorded.
[ ] Expert review / adjudication and disagreement handling documented
    (inter-rater agreement or a written deferral reason).
```

## 4. Gate 4 — Authorization / License

For operator-provided data this is use-rights, not a public license:

```text
[ ] Source and version/release tag recorded.
[ ] Allowed use, forbidden use, and redistribution limits recorded.
[ ] Authorization basis on file (data-use agreement, ownership, or authoritative
    permission).
[ ] Content hash recorded ONLY at later approved assembly, not during Slice 13.
```

## 5. Gate 5 — Storage / Redaction

```text
[ ] artifact_class = LOCAL_SENSITIVE or FILESYSTEM_ONLY
[ ] filesystem_only = true
[ ] http_servable = false, frontend_visible = false, downloadable_via_api = false
[ ] Stored outside the git repository.
[ ] Coordinate proxies redacted from every public/summary surface.
```

## 6. Gate 6 — I2 Compatibility (capability check)

The source must be capable of producing a valid I2 pack later:

```text
[ ] Shapes into dataset_manifest.json + training_examples.jsonl
    (authoritative schema in dataset_pack_readiness.py + SPECIAL_TRACK_I).
[ ] Every reviewed-tier label can carry label_evidence_source.
[ ] Supports group + temporal-holdout splits with no leakage.
[ ] Can supply negatives/background AND hard negatives.
[ ] Enough reviewed-tier labels/class, holdout size, and negatives to set the I1
    quantitative gates; primary metric + Phase-F baseline margin can be preregistered.
```

## 7. Acceptable Vs Not — Quick Reference

```text
ACCEPTABLE (worth a Slice 13 review)
  - Operator field-validated records under data-use agreement, coordinates redactable
  - Authoritative authority records, exposure already managed, redactable
  - Non-sensitive land-cover/terrain reference for negatives/background

NOT ACCEPTABLE
  - Public coordinate datasets of preserved/vulnerable sites      (Gate 1)
  - Imagery-only labels on a similar Sentinel/SAR/DEM stack        (Gate 2)
  - Notebook / Phase F outputs as the only labels                  (Gate 2)
  - Any source where redaction cannot remove the targeting vector  (Gate 1)
```

## 8. Intake Form (Complete Before Opening A Slice 13 Review)

```text
source_name:
source_reference / DOI / authority:
authorization_basis:            (ownership | data-use agreement | authoritative permission)
what_the_labels_represent:
label_production_method:
label_evidence_type:            (one of the Gate-2 allowed types)
sensor/source_used_for_labels:
coordinate_exposure:            (none | redactable_proxy_only | raw_exposed -> REJECT)
written_sensitivity_rationale:  (required if relying on already-public/destroyed sites)
redaction_plan:
can_supply_negatives:           (yes/no)
can_supply_hard_negatives:      (yes/no)
storage_location_outside_git:   (yes/no)
operator_sign_off:
```

A candidate that cannot truthfully complete this form is not ready for review.

## 9. Boundary

This spec does not acquire data, create a dataset, label anything, download, train,
run inference, add ML dependencies, or expose anything. It defines only what a source
must be before Slice 13 review begins. H3 training and H4 private inference remain
blocked until a source passes every Slice 13 gate, an I2 pack is assembled outside
git, and the I2 validator returns `ready_for_private_training_later`.
