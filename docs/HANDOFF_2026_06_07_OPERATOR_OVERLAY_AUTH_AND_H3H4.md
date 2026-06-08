# Handoff — Operator Overlay Auth, Slice 13, H3/H4, and D1 State

Date: 2026-06-07

This handoff summarizes the session state after completing Slice 13 closeout, D1 scaffold, the operator overlay frontend panel/client hook, and the documentation closeout. It also records the current auth-integration finding and the preferred next step.

## Current Repository State

Recent completed work on `main` includes:

```text
[x] Slice 13A — private candidate register scaffold
[x] Slice 13B — first source review through the six gates
[x] Slice 13C — DAFA-LS sensitivity/misuse decision
[x] Slice 13D — arXiv:2602.19608 source review
[x] Slice 13E — current known-lead source approval closeout
[x] Slice 13 acceptable-source spec
[x] Slice 13 acceptable-source spec linked from governance docs
[x] D1 — frozen notebook reference bundle scaffold and operator collection plan
[x] G2 operator private overlay frontend panel/client hook
[x] G2 frontend panel/client hook documentation closeout
```

The roadmap now treats the operator overlay frontend/client hook as complete and leaves the remaining G2 integration work as real auth-provider / authorization wiring.

## H3 / H4 Status

H3 training and H4 private inference remain blocked.

Current ML/data state:

```text
approved_dataset_source = none
i2_pack = none
ready_for_private_training_later = false
h3_training_allowed = false
h4_private_inference_allowed = false
```

Why blocked:

- Slice 13 closed the current known public-lead set.
- DAFA-LS / `arXiv:2409.09432` was rejected at Gate 1.
- `arXiv:2602.19608` was rejected at Gate 1.
- No source is `conditionally_approved_for_I2`.
- No I2 pack exists.
- No H3/H4 work may begin until a future candidate passes Slice 13-style source approval and then the I2 validator returns `ready_for_private_training_later`.

The acceptable-source spec now defines what future evidence must look like before opening another Slice 13 review:

```text
docs/FUTURE_SLICE_13_ACCEPTABLE_SOURCE_SPEC.md
```

Plain-English unlock condition:

```text
A future source must be safe enough not to become a sensitive-location targeting map, and its labels must be independent of the heuristic and input stack being modeled.
```

## Frozen Notebook Reference Status

D1 is complete as a scaffold and operator collection plan only.

Current parity/reference state:

```text
reference_bundle_scaffold = complete
real_frozen_references_collected = false
notebook_value_parity_verified = false
```

Important constraints:

- Real frozen references remain operator-owned and outside git.
- Missing references are not success.
- Notebook-value parity must not be marked true until Phase E/E3/E4 verifiers pass against real private references.
- No reference artifacts should be committed.

D1 documentation:

```text
docs/FUTURE_SLICE_D1_FROZEN_REFERENCE_BUNDLE_COLLECTION_PLAN.md
```

## Operator Overlay Frontend Status

The operator overlay frontend panel/client hook is complete.

Implemented frontend files:

```text
frontend-v2/src/app/api/operatorOverlays.ts
frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx
frontend-v2/src/app/components/SettingsPage.tsx
frontend-v2/src/app/App.tsx
```

Behavior:

- Default-off local UI setting.
- Panel appears in the selected-run view only when enabled.
- Calls the backend route:

```text
GET /runs/{run_id}/operator/private-overlays?artifact_family=...&access_mode=operator_only_preview
```

- Frontend does not set or fabricate `X-Operator-*` headers.
- Frontend handles allowed / not_available / denied / error states.
- Frontend displays coordinate-free preview summaries only.
- No public download button, public overlay, map layer, geometry rendering, exact coordinate display, path display, or hash display.

Build verification supplied by operator:

```text
cd frontend-v2
npm run build
# passed
```

## Current Auth Finding

The backend route currently reads the operator context directly from request headers:

```text
X-Operator-Authenticated
X-Operator-Id
X-Operator-Roles
X-Operator-Authorized-Runs
X-Request-Id
```

Those headers are parsed inside:

```text
app/api/operator_overlays.py
```

and then passed into:

```text
app/services/operator_overlay_preview.py
```

