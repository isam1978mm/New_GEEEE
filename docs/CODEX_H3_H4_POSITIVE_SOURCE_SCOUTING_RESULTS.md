# Codex H3/H4 Positive Source Scouting Results

This document records the Codex metadata-only positive-source scouting pass.

This is documentation only.
It does not create data, assemble I2, start training, start inference, add dependencies, or change app behavior.

No source payloads, record-level material, private operator records, imagery, masks, chips, archives, or training labels are added here.

## Current project status before results

```text
C05 ESA WorldCover: conditionally approved for later I2 negative/background only
C06 Dynamic World: conditionally approved for later I2 hard-negative only
C07 Maus mining polygons: conditionally approved for later I2 hard-negative only
C01 UNOSAT / UNESCO: still under_review; source-specific information required
I2 assembly: not authorized
H3 training: blocked
H4 private inference: blocked
```

## Codex result summary

Codex found one strongest public/metadata candidate and several operator-permission candidates.

## Highest-priority new candidate

```text
candidate_id: POS-01
source_name: Linked4Resilience annotated damaged cultural sites / infrastructure dataset
source_link_or_doi: https://zenodo.org/records/14569340
owner_or_authority: Shuai Wang et al.; derived from UNESCO and ScienceAtRisk source families
evidence_type: annotated damaged cultural-property / infrastructure dataset
why_it_matters: closest package-like positive-source lead found by Codex
current_decision: ready_for_6gate_review
```

Codex-reported blockers:

```text
[ ] license conflict / ambiguity must be resolved
[ ] private ML training permission is not known
[ ] source derivation rights must be checked
[ ] sensitivity and redaction risk must be reviewed
[ ] exact target-fit for H3/H4 must be reviewed
```

Important: POS-01 is not approved for I2. It is only approved to open a metadata-only six-gate review.

## Existing C01 remains important

```text
candidate_id: C01
source_name: UNITAR-UNOSAT / UNESCO damage / looting assessment source family
current_decision: ready_for_source_specific_review / still_under_review
```

Codex reported that the best web-discoverable actionable positive family is still C01 if a specific safe subset can be selected and licensed.

C01 still needs:

```text
[ ] exact product/subset
[ ] per-item license confirmation
[ ] private ML training permission
[ ] method / adjudication details
[ ] redaction plan
[ ] validator-ready neutral label mapping later
```

## Operator / authority candidates needing permission

Codex also identified these as potentially strong, but not immediately approvable without operator/authority permission:

```text
C04 — operator/national-authority field-verified records
C10 — MEGA-Jordan / Arches Jordan national heritage inventory
C11 — national heritage authority post-conflict damage records
C03 — ASOR CHI incident / damage reports
C02 — EAMENA disturbance / threat records
C09 — UNESCO World Heritage State of Conservation records
```

Common blocker:

```text
permission / DUA / reuse rights unknown
private training permission unknown
sensitivity review required
```

## Weak or rejected leads

```text
POS-05 / Science at Risk infrastructure data: weak_signal_only unless operator scoping makes it target-specific
POS-06 / xBD or xView2 generic building-damage data: reject for H3/H4 target-positive role
C12 / law-enforcement antiquities seizure data: weak_signal_only for site-pixel labels
```

Still excluded:

```text
D1 outputs
Phase F scores
candidate zones
same-app-layer signals
public gazetteers of preserved/vulnerable places
negative/background-only sources
```

## Best next review target

```text
Next metadata-only review target: POS-01 Linked4Resilience / Zenodo damaged cultural sites dataset
```

Why:

```text
It is the closest new package-like positive-source lead.
It has a DOI / repository page.
It appears derived from external source families.
It may clarify subset, method, license, and sensitivity questions faster than broad C01 source-family review.
```

## Next step

Open a metadata-only six-gate review for POS-01.

Do not download the Zenodo payload.
Do not inspect or copy record-level contents.
Do not assemble I2.
Do not train.
Do not infer.

The POS-01 review should decide only:

```text
[ ] Gate 1 sensitivity / misuse
[ ] Gate 2 independent evidence
[ ] Gate 3 provenance / method
[ ] Gate 4 license / access terms
[ ] Gate 5 storage / redaction
[ ] Gate 6 I2 schema fit
```

## Current final status

```text
POS-01: ready_for_6gate_review
C01: still_under_review
C05/C06/C07: negative or hard-negative only
positive_source_approved: false
I2 assembly: not authorized
H3 training: blocked
H4 inference: blocked
```
