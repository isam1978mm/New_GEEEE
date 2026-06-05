## Phase 9 End-to-End Parity Harness

Phase 9 adds one repository-supported end-to-end notebook parity harness.

Phase 9 does not generate app outputs.
Phase 9 does not run the live pipeline.
Phase 9 does not call Earth Engine.
Phase 9 does not change science, raster, or math logic.
Phase 9 does not expose private outputs through API, frontend, or artifact serving.

The harness exists to compare an app output tree against a frozen notebook reference bundle while keeping two ideas separate:

1. runtime output presence
2. notebook-value parity

Runtime output presence means the expected app artifact exists and can be checked.
Notebook-value parity means the app artifact matches the frozen notebook reference through a family-specific verifier.

These are not the same signal.
An app output can exist without notebook-value parity.
A frozen notebook reference can be missing, and that is not success.
A comparison dependency such as `rasterio` can be unavailable, and that is not success.

The Phase 9 harness writes one JSON report:

`data/runs/<run_id>/manifests/end_to_end_notebook_parity_report.json`

The report aggregates existing parity families and records:

- app output status
- reference status
- runtime output verification status
- notebook-value parity status
- comparison status
- blocker
- recommended next action

Phase 9 family handling stays conservative:

- verifier-backed families use the existing read-only parity verifiers where available
- inventory-only families remain inventory-only
- design-only families remain design-only
- decision-only families remain decision-only
- families without a read-only verifier remain incomplete or verifier-not-available

The harness does not turn inventory-only, design-only, or decision-only families into a passing end-to-end run by themselves.

Notebook-value parity can pass only when:

- the frozen notebook reference bundle is available
- the app output artifact is available
- the relevant family verifier exists
- the verifier can run in the current environment
- the family comparison passes

Missing frozen references must report `reference_missing` or `incomplete`.
Missing app outputs must report `app_output_missing` or `incomplete`.
Missing optional comparison capability must report `comparison_unavailable`.

Phase 9 follows Phase 8 and precedes Phase 10 in the roadmap.
