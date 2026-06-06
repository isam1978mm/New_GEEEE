# Special Track G2 Operator-Only Overlay UI Design

Special Track G2 is a design and policy boundary phase only.

It does not implement overlay UI. It does not expose generated private overlays.
It does not make overlays public. It does not add API routes, frontend controls,
public downloads, map tiles, or artifact-serving changes.

## Relationship To Phase A

Phase A shows the operator-selected starting point and ROI/GRID preview before
backend outputs exist.

G2 is different. G2 is for a later UI that may display generated private overlay
results after outputs exist. That later UI remains blocked until authentication,
role checks, per-run authorization, audit logging, redacted denial responses,
and default-off configuration are implemented in small user-approved slices.

## Source Of Truth

The G2 policy helper is:

```text
app/pipeline/parity/operator_overlay_ui_policy.py
```

It writes a private policy report only:

```text
data/runs/<run_id>/manifests/special_track_g2_operator_overlay_ui_policy.json
```

The report is metadata only. It must not create KMZ, KML, GeoJSON, HTML, image,
raster, NPY, coordinate, classifier, model, public overlay, or UI output
artifacts.

## Modes

### disabled_default

- Default state.
- Generated overlays are not visible in UI.
- No API exposure.
- No frontend exposure.
- No artifact-serving change.

### operator_only_preview

- Future allowed mode only after implementation approval.
- Requires authentication.
- Requires operator role.
- Requires per-run authorization.
- Requires audit logging.
- Requires default-off configuration.
- Not public.
- No public downloads.

### redacted_denied

- Used when a user lacks permission.
- Must not reveal generated overlay presence.
- Must not include exact coordinates, raw geometry, bounds, local paths, private
  hashes, or artifact contents.

### future_public_review_required

- Public exposure remains blocked.
- Requires separate user approval and artifact-serving policy review.
- Not part of G2 implementation.

## Required Future Gates

Any later operator-only preview implementation must include:

- authentication
- operator role checks
- per-run authorization
- default-off configuration
- audit logging for allow and deny paths
- redacted denial responses
- private DTO schema review
- no public downloads by default

## Private Overlay DTO Boundary

A future private overlay DTO may include generated overlay content only after all
operator-only gates pass. Public DTOs remain redacted and must not include exact
coordinates, raw geometry, bounds, local paths, private hashes, or artifact
contents.

## Safety Boundary

G2 does not:

- implement overlay UI
- expose generated private overlays
- make overlays public
- change API, frontend, database, or artifact-serving behavior
- call Earth Engine
- start backend runs
- generate map artifacts
- change raster or math logic
- change classifier, model, or training logic
- implement Special Track H, I, or J behavior

Future implementation must be split into small user-approved slices. A sensible
first slice would be authentication and role policy, followed by per-run
authorization, audit logging, private DTO review, frontend preview review, and
serving-policy review.
