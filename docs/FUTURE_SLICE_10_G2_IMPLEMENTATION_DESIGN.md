# Future Slice 10 / G2 Implementation Design Details

## Scope

Future Slice 10 specifies the detailed implementation contract for a later
operator-only private generated-overlay UI that can view generated private overlay
results after private artifacts exist.

Future Slice 10 is design/details only. It does not implement API routes. It does
not implement frontend UI. It does not expose private overlays. It does not expose
exact coordinates publicly. It does not change artifact serving. It does not call
Earth Engine. It does not generate map artifacts. The operator-only overlay UI
remains blocked until Future Slice 11 and Future Slice 12.

The binding context is `docs/SPECIAL_TRACK_G2_OPERATOR_ONLY_OVERLAY_UI_DESIGN.md`,
the access-control boundary in
`docs/SPECIAL_TRACK_G_EXACT_COORDINATE_OVERLAY_ACCESS_CONTROL.md`, and the private
map artifact contract in `docs/PHASE_6_PRIVATE_MAP_ARTIFACT_PARITY_CONTRACT.md`.

## Source Of Truth

The design helper is:

```text
app/pipeline/parity/operator_overlay_implementation_design.py
```

It writes one private JSON report:

```text
data/runs/<run_id>/manifests/future_slice_10_g2_implementation_design.json
```

The report path stays under `run_dir`. The helper creates no map artifacts,
coordinates, rasters, NPY files, model files, datasets, labels, chips, or public
outputs.

## Design Distinction

- Phase A shows the operator-entered or clicked point and ROI/GRID preview before
  outputs exist.
- G2 future implementation shows generated private overlay results after private
  artifacts exist.
- G2 is operator-only, not public.

The later access mode is `operator_only_preview`. The blocked modes are
`redacted_public` and `public_exact_coordinate`.

## Backend Route Design Summary

A future, not-yet-implemented route is specified, design only:

- `route_name`: `operator_private_overlays`
- `method`: `GET`
- `path`: `/runs/{run_id}/operator/private-overlays`
- `auth_required`, `operator_role_required`, `per_run_authorization_required`,
  `audit_log_required`, and `default_off_required` are all required
- `allowed_artifact_families`: Phase D1 private GeoJSON, Phase D2 private KMZ, Phase
  D3 private heatmap JSON
- `forbidden_artifact_families`: any public/redacted-public/public-exact-coordinate
  overlay family
- `request_fields`: `run_id`, `artifact_family`, `access_mode`
- `response_fields` (operator-only success, permissible only after gates):
  `run_id`, `artifact_family`, `access_mode`, `operator_overlay_payload_ref`,
  `audit_event_id`
- `redacted_denial_fields`: `outcome`, `reason_code`, `request_id`
- `serving_policy`: operator-only preview, filesystem-only artifacts, not public
  HTTP, no public download, artifact-serving policy unchanged
- `implementation_allowed_now`: false; `required_future_slice`: Future Slice 12

This route is not implemented in Future Slice 10.

## Frontend Panel Design Summary

A future, not-yet-implemented panel is specified, design only:

- `component_or_panel_name`: `OperatorPrivateOverlayPanel`
- `visibility_rule`: visible only to an authenticated operator with per-run
  authorization after private artifacts exist
- `default_state`: `hidden_default_off`
- `operator_role_required`, `run_authorization_required`, and `audit_event_required`
  are all required
- `artifact_family_tabs`: the three Phase D private families
- `allowed_display_modes`: `operator_only_preview`
- `forbidden_display_modes`: `redacted_public`, `public_exact_coordinate`
- `redaction_behavior` and `error_and_denial_behavior` use generic redacted
  denials with no presence leak and no coordinates, geometry, paths, or hashes
- `implementation_allowed_now`: false; `required_future_slice`: Future Slice 12

This panel is not implemented in Future Slice 10.

## DTO And Redaction Policy Summary

- The operator-only success DTO may include a private overlay payload reference
  only after the authentication, operator-role, per-run-authorization, audit, and
  default-off gates exist.
- The redacted denial DTO carries only `outcome`, `reason_code`, and `request_id`,
  and must not reveal overlay presence.
- The public/redacted DTO must never include exact coordinates, raw geometry,
  bounds, KML contents, heatmap point payloads, local paths, private hashes,
  download URLs, or private artifact contents.

## Audit Policy Summary

Audit events carry `event_type`, `actor_id`, `run_id`, `artifact_family`,
`access_mode`, `access_outcome`, `timestamp`, `reason_code`, `request_id`, and
`client_context_redacted`. Audit records must not include exact coordinates, raw
geometry, KML contents, heatmap point payloads, local filesystem paths, private
hashes, or artifact contents. Both allow and deny events are required.

## Config / Default-Off Policy Summary

The proposed configuration key `operator_private_overlay_preview_enabled` defaults
to `false`. No configuration is added now; `config_added_now` and
`implementation_allowed_now` are both false. The overlay UI stays default-off even
after a future implementation slice exists.

## Required Tests Before Implementation

Before any later implementation, tests must cover authentication, operator role,
per-run authorization, audit allow/deny events with redaction, default-off
configuration, redacted denial without presence leak, public-exposure blocking, and
no artifact-serving change.

## Future Slice Plan

- Future Slice 11 should implement the auth/role/audit foundation, including
  authentication, operator role, per-run authorization, audit logging, and
  default-off configuration. It exposes no overlay payload.
- Future Slice 12 should implement the operator-only private overlay preview route
  and panel only after Future Slice 11 passes, keeping default-off, redacted
  denials, and no public exposure.

## Safety Boundary

Future Slice 10 does not:

- add an API endpoint serving generated private overlay geometry
- add frontend overlay UI, map tiles, public overlays, or public downloads
- change artifact-serving or auth runtime behavior
- create database migrations
- expose exact coordinates publicly or expose private GeoJSON/KMZ/heatmap artifacts
  through HTTP
- call Earth Engine or start backend runs
- generate map artifacts, rasters, or NPY files
- train models, run inference, download weights, or add ML dependencies
- implement Future Slice 11 or Future Slice 12

The operator-only overlay UI remains blocked until Future Slice 11 and Future Slice
12.

## Cross-Reference: Future Slice 11 Foundation

The backend-internal access-control and audit foundation for this design is
implemented in `docs/FUTURE_SLICE_11_G2_AUTH_ROLE_AUDIT_FOUNDATION.md` and
`app/pipeline/parity/operator_overlay_access_foundation.py` (foundation only). That
cross-reference does not change or weaken any gate in this document; it adds no API
route, no frontend UI, no artifact-serving change, and no public exposure, and the
operator-only overlay preview remains blocked until Future Slice 12.
