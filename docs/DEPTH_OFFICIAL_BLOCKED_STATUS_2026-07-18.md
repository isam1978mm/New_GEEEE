# Historical Depth Status — Superseded 2026-07-18

This document previously described the entire depth workstream as blocked because the private calibration pack contained no verified records.

That wording is superseded by:

```text
docs/DEPTH_ACTIVE_EVIDENCE_ACQUISITION_STATUS_2026-07-18.md
```

## Correct current interpretation

```text
research_and_evidence_work = active
online_evidence_search = active
candidate_dataset_inspection = active
software_and_intake_tooling = active
relative_depth_claim = gated
numerical_depth_claim = gated
app_depth_output = not_available
```

Missing verified calibration records prevent a scientific depth claim and app activation, but they do not stop evidence search, archive inspection, source qualification, data acquisition, supporting experiments, or tooling work.

## Historical facts retained

At the time of the original status:

- the private calibration pack had zero records;
- the validator correctly returned `not_ready_no_records`;
- the manifest finalizer correctly refused the empty pack;
- no model training had started;
- no app depth output had been enabled;
- notebook outputs, classifier results, PCA outputs, target masks, visual guesses, and generated labels were not acceptable depth truth.

Those facts remain valid. Only the overall status label changed.

## Current execution rule

Continue work through the evidence-qualification pipeline:

```text
search
→ inspect
→ verify provenance and depth truth
→ classify suitability
→ import verified evidence privately
→ validate the dataset contract
→ run relative-depth research
```

Do not stop merely because the first candidate lacks complete metadata. Record the gap and continue investigating that source and other sources.

## Release boundary

The following still require verified evidence and passed validation:

- claiming that relative depth works;
- claiming numerical depth ranges;
- enabling depth output in the normal app;
- presenting depth as physically confirmed.

This file is retained only to preserve the historical decision trail. It is not the current project status.