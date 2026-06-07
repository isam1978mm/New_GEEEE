# Future Slice 13A Candidate Register Scaffold

Slice 13A adds scaffold tooling for a private candidate register. It does not review
real candidate sources.

## Scope

Slice 13A creates:

- a schema helper for the candidate review record
- approved lifecycle values
- six gate names from the Slice 13 checklist
- a private register scaffold initializer
- a redacted setup summary
- a private run report

Implemented module:

`app/pipeline/parity/dataset_source_candidate_register.py`

## Private Register Layout

The operator supplies a private root outside the repository. The helper rejects
repository-contained roots and path traversal. When explicitly called, it creates
only this empty structure:

```text
<PRIVATE_ROOT>/
  candidate_register/
    candidates.jsonl
    reviews/
```

`candidates.jsonl` is created empty. No real candidate entries, datasets, labels,
chips, masks, imagery, coordinates, site lists, or source payloads are created.

## Candidate Schema

The candidate record schema mirrors `docs/FUTURE_SLICE_13_EXECUTION_CHECKLIST.md`
and includes:

```text
candidate_id
source_name
source_reference
source_url_or_doi
source_type
lead_status
review_status
sensitivity_status
sensitivity_decision
sensitivity_blocker
independence_status
independence_decision
independence_blocker
provenance_status
provenance_decision
provenance_blocker
license_status
license_decision
license_blocker
storage_status
storage_decision
storage_blocker
i2_compatibility_status
i2_compatibility_decision
i2_compatibility_blocker
final_decision
final_blocker
reviewer
review_date
notes
```

Lifecycle values are:

```text
unverified_lead
under_review
rejected
conditionally_approved_for_I2
```

Gate names are:

```text
sensitivity_misuse
independent_evidence
provenance_labeling_method
license_access_terms
storage_redaction
i2_validator_compatibility
```

## Redaction Boundary

The setup summary and run report do not include:

- local paths
- coordinates
- private hashes
- candidate contents
- source payloads

They report only scaffold status, schema metadata, lifecycle values, gate names,
and safety booleans.

## Safety Boundary

Slice 13A does not:

- review real candidate sources
- create a real dataset pack
- create labels, chips, masks, imagery, coordinates, or site lists
- collect web content into the repository
- call Earth Engine
- train a model
- run inference
- add ML dependencies
- expose overlays or coordinates
- change API, frontend, database, or artifact-serving behavior
- implement H3 or H4

## Report

The report writer writes metadata only:

```text
data/runs/<run_id>/manifests/future_slice_13a_candidate_register_scaffold.json
```

The report is private run metadata. It does not include private register paths or
candidate contents.

## Next Step

The next Slice 13 step is a separate, user-approved source-review slice that uses
the private register scaffold to evaluate candidate sources through the six gates.
