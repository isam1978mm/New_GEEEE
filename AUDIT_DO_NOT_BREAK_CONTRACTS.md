# Do Not Break Contracts

Read this before changing tests, frontend artifact handling, operator outputs, classifier naming, run-state cleanup, or public/private safety code.

This app is audited as a **local private app**, not a public product. Passing CI is not enough if old completed local runs stop rendering their existing outputs.

## Owner-directed final area findings contract — 2026-07-17

Future audits must preserve the following operator-facing behavior:

1. After a completed run, the app must provide an easy-English **Final area findings summary**.
2. The summary must rank possible findings from strongest to weakest.
3. Each finding must show the classifier probability or score produced by the app.
4. The summary must clearly name the best-supported finding and explain which result deserves the most attention.
5. When the evidence is weak, conflicting, or incomplete, the summary must say that no strong result was found instead of forcing a confident conclusion.
6. Direct domain labels are allowed because this is a private local app for one informed operator.
7. Do not replace useful labels with generic neutral bands merely to satisfy the superseded PRD v0.5 neutrality rule.
8. Preserve current core outputs and legacy `experimental/*` outputs when building the summary.
9. Do not invent depth. Numerical depth in metres is a separate capability and must remain unavailable until the depth-estimation execution plan is implemented and validated.

This contract defines how results are summarized. It does not turn classifier output into physical confirmation or a validated scientific measurement.

### Implemented Item 8 contract — 2026-07-18

The final area findings summary is now implemented in classifier output contract
`core_classifier_outputs_v2`.

Future audits must preserve these exact semantics:

- `class_score` and `finding_score` are **app scores**, not measured probabilities.
- Finding labels are produced by a deterministic rule using the app score and the
  object's bounding-box shape.
- The summary groups objects by finding label and ranks labels by their highest app
  score, then supporting candidate count.
- When two or more findings share the highest app score, the summary must say
  they are tied and explain that support count determines the displayed order.
- A tied result must not be described as one uniquely strongest finding.
- The summary is stored under `final_area_findings` in `classifier/summary.json`.
- New classifier rows include `finding_label`, `finding_score`, `score_type`,
  `finding_reason`, and `review_order`.
- Existing `classifier/*` artifacts remain available.
- Identical legacy copies under `experimental/*` remain available.
- The frontend derives the same score-and-shape summary for older completed runs
  whose summary JSON predates `final_area_findings`.
- The unsupported hard-coded “about a 30% signal” wording must not be restored.
- The frontend must say that app screening scores are not measured probabilities or
  physical confirmation.
- `depth_status` remains `not_available`, and the UI displays no depth in metres.

The current rule does not calculate competing class probabilities such as “72% metal,
19% chamber, 9% natural ground.” Audits must not require or display that type of
distribution unless a future validated classifier actually produces it.

## Non-negotiable rule

Do not make CI green by removing behavior that real existing runs depend on.

If a patch changes tests, it must preserve or add a behavior-level regression test for the user-visible contract.

## Classifier compatibility contract

The classifier is a core app feature. The old `experimental/` path is legacy compatibility, not disposable dead code.

The app must support both current core classifier outputs and legacy experimental outputs:

```text
classifier/classifications.csv
classifier/summary.json
classifier/neutral_target_labels.json

experimental/classifications.csv
experimental/summary.json
experimental/neutral_target_labels.json
```

If either set exists for a completed run, the **Classifier Results** panel must not display:

```text
No classifier result is available for this run yet.
```

The UI must display classifier results and provide working download links.

Required frontend fallback order:

1. Core artifact route, for example `classifier_classifications`.
2. Legacy artifact route, for example `experimental_classifications`.
3. Output-tree download route, for example `experimental/classifications.csv`.

Do not remove output-tree fallback support for old runs.

## Required classifier regression test

Before declaring CI fixed after classifier, artifact, frontend, or output-tree edits, verify old-run compatibility:

- Seed or use a completed run with only legacy `experimental/*` classifier files.
- Confirm the operator output tree lists:
  - `experimental/classifications.csv`
  - `experimental/summary.json`
  - `experimental/neutral_target_labels.json`
- Confirm `/outputs/download/experimental/classifications.csv` works.
- Confirm the frontend classifier loader can fetch summary and rows through fallback.
- Confirm the panel does not show the empty classifier result message.

Recommended permanent test name:

```text
tests/integration/test_classifier_legacy_ui_fallback_contract.py
```

## Frontend test rule

Do not remove a brittle UI text assertion unless another assertion still proves the same user-visible behavior.

Bad fix:

```text
Remove old text assertions until frontend_static passes.
```

Good fix:

```text
Replace exact-copy checks with behavior checks that verify downloads, fallback URLs, and visible data state.
```

## Operator output contract

There are two different operator-output concepts. Do not merge them accidentally.

### Private-local safe path helper

`is_operator_visible_relative_path()` may allow safe unlisted local files when the app is running as a private local tool.

It must still block genuinely sensitive paths and names, including:

```text
../outside.txt
.env
PATH_MAP.local.json
*.db
*.sqlite
*.log
credentials
service-account
private_key
```

### Operator output tree listing

The output tree served to the UI must remain allowlisted and must not suddenly expose arbitrary local files.

Use the stricter tree-listing helper for output-tree enumeration and not-implemented filtering.

Do not use a private-local permissive helper to filter `not_implemented` output-tree entries.

## Run-name safety contract

There is a split contract:

- `RunCreate` DTO may accept private local names for internal validation/harness tests.
- The public `/runs` endpoint must reject coordinate-like or path-like names with a generic 422 validation error that does not echo the unsafe value.

Do not move the public endpoint rejection into the DTO if it breaks the private-local schema harness.

## Startup stale-run contract

Startup stale cleanup must not break the queued-run lock contract.

Queued runs remain queued and still block a second active run. Running orphaned runs may be marked `stale_failed`.

Do not mark queued runs stale during startup unless all startup and runs API tests are intentionally redesigned together.

## GeoTIFF alignment contract

Alignment QA uses real GeoTIFF metadata as authoritative. Sidecar JSON is optional/non-authoritative for alignment.

Test fixtures that expect alignment pass must write real georeferenced TIFFs, not plain PIL TIFFs with only sidecar metadata.

A drift test must mutate the real TIFF transform, not only the sidecar.

## Test-change checklist

Before committing any future patch that touches classifier, artifacts, output tree, frontend, or run state:

1. Run the targeted unit/integration tests.
2. Run at least one old-run compatibility check.
3. Confirm both new core outputs and legacy `experimental/*` outputs are still handled.
4. Confirm public/private separation is preserved.
5. Confirm no exact coordinates, private paths, raw arrays, KMZs, or target geometry are exposed through public UI/API unless explicitly approved.

## Safe summary for future sessions

Do not optimize for green CI alone. The app must remain compatible with existing local private runs. The classifier panel disappearing while files still exist is a regression, even if tests pass.
