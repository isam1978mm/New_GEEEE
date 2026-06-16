# POS-01 Phase D aggregate-only sensitivity and exclusion review result

Status: passed for private-handling decision; exact exclusion-union count still needed

This document records operator-provided aggregate-only sensitivity and exclusion counts for POS-01 CSV files.

No source rows are included.

No coordinates are included.

No site names are included.

No addresses are included.

No map links are included.

No raw source payload contents are included.

No private local paths are included.

## Reviewed files

- unesco.csv
- science-at-risk.csv

## Aggregate accepted/rejected counts

### unesco.csv

| Metric | Count |
| --- | ---: |
| Accepted Yes | 211 |
| Rejected No | 140 |
| Blank Include | 14 |

Accepted records missing key fields:

| Field | Missing among accepted |
| --- | ---: |
| Type of damanged site | 1 |
| Geo location | 2 |
| Address | 2 |
| Date of damage first reported | 13 |

Accepted records with location-like fields present:

| Field | Present among accepted |
| --- | ---: |
| Geo location | 209 |
| Address | 209 |
| Link to google Maps | 209 |

### science-at-risk.csv

| Metric | Count |
| --- | ---: |
| Accepted Yes | 22 |
| Rejected No | 1 |
| Blank Include | 0 |

Accepted records missing key fields:

| Field | Missing among accepted |
| --- | ---: |
| Type of damanged site | 0 |
| Geo location | 0 |
| Address | 0 |
| Date of damage | 0 |

Accepted records with location-like fields present:

| Field | Present among accepted |
| --- | ---: |
| Geo location | 22 |
| Address | 22 |
| Link to google Maps | 22 |

## Sensitivity decision

Decision:

```text
sensitivity_private_handling_required
```

Reason:

- accepted records contain location-like fields by aggregate count
- location-like fields must remain outside Git
- repo-visible documentation may contain only aggregate counts and safe field names
- no raw sensitive values were copied into Git

## Exclusion rule candidates

Candidate exclusion rules for later I1 mapping:

```text
exclude Include blank
exclude Include No
exclude accepted records missing required type field
exclude accepted records missing required geolocation field
exclude accepted records missing required address field if address is required for source QA
route accepted records missing damage date to needs_operator_review or non-temporal-only review
```

Exact exclusion-union counts are still needed before a final Phase E decision.

## Phase D decision

Decision:

```text
sensitivity_review_passed_private_handling_required
```

Open item:

```text
compute aggregate union counts for accepted records with any required-field gap
```

The open item is aggregate-only and must not expose row values.

## Current final status

Phase A private file inventory passed.

Phase B header-only schema review passed with sensitivity controls.

Phase C aggregate-only label review passed for aggregate counts.

Phase D sensitivity review passed for private handling.

Phase D exact exclusion-union count is still pending.

I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.