The app is still local-first. The README states v1 has no PostgreSQL, Supabase, Redis, Celery, RQ, arq, or separate worker requirement. Therefore, do not suddenly introduce Supabase/OIDC/auth-provider dependencies unless the user explicitly approves a larger architecture change.

## Recommended Next Auth Step

Do not jump straight to a full auth provider.

Recommended next slice:

```text
Auth-1 — operator auth context adapter, no provider yet
```

Purpose:

```text
Move operator identity parsing out of the overlay route into one backend adapter, while keeping current behavior and failing closed.
```

Target shape:

```text
OperatorAuthContext:
  actor_id
  is_authenticated
  roles
  authorized_run_ids
  request_id
```

Recommended new module:

```text
app/services/operator_auth_context.py
```

Conceptual flow after Auth-1:

```text
operator_overlays.py
  -> resolve_operator_auth_context(request)
  -> build_operator_overlay_preview(...auth_context fields...)
```

Auth-1 does not add a real provider. It only centralizes the current trusted-header parsing behind a stable adapter boundary.

Auth-1 must preserve:

```text
- backend default-off behavior
- redacted denial responses
- audit event on every allow/deny decision
- no public overlay exposure
- no public downloads
- no artifact-serving policy change
- no frontend changes
- no Supabase/OIDC dependency
- no H3/H4 or ML work
```

Later auth steps, only after Auth-1:

```text
Auth-2 — trusted proxy mode / settings gate
Auth-3 — per-run authorization source/store
Auth-4 — real provider integration, only if explicitly approved
```

## Blocked Items

```text
[blocked] H3 training
[blocked] H4 private inference
[blocked] public location overlay exposure
[blocked] notebook-value parity against real references
[blocked] full real auth provider integration until Auth-1/Auth-2/Auth-3 decisions are made
```

Reasons:

- H3/H4: no approved dataset source and no I2-ready pack.
- Public overlay exposure: requires a separate explicit use/misuse, redaction, access-control, audit, and serving-policy review.
- Notebook-value parity: real frozen references are absent.
- Real auth provider: current best next step is an adapter, not a provider jump.

## How We Worked In This Session

The working pattern was:

1. Identify the next item from the documented roadmap/checklist.
2. If a proposed item was not in the checklist, stop and add it to the plan first.
3. Use small scoped goals.
4. Keep every goal constrained by allowed files, forbidden files, tests, and safety boundaries.
5. Validate with focused tests and broad tests/builds when possible.
6. Commit to `main` only after the user approved the scope.
7. Never force-push.
8. If a task is blocked by missing real-world data, say it is blocked instead of pretending code can solve it.

The user expects the assistant to act as an orchestrator:

```text
- choose the safest next documented step
- explain why in plain English
- do not expand the roadmap silently
- ask/tell before adding new sub-slices
- produce Codex-style goals when implementation is needed
- verify commits/results when the user reports completion
- keep public exposure, coordinates, dataset, ML, and auth boundaries explicit
```

## Prompt Style Used

Implementation prompts should be structured like this:

```text
/goal <one slice only>

Repo / branch / sync rules
MUST READ FIRST
SCOPE
Purpose
Do not...
Required behavior
Suggested files
Required tests
Allowed files
Do not modify
Validation commands
Before commit checks
Commit message
Push rules
Final report requirements
```

Important prompt expectations:

- One slice only.
- No hidden adjacent work.
- No public exposure unless explicitly approved.
- No generated/private artifacts committed.
- No H3/H4 unless the data gates are actually satisfied.
- No new auth provider dependency unless explicitly approved.
- Use direct, plain English when the user asks for explanation.

## Next Session Starting Point

Start by asking which path the user wants:

```text
A. Auth-1 — operator auth context adapter, no provider yet
B. Real frozen reference collection outside git, if the operator has files
C. New Slice 13-style source review, if the operator has a Gate-1-clean source
D. Public overlay exposure review, still blocked and requires explicit approval
```

Recommended default:

```text
A. Auth-1 — operator auth context adapter, no provider yet
```

Do not proceed directly to real provider wiring until Auth-1 is complete and the user approves the next auth slice.
