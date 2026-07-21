# Depth Blockers Execution Plan — 2026-07-20

Status: authoritative execution plan for the private local depth-research workflow.

This plan turns the remaining blockers into a finite sequence of research, evidence, validation, and software tasks. It must be read with:

- `docs/DEPTH_REMAINING_BLOCKERS_AND_UNBLOCKING_PLAN_2026-07-20.md`
- `docs/DEPTH_CALIBRATION_DATASET_CONTRACT.md`
- `docs/DEPTH_VALIDATION_GATES_SPEC.md`
- `docs/DEPTH_PUBLIC_EVIDENCE_CANDIDATE_REGISTER_2026-07-18.md`
- `docs/DEPTH_ACTIVE_EVIDENCE_ACQUISITION_STATUS_2026-07-18.md`
- `templates/depth_calibration/README.md`

## One-sentence decision

There is no valid shortcut around independent evidence, but the project can move faster by searching for and qualifying existing public known-depth ground truth before requiring new field collection.

## Current boundary

The current matched Sentinel-1 work supports an unexplained site-specific radar change. It does not identify the physical cause, establish a buried object, provide depth, or justify a confidence percentage.

```text
current_site_status = unexplained_radar_anomaly_research_case
cause_attribution = blocked_missing_independent_physical_evidence
relative_depth = blocked_missing_known_depth_calibration_pack
numerical_depth = blocked_missing_model_and_holdout_validation
app_depth_enabled = false
```

The work is active even though app depth remains gated.

## Existing work that must be reused

Do not create a parallel evidence register or duplicate the calibration tooling.

Already available:

- public evidence candidate register P1–P8;
- 16 extracted public candidate rows across two controlled physical-site groups;
- public candidate validator and regression tests;
- first-pass Sentinel-1 scale-compatibility finding;
- private-pack initializer;
- dry-run-first private record intake;
- aggregate-only calibration-pack validator;
- manifest finalizer;
- dataset, feature, validation, privacy, and app architecture contracts.

Current public candidate records remain unapproved for private-pack import because reference uncertainty and complete sensor/support qualification are unresolved.

## Responsibility boundary

### Work that can be completed through research and repository execution

- search public and institutional sources;
- inspect papers, archives, metadata, licences, and provenance;
- assess whether a source contains independent depth-to-top truth;
- assess uncertainty, grouping, dates, target context, and sensor compatibility;
- maintain the public candidate register;
- prepare synthetic test fixtures and evaluation code;
- initialize, validate, and finalize the private calibration pack after valid records are available;
- implement training, holdout evaluation, refusal, privacy, and app integration code after the required gates open.

### Work that requires an outside person, organization, or physical source

- provide private or non-public engineering and construction records;
- authorize restricted data use;
- answer author or custodian requests when direct correspondence is required;
- conduct GPR, magnetometer, electromagnetic, excavation, or other physical investigation;
- create independently measured controlled-site records;
- confirm that a location is genuinely target-free.

Online research can discover evidence. It cannot manufacture missing physical truth.

# Workstream A — Current-site cause attribution

## Goal

Identify a specific physical explanation for the current radar anomaly using evidence independent of the satellite feature stack.

## A1 — Paper-trail search

Search, where lawful and applicable, for:

- utility-owner and utility-location records;
- municipal public-works or engineering records;
- building permits and construction drawings;
- as-built plans;
- drainage, irrigation, septic, foundation, trench, or pipeline plans;
- land or property records;
- historical aerial imagery and documented site-change records;
- archaeological or engineering reports already associated with the area.

## A2 — Evidence qualification

For each candidate source, record:

- source owner or publisher;
- document title, date, version, and reference;
- method used to establish the claimed feature;
- spatial matching method;
- uncertainty and limitations;
- whether the evidence is independent of the app and notebook signals;
- whether it supports a specific physical interpretation.

## A3 — Escalation when records are insufficient

If documentary evidence cannot identify the cause, the next valid step is a professional physical-site investigation, such as:

- ground-penetrating radar;
- magnetometer survey;
- electromagnetic-induction survey;
- another documented geophysical or engineering investigation.

No excavation is required merely to begin independent verification.

## A pass condition

Blocker 1 passes only when traceable, reviewable, spatially matched independent evidence supports a specific physical interpretation.

## A stop states

```text
completed_cause_supported
partially_unblocked_candidate_explanation_only
blocked_no_public_records_found
blocked_requires_owner_or_authority_records
blocked_requires_physical_survey
```

A visually similar map, classifier label, PCA anomaly, notebook name, or invented confirmation percentage does not pass.

# Workstream B — Public known-depth evidence acquisition

## Goal

Use existing open or institutionally available ground truth to populate the private known-depth calibration pack without inventing labels.

This is the immediate critical-path workstream for Blocker 2.

## B1 — Continue the existing P1–P8 queue

Complete the unresolved work already recorded in the candidate register:

