# Depth Terminology Correction

Status: authoritative wording correction for the depth-estimation work.

## Correction

The word `lawful` was unnecessarily added to the Phase 2 wording. The owner did not request a public-service, legal-review, or public-exposure requirement.

For this private local app, the correct requirement is:

> Use independently measured or independently documented known-depth reference cases, and store the resulting dataset locally outside Git.

This means only that the reference depth must come from evidence independent of the notebook, classifier, target mask, PCA output, or other app-generated signal.

It does **not** mean:

- the app must be public;
- the dataset must be uploaded;
- a public API must be enabled;
- a legal review is a depth-model prerequisite;
- the private local workflow must be converted into a public product.

## Private-local boundary

The intended storage and access boundary remains:

```text
local private storage
outside Git
not served by the API
not visible in the frontend unless a later local operator view is approved
not publicly downloadable
```

## Superseding wording

Where the depth execution plan or calibration contract says `lawful documented sources` or `controlled lawful test sites`, read it as:

```text
independently documented sources
controlled test sites with measured placement depth
```

No other evidence, calibration, privacy, or validation rule is changed by this correction.
