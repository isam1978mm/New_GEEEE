# POS-01 actual dataset review kickoff

Status: not started

This document opens the next possible phase after Future I2 planning.

This phase is different from metadata review.

Metadata review asked:

```text
Does POS-01 look acceptable on paper?
```

Actual dataset review asks:

```text
What is actually inside the POS-01 source package, and does it still satisfy the project rules?
```

## Current status

POS-01 is a metadata-approved positive source candidate.

Future I2 planning checklists are complete.

Actual POS-01 dataset review is not started.

I1 row creation is not started.

I2 assembly is not started.

H3 remains blocked.

H4 remains blocked.

## Required operator action before review can start

The operator must obtain the POS-01 source package and keep it outside Git.

Do not commit the source package.

Do not copy raw records into repo-visible docs.

Do not copy coordinates, site lists, labels, imagery, chips, masks, or source payload rows into Git.

The source must be stored in an operator-private location.

Recommended local storage class:

```text
operator_private_storage
LOCAL_SENSITIVE or FILESYSTEM_ONLY
outside_git
```

## Plain English next step

The next step is:

```text
Put the POS-01 source package in a private local folder outside Git, then run a metadata-only file inventory.
```

The first review pass should only answer:

```text
What files are present?
What file types are present?
Is there a README/license/method note?
What schemas or tables exist?
Are sensitive fields likely present?
```

It should not publish record contents.

## Phase A — private file inventory

Allowed outputs:

- file names if not sensitive
- file extensions
- file counts
- approximate file sizes
- whether README/license/method files exist
- whether tabular/geospatial/source-document files exist

Forbidden outputs:

- raw rows
- coordinates
- site names
- source labels as raw values
- source payload contents
- private absolute paths in repo-visible docs

Decision values:

```text
inventory_ready_for_schema_review
inventory_needs_operator_info
inventory_blocked_sensitive_contents
inventory_rejected
```

## Phase B — schema review

This phase starts only after Phase A passes.

Allowed outputs:

- safe field names only
- table names only if safe
- aggregate counts
- blocker names

Forbidden outputs:

- row values
- location-bearing values
- site identifiers
- private source contents

Decision values:

```text
schema_ready_for_label_review
schema_needs_operator_info
schema_blocked
schema_rejected
```

## Phase C — label definition review

This phase starts only after Phase B passes.

It checks whether the source actually contains records that can map to the neutral positive label family:

```text
Class_A
```

Decision values:

```text
label_review_passed
label_review_passed_with_exclusions
label_review_needs_operator_info
label_review_blocked
label_review_rejected
```

## Phase D — sensitivity and exclusion review

This phase checks whether any records or fields must be excluded before I1 mapping.

Allowed outputs:

- aggregate accepted count
- aggregate excluded count
- exclusion rule summaries
- blocker names

Forbidden outputs:

- raw excluded records
- raw accepted records
- location-bearing values
- sensitive identifiers

## Phase E — actual review decision

Allowed final decisions:

```text
actual_review_passed
actual_review_passed_with_exclusions
needs_operator_info
blocked_by_permission
blocked_by_sensitivity
blocked_by_schema
blocked_by_label_quality
rejected
```

Only `actual_review_passed` or `actual_review_passed_with_exclusions` can lead to a later I1 mapping phase.

## Stop conditions

Stop immediately if the work requires:

```text
committing source data
publishing raw records
publishing coordinates
publishing site lists
creating I1 rows
assembling I2
training
inference
changing app/API/frontend code
```

Those require separate explicit approval.

## Current next action

Operator action required:

```text
Acquire POS-01 and store it outside Git in an operator-private folder.
```

After that, the next safe review action is:

```text
Run private file inventory only.
```

## Current final status

Actual POS-01 dataset review is opened but not started.

I2 assembly is not authorized.

H3 remains blocked.

H4 remains blocked.