1. extract TU1208 depth-to-top definitions and uncertainty support;
2. obtain Texas A&M–Corpus Christi target-level construction details and dates;
3. recover reference uncertainty for IAG/USP and Ahmadu Bello records;
4. recover exact construction or installation dates where satellite pre/post matching is possible;
5. inspect unresolved archive metadata and obtain missing source documentation;
6. seek independent confirmation for interpreted-depth candidates;
7. find independently documented confirmed no-target or background cases.

## B2 — Extend the existing register, not replace it

New source categories may be added only through the same screening vocabulary and three-decision framework:

```text
source_evidence_usable
method_research_usable
direct_app_calibration_usable
```

### Sentinel-1-native archaeology candidates

These may fill the current sensor-match gap, but must begin as candidates only.

Required before any import approval:

- primary source verified;
- independent excavation, engineering, or survey depth established;
- depth-to-top definition extracted;
- uncertainty recorded or defensibly bounded;
- Sentinel-1 acquisition and processing documented;
- physical-site grouping defined;
- sensitivity and misuse review passed;
- scale and support screen passed.

Sentinel-1 involvement alone does not make a record valid calibration truth.

### Out-of-finding-family sources

Ordnance or other sources outside the approved benign finding families must not enter the active buried-object calibration pack. They may be rejected with reason or retained only as separately governed method research when lawful and appropriate.

### Natural-interface depth analogs

Permafrost thaw depth, groundwater depth, subsidence-linked depth, and similar natural-interface datasets must remain in a separate method-only track.

```text
usable_for_harness_testing = possible
usable_as_buried_object_calibration_truth = no
private_calibration_pack_import = prohibited
```

They may test evaluation machinery but cannot establish buried-object depth performance.

## B3 — Apply the existing Sentinel-1 scale rule

Do not restart the scale screen from zero.

The first-pass repository finding already rules out treating each small controlled-site object as a separate Sentinel-1 sample. The active satellite experiment shape is:

```text
whole_physical_site_or_large_isolated_section_pre_post_experiment
```

not:

```text
individual_small_target_satellite_depth_row
```

The remaining task is to formalize and apply that rule consistently.

For every candidate site, determine:

- physical site extent;
- approved clean analysis window;
- likely mixing with neighboring targets or infrastructure;
- available Sentinel-1 orbit, geometry, dates, and valid-pixel support;
- whether a defensible pre/post or cross-site comparison exists;
- whether the source is direct calibration, method-only evidence, or unsuitable.

A candidate with unresolved scale support cannot be marked `direct_app_calibration_usable`.

## B4 — Reference-uncertainty policy

Every usable positive record needs reported uncertainty or a documented defensible uncertainty rule.

The policy must record:

- source measurement precision;
- installation or survey tolerance;
- surface-reference uncertainty;
- ambiguity in depth reference;
- any conversion required to obtain depth to the top;
- final bounded uncertainty used by the calibration record.

Uncertainty must not be guessed merely to satisfy the validator.

## B5 — Confirmed-negative acquisition

Search for independent no-target or background evidence, including:

- cleared control areas at controlled test sites;
- pre-installation survey areas with documented absence before placement;
- independently surveyed undisturbed control plots;
- engineering or construction records establishing a valid empty comparison area;
- earlier heuristic false positives only after independent negative confirmation.

A quiet radar pixel, unverified background area, or heuristic false positive does not count as a confirmed negative.

## B6 — Candidate qualification decision

Each source must end in one explicit state:

```text
candidate_under_review
evidence_verified_pending_support
direct_calibration_candidate
method_research_only
rejected_missing_independent_depth
rejected_missing_uncertainty
rejected_scale_or_sensor_mismatch
rejected_privacy_or_misuse_risk
rejected_out_of_finding_family
```

## B pass condition

Blocker 2 passes only when the private calibration pack contains contract-eligible known-depth positives and independently confirmed negatives in train, validation, and untouched holdout splits, with whole physical sites or leakage groups kept together.

The present unknown research site remains excluded from fitting and threshold selection. It may be retained for audit as an uncertain record with both inclusion flags false.

# Workstream C — Private calibration-pack assembly

## Goal

Convert only fully qualified evidence into a private, contract-valid calibration pack outside Git.

## Existing tool sequence

```text
scripts/init_depth_calibration_pack.py
→ scripts/add_depth_calibration_record.py --create-template
→ scripts/add_depth_calibration_record.py
→ scripts/add_depth_calibration_record.py --write
→ scripts/validate_depth_calibration_pack.py
→ scripts/finalize_depth_calibration_manifest.py
→ scripts/finalize_depth_calibration_manifest.py --write
→ scripts/validate_depth_calibration_pack.py
```

## C rules

- real coordinates, records, source paths, and site-level splits remain outside Git;
- every positive has independent depth-to-top truth and uncertainty;
- every negative has independent no-target support;
- identifiers do not encode coordinates;
- one physical site or leakage group never crosses splits;
- repeated dates and linked features stay together;
- feature manifest excludes classifier, PCA, target-mask, generated-label, and circular inputs;
- the holdout remains untouched and research-eligible;
- no row exists merely to make a split look non-empty.

## C pass condition

The aggregate validator reports dataset-contract readiness with eligible positives and negatives in every required split, and the finalized manifest hashes and counts validate.

