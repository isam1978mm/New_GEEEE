# Special Track G1 Exact-Coordinate Overlay Access Control

Special Track G1 is a design and policy boundary phase only.

It does not expose exact coordinates publicly. It does not add public overlays,
map tiles, frontend previews, API endpoints, public downloads, or artifact
serving changes.

## Purpose

Exact-coordinate overlay means any map layer, geometry file, tile, preview, or
DTO that includes precise point, line, polygon, bounds, or GRID-derived location
content tied to a run.

Private filesystem-only exact-coordinate artifacts remain allowed only under the
existing private run-directory boundary. They are not HTTP served, not visible in
the frontend, and not downloadable through API.

## Source Of Truth

The G1 policy helper is:

```text
app/pipeline/parity/exact_coordinate_overlay_policy.py
```

It writes a private policy report only:

```text
data/runs/<run_id>/manifests/special_track_g_exact_coordinate_overlay_policy.json
```

The report is metadata only. It must not create KMZ, KML, GeoJSON, HTML, image,
raster, NPY, coordinate, classifier, model, or public overlay artifacts.

## Access Modes

### private_filesystem_only

- Exact coordinates may exist only in private files under `run_dir`.
- `http_servable=false`
- `frontend_visible=false`
- `downloadable_via_api=false`
- This is the only current boundary that allows exact-coordinate content.

### operator_only_authenticated

- Exact coordinates may be visible only to an authorized operator role.
- This mode requires authentication, role checks, per-run authorization, and
  audit logging before implementation.
- It is disabled by default.
- It requires explicit future user approval.

### redacted_public

- No exact coordinates.
- No raw geometry.
- No bounds.
- No local paths.
- No private hashes.
- May show generalized summary metadata only after a future schema review.
- It requires explicit future user approval.

### public_exact_coordinate

- Not allowed by default.
- Requires explicit user approval in a later implementation phase.
- Requires access-control design, audit logging, frontend review, and
  artifact-serving policy review before implementation.

## DTO Boundary

Public DTOs must not include:

- exact coordinate values
- raw geometry
- bounds
- local filesystem paths
- private hashes
- download references for private coordinate artifacts

Public summaries may later include only generalized metadata such as artifact
type, feature count, redaction status, and serving flags after a separate schema
review.

## Role And Permission Policy

Operator-only overlay mode requires:

- authentication
- operator role
- per-run authorization
- default-off configuration
- audit logging
- redacted denial responses

Loopback-only app behavior is not enough for public exact-coordinate exposure.

## Audit Logging Policy

Any future operator-only or public exact-coordinate access must log:

- actor identifier
- run identifier
- action type
- access outcome
- timestamp

Audit payloads must omit exact coordinates, raw geometry, local paths, private
hashes, and private artifact contents.

## Artifact Serving Boundary

Special Track G1 makes no artifact-serving change.

Future exact-coordinate serving would require a separate user-approved phase and
a serving-policy review. Existing private coordinate artifacts remain blocked
from HTTP serving by default.

## Future Implementation Slices

Future work must be split into small user-approved slices:

- access-control implementation
- audit logging implementation
- public-safe DTO schema review
- operator-only frontend preview review
- artifact-serving policy review
- public overlay exposure decision

Special Track H, I, and J remain separate. G1 does not implement deep-learning,
training, or full Tesla flow decomposition behavior.
