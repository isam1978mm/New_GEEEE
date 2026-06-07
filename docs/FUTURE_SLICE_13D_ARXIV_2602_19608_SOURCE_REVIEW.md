# Future Slice 13D arXiv 2602.19608 Source Review

Slice 13D performs a metadata-only source review for the `arXiv:2602.19608`
candidate lead through the six Slice 13 gates.

It does not approve training. It does not download data. It does not assemble an
I2 pack. It does not train or infer. It does not add ML dependencies. It does
not call Earth Engine. It does not change API, frontend, database, or
artifact-serving behavior.

## Candidate

Candidate reviewed:

```text
candidate_id: arxiv_2602_19608_looted_sites
source_name: arXiv 2602.19608 public metadata lead
source_reference: arXiv:2602.19608; microsoft/looted_site_detection public repository metadata
source_url_or_doi: https://doi.org/10.48550/arXiv.2602.19608
source_type: public_paper_and_repository_metadata
lead_status: unverified_lead
```

The candidate is reviewed only as an `unverified_lead`. Public, cited, or online
metadata does not make a source approved for I2, H3, H4, training, or inference.

## Public Metadata Reviewed

The arXiv metadata describes a satellite-based pipeline for looted
archaeological-place detection, PlanetScope monthly mosaics, a curated
Afghanistan dataset with looted and preserved examples, multi-year imagery, and
site-footprint masks. The paper metadata also references a public repository.

The repository metadata indicates code and examples for feature-based and
image-based ML workflows, including example chips and masks, but Slice 13D does
not download or inspect source payload files. Repository code licensing does not
by itself establish dataset-payload access, reuse, or redistribution terms for a
private I2 pack.

## Six-Gate Result

The review applies all six gates:

```text
sensitivity_misuse: reject
independent_evidence: weak_signal_only
provenance_labeling_method: insufficient_information
license_access_terms: insufficient_information
storage_redaction: needs_human_review
i2_validator_compatibility: insufficient_information
```

Gate 1 rejects I2 routing for this metadata lead. The source metadata concerns
looting-related heritage-place imagery, preserved-place examples, and
footprint-mask material. Slice 13 policy ranks sensitivity/misuse first, and
Gate 1 can reject a candidate without waiting for later gates.

The independent-evidence gate also blocks I2 routing. Public metadata does not
establish reviewed-tier labels independent of modeled imagery signals.
Imagery-derived labels remain weak-signal-only unless a later review supplies
independent evidence that satisfies the binding ML readiness plan.

Method/provenance, dataset-payload access terms, storage/redaction, and I2
schema fit also remain incomplete from metadata-only review. No private source
material was accessed or assembled.

## Final Decision

Final decision:

```text
rejected
```

This is not `conditionally_approved_for_I2`. Conditional I2 approval requires all
six gates to pass. H3 training and H4 inference remain blocked.

## Helper

Implemented in:

```text
app/pipeline/parity/dataset_source_review.py
```

The helper provides:

- a deterministic redacted review record for `arXiv:2602.19608`
- six-gate status metadata
- gate rules that make `conditionally_approved_for_I2` possible only when all
  six gates pass
- a redacted private report writer

Report path:

```text
data/runs/<run_id>/manifests/future_slice_13d_arxiv_2602_19608_source_review.json
```

The report does not include exact coordinates, raw geometry, site lists, local
paths, private hashes, labels tied to locations, or dataset payload content.

## Safety Boundary

Slice 13D does not:

- download datasets, imagery, masks, chips, labels, site lists, or archives
- create a private candidate register in git
- create an I2 pack
- train a model
- run inference
- add ML dependencies
- call Earth Engine
- scrape web pages into the repo
- expose overlays or private source material publicly
- change API, frontend, database, or artifact-serving behavior

## Next Step

The next Slice 13 step is either:

- review another operator-provided candidate source through the same six gates,
  or
- close the current known-lead review set only if the external private-register
  criteria are satisfied and the operator accepts that no source is approved for
  I2 routing.

H3 and H4 remain blocked until a later source passes Slice 13, an I2 pack is
assembled outside git, and the I2 validator returns
`ready_for_private_training_later`.