# Workstream D — Scientific-validation preparation

## Goal

Remove software delay without pretending synthetic data proves scientific performance.

This work may proceed before the private pack is ready.

## D1 — Freeze baseline definitions

Prepare deterministic implementations for:

- majority-class baseline;
- stratified-random baseline;
- one-feature threshold baseline;
- median-depth baseline;
- relative-class midpoint baseline;
- confounder-only baseline.

## D2 — Build the evaluation harness

Using synthetic fixtures only, test:

- group-separated train, validation, and holdout handling;
- leakage rejection;
- metric calculations;
- interval coverage and width calculations;
- subgroup reporting;
- abstention behavior;
- unsupported-condition refusal;
- deterministic repeated execution;
- aggregate-only output and privacy protections.

Synthetic or analog results must be labelled software or method tests, never scientific validation.

## D3 — Preregister the acceptance framework

Before opening the untouched holdout, freeze and version:

- primary metrics;
- baseline comparisons;
- acceptance and failure rules;
- allowed training and validation selection process;
- holdout-use prohibition;
- relative-depth performance thresholds;
- numerical metre tolerances;
- interval-coverage targets;
- interval-width failure rules;
- subgroup and support requirements;
- abstention expectations.

Any revision based on training or validation results must be recorded before holdout evaluation.

# Workstream E — Relative-depth scientific validation

## Entry condition

Workstream C passes and the feature manifest is frozen.

## Execution

1. derive relative categories using training data only;
2. fit candidate methods on training sites only;
3. choose features, thresholds, and model settings using training and validation only;
4. freeze the accepted method and package;
5. evaluate once on untouched holdout sites;
6. compare against frozen simple baselines;
7. run confounder, ablation, support, negative-case, and stability tests;
8. report site-level, class-level, subgroup, coverage, and abstention results.

## E pass condition

The accepted relative method beats the frozen baselines on unseen physical sites, does not depend on one site or confounder group, and abstains outside supported conditions.

No metre output is allowed from this gate.

# Workstream F — Numerical depth and calibrated uncertainty

## Entry condition

Relative-depth evidence succeeds and the numerical experiment has a justified support range.

## Execution

1. freeze numerical features, preprocessing, interval method, and support policy;
2. fit on training sites only;
3. select using training and validation only;
4. evaluate once on untouched holdout sites;
5. compare with median-depth and relative-midpoint baselines;
6. report absolute error, bias, RMSE, interval coverage, interval width, tolerance success, subgroup performance, and abstention;
7. reject narrow but poorly calibrated intervals and unusably wide intervals.

## F pass condition

The numerical method beats the frozen baselines on unseen physical sites, meets preregistered error and interval rules, and provides honest refusal outside support.

A raw model score is never a validated confidence percentage.

# Workstream G — App implementation and release

## Entry condition

The applicable dataset and scientific gates pass for the requested mode.

## Execution

- implement the frozen depth stage and schemas;
- package the approved model, feature manifest, versions, hashes, and support matrix locally;
- implement refusal and abstention paths;
- add unit and integration tests;
- prove depth does not modify classifier or legacy artifacts;
- enforce filesystem-only private details;
- test privacy, wording, compatibility, package integrity, and old-run behavior;
- run a frozen full private-local acceptance;
- enable only the mode supported by the evidence.

## G pass condition

All applicable contract, software, scientific, support, privacy, wording, compatibility, and release gates pass.

Until then:

```text
depth_mode = off
visible_depth_result = not_available
```

# Immediate execution queue

## Active now

- [ ] Start Workstream A paper-trail search for independent current-site evidence.
- [ ] Continue unresolved P1–P8 evidence extraction.
- [ ] Review new Sentinel-1-native candidate sources under provenance, uncertainty, scale, and sensitivity rules.
- [ ] Recover reference uncertainty for extracted controlled-site records.
- [ ] Find independently confirmed no-target/background candidates.
- [ ] Formalize the existing whole-site or large-section Sentinel-1 scale rule in the candidate register.
- [ ] Build or complete frozen baseline and holdout-evaluation harnesses with synthetic fixtures.
- [ ] Commit a versioned preregistration framework before final holdout use.

## Waiting on qualified evidence

- [ ] Import the first approved positive record into the private pack.
- [ ] Import the first approved confirmed-negative record.
- [ ] Populate all required group-separated splits.
- [ ] Freeze the neutral feature manifest.
- [ ] Finalize and validate the private calibration pack.

## Gated until the pack passes

- [ ] Fit the relative-depth baseline.
- [ ] Run untouched holdout validation.
- [ ] Consider numerical depth ranges.
- [ ] Implement and release app depth.

# Honest completion states

Use only these status meanings:

```text
completed
active_research
partially_unblocked
blocked_no_public_evidence_found
blocked_requires_owner_action
blocked_requires_source_authorization
blocked_requires_physical_survey
blocked_missing_contract_ready_pack
blocked_missing_holdout_validation
blocked_release_gates
```

Finding a paper is not the same as obtaining a valid record. Passing software tests is not the same as proving depth estimation works. App depth remains disabled until the full applicable chain passes.