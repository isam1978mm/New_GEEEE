# Future Slice 11 / G2 Auth, Role, And Audit Foundation

## Scope

Future Slice 11 adds the backend-internal access-control and audit foundation for
the future operator-only private overlay route designed in Future Slice 10. It adds
auth/role/audit foundation only.

Future Slice 11 does not implement the overlay API route. It does not implement
frontend UI. It does not expose generated private overlays. It does not expose exact
coordinates publicly. It does not read or serve private artifact files. It does not
change artifact serving. It does not call Earth Engine. It does not generate map
artifacts.

The binding context is `docs/FUTURE_SLICE_10_G2_IMPLEMENTATION_DESIGN.md`,
`docs/SPECIAL_TRACK_G2_OPERATOR_ONLY_OVERLAY_UI_DESIGN.md`, and
`docs/SPECIAL_TRACK_G_EXACT_COORDINATE_OVERLAY_ACCESS_CONTROL.md`.

## Source Of Truth

The foundation helper is:

```text
app/pipeline/parity/operator_overlay_access_foundation.py
```

It writes one private JSON report:

```text
data/runs/<run_id>/manifests/future_slice_11_g2_auth_role_audit_foundation.json
```

The report path stays under `run_dir`. The helper creates no map artifacts,
coordinates, rasters, NPY files, model files, datasets, labels, chips, or public
outputs, and it opens no private artifact file.

## Access Decision Behavior

`evaluate_overlay_access(request)` answers whether an operator-only private overlay
preview is allowed. It fails closed and checks gates in this order:

1. operator overlay preview enabled (default-off) — else `denied_default_off`
2. authenticated — else `denied_unauthenticated`
3. operator role present — else `denied_missing_operator_role`
4. per-run authorization (explicit `authorization_result` or `run_id` in
   `authorized_run_ids`) — else `denied_run_not_authorized`
5. access mode is a blocked public exposure mode — `denied_public_exposure_blocked`
6. access mode is not `operator_only_preview` — `denied_unsupported_access_mode`
7. requested artifact family not allowed — `denied_unsupported_artifact_family`
8. otherwise `allowed_operator_preview`

Access is allowed only when every gate passes: enabled, authenticated, operator
role, per-run authorized, allowed artifact family, and `operator_only_preview` mode.
Allowed artifact families are Phase D1 private GeoJSON, Phase D2 private KMZ, and
Phase D3 private heatmap JSON. The denied access modes are `redacted_public`,
`public_exact_coordinate`, and any unknown or unsupported mode.

Every decision sets `audit_required=true`, carries a redacted actor identifier,
keeps `public_exposure_changes=false` and `artifact_serving_changes=false`, and
opens no artifact file.

## Allowed / Denied Statuses

`allowed_operator_preview`, `denied_default_off`, `denied_unauthenticated`,
`denied_missing_operator_role`, `denied_run_not_authorized`,
`denied_unsupported_artifact_family`, `denied_unsupported_access_mode`, and
`denied_public_exposure_blocked`.

## Redacted Denial Behavior

`build_redacted_denial_response(decision)` returns a generic, identical body for
every denial cause so it cannot reveal whether a run or private artifact exists. It
includes only `status`, `reason_code`, `request_id`, `message`, `retry_allowed`, and
`support_reference`, with a single generic reason code. It must not include exact
coordinates, raw geometry, bounds, KML contents, heatmap point payloads, local
paths, private hashes, artifact contents, private artifact existence, download URLs,
or content-revealing file names. The granular internal reason code stays in the
server-side decision and the private audit event only.

## Audit Event Behavior

`build_audit_event(decision, actor_id=...)` builds a private audit event for every
decision (allow and deny). Fields: `event_type`, `actor_id`, `run_id`,
`artifact_family`, `access_mode`, `access_outcome`, `timestamp`, `reason_code`,
`request_id`, and `client_context_redacted`. The audit event must not include exact
coordinates, raw geometry, KML contents, heatmap point payloads, local filesystem
paths, private hashes, artifact contents, or download URLs.

## Default-Off Behavior

Access remains denied by default unless `operator_overlay_preview_enabled` is true.
The default-off gate is checked first, so a disabled preview denies access even for
an otherwise fully authorized operator request.

## Safety Boundary

Future Slice 11 does not:

- add an API endpoint serving generated private overlay geometry
- add frontend overlay UI, map tiles, public overlays, or public downloads
- change artifact-serving or auth runtime behavior, or create database migrations
- expose exact coordinates publicly or expose private GeoJSON/KMZ/heatmap artifacts
  through HTTP
- return private artifact contents or read any private artifact file
- call Earth Engine or start backend runs
- generate map artifacts, rasters, or NPY files
- train models, run inference, download weights, or add ML dependencies
- implement Future Slice 12

Future Slice 12 should implement the operator-only private overlay preview only
after this foundation passes, keeping default-off, redacted denials, and no public
exposure.
