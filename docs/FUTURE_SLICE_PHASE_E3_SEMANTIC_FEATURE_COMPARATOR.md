# Future Slice 03 / Phase E3 Semantic Feature Comparator

## Scope

Phase E3 adds a private comparator for Phase C semantic feature outputs. It covers the Phase C1 relation writer family and the Phase C2 extended writer family.

Phase E3 is comparator-only. It does not implement new formulas, change Phase C formulas, generate production rasters or tensors, call Earth Engine, expose outputs through API or frontend, or change artifact-serving policy.

## Supported Outputs

Phase C1 relation outputs:

- `AI_BEH_VegRoot_REL_ND_DOM_lin_640`
- `AI_BEH_IronOxide_REL_Ratio_DOM_lin_640`
- `AI_BEH_ClayThermal_REL_Ratio_DOM_lin_640`

Phase C2 extended outputs:

- `AI_BEH_GoldAlloy_REL_Ratio_DOM_lin_640`
- `AI_BEH_SilverCopper_REL_Ratio_DOM_lin_640`
- `AI_BEH_ERT_Resistivity_Proxy_DOM_lin_640`

The comparator reads local private `.npy` arrays for those names. Test fixtures may create tiny temporary arrays under pytest temporary directories only. Real frozen notebook references remain external and must not be committed.

## Comparator Behavior

The implementation module is:

`app/pipeline/parity/semantic_feature_comparator.py`

It writes a private JSON report under:

`data/runs/<run_id>/manifests/phase_e3_semantic_feature_comparator.json`

Supported per-output statuses:

- `passed`
- `failed`
- `reference_missing`
- `app_output_missing`
- `comparison_unavailable`
- `skipped_by_request`
- `error`

Overall status is `passed` only when every selected output passes. Missing references are not success. Missing app outputs are not success. Numeric mismatch above tolerance is not success. Shape mismatch is not success.

## Tolerance And NaN Policy

Tolerance is configurable with `atol` and `rtol`.

NaN policy:

- NaN in the same positions may compare as equal.
- NaN position mismatch fails.
- Finite numeric values must compare within tolerance.

## Runtime And Parity Flags

Runtime output presence and notebook-value parity remain separate.

- `runtime_output_verified=true` only when all selected app output arrays are present.
- `notebook_value_parity_verified=true` only when every selected output passes value comparison.
- Any missing reference keeps `notebook_value_parity_verified=false`.
- Any missing app output keeps `runtime_output_verified=false`.

## Safety Boundary

Phase E3 does not:

- add a writer
- create science outputs
- create production raster or tensor artifacts
- call Earth Engine
- start backend runs
- wire anything into the live pipeline
- change existing formulas
- change API, frontend, database, or artifact-serving behavior
- expose private outputs publicly
- add map overlays
- train models or run inference
- implement Phase D, G, H, I, or J follow-up work

The comparator report is private metadata only. It is not a public DTO and must not be used as approval for API, frontend, or artifact-serving exposure.

## Later Work

Future slices may register this comparator inside the broader frozen-reference verifier or add Phase D private map artifact comparison. Those are separate user-approved slices.
