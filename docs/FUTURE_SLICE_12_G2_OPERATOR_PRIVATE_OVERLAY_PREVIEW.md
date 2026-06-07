# Future Slice 12 / G2 Operator-Only Private Overlay Preview

## Scope

Future Slice 12 implements an operator-only private overlay preview path using the
Slice 11 access/audit foundation. It is operator-only private preview, not public
overlay exposure.

Future Slice 12 is default-off. It requires authentication, operator role, per-run
authorization, and an audit event on every decision. It does not expose overlays
publicly. It does not add public downloads. It does not change artifact-serving
policy. It does not call Earth Engine. It does not generate artifacts. It does not
train or run inference. Public overlay exposure remains out of scope and requires
separate approval.

The binding context is `docs/FUTURE_SLICE_10_G2_IMPLEMENTATION_DESIGN.md`,
`docs/FUTURE_SLICE_11_G2_AUTH_ROLE_AUDIT_FOUNDATION.md`,
`docs/SPECIAL_TRACK_G2_OPERATOR_ONLY_OVERLAY_UI_DESIGN.md`, and
`docs/SPECIAL_TRACK_G_EXACT_COORDINATE_OVERLAY_ACCESS_CONTROL.md`.

## Backend Route

A default-off route is added:

```text
GET /runs/{run_id}/operator/private-overlays?artifact_family=...&access_mode=operator_only_preview
```

- Implementation: `app/api/operator_overlays.py`,
  `app/services/operator_overlay_preview.py`,
  `app/schemas/operator_overlays.py`.
- The route is registered in `app/main.py`.
- The route stays default-off through the config flag
  `OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED` (`Settings.operator_private_overlay_preview_enabled`,
  default `false`). When disabled, every request is denied regardless of headers.
- Operator identity, role, and per-run authorization are supplied by an upstream
  authenticated context, mapped here from request headers
  (`X-Operator-Authenticated`, `X-Operator-Id`, `X-Operator-Roles`,
  `X-Operator-Authorized-Runs`, `X-Request-Id`). Wiring these headers to a real
  authentication provider is a later integration step.

## Access Gates

The route enforces every Slice 11 gate via `evaluate_overlay_access`, in order:
default-off enablement, authentication, operator role, per-run authorization,
access mode (`operator_only_preview` only), and allowed artifact family. Access is
allowed only when all gates pass. Denied modes are `redacted_public`,
`public_exact_coordinate`, and any unknown or unsupported mode.

Supported private artifact families: Phase D1 private GeoJSON
(`phase_d1_private_geojson`), Phase D2 private KMZ (`phase_d2_private_kmz`), and
Phase D3 private heatmap JSON (`phase_d3_private_heatmap_json`).

## Private Preview Loading

On an allowed decision the service reads only the requested private artifact under
the run directory, using a run-relative path that rejects traversal and absolute
paths. It returns a coordinate-free operator-only preview:

- GeoJSON: feature count and the neutral set of geometry kinds present.
- KMZ: `doc.kml` placemark count.
- Heatmap JSON: point count and a scalar weight summary (min/max/mean).

The preview payload carries no exact coordinates, raw geometry, KML contents, local
filesystem paths, private hashes, public download URLs, or artifact-serving URLs. A
missing artifact for an authorized operator returns a safe operator-only
`not_available` outcome; the denial path never reads any artifact file. Because all
JSON responses pass the application redaction boundary, the preview is intentionally
coordinate-free; an operator coordinate display would require a separate
later-approved private channel and is out of scope here.

## Audit Behavior

Every allow or deny decision builds an audit event with the Slice 11 policy
(`event_type`, `actor_id`, `run_id`, `artifact_family`, `access_mode`,
`access_outcome`, `timestamp`, `reason_code`, `request_id`,
`client_context_redacted`). The audit event excludes exact coordinates, raw
geometry, KML contents, heatmap point payloads, local filesystem paths, private
hashes, artifact contents, and download URLs. The success response carries only a
minimal audit summary.

## Redacted Denial Behavior

Denied requests return HTTP 403 with a generic, identical body for every denial
cause (`outcome=denied`, generic `status`/`reason_code`/`message`, `retry_allowed`,
`support_reference`). It does not reveal artifact existence and excludes exact
coordinates, raw geometry, bounds, KML contents, heatmap point payloads, local
paths, private hashes, artifact contents, download URLs, and content-revealing file
names. The denial path reads no artifact file.

## Frontend

The operator-only frontend panel (`OperatorPrivateOverlayPanel`) is left pending.
This slice implements the backend route, service, schemas, and tests only, and does
not modify frontend files or built assets. The panel and client hook remain a later
step, kept hidden/default-off with redacted denial display and no public download or
overlay layer.

## Safety Boundary

Future Slice 12 does not add public overlay exposure, public downloads, public
exact-coordinate mode, or artifact-serving changes. It does not make private
GeoJSON/KMZ/heatmap artifacts downloadable through the existing artifact-serving
endpoints. It does not remove default-off behavior, bypass auth/role/per-run checks,
or bypass audit event creation. It does not call Earth Engine, start backend runs,
generate rasters or NPY files, change raster/math logic, train models, run inference,
download weights, or add ML dependencies. Public overlay exposure remains out of
scope and requires separate explicit approval.
