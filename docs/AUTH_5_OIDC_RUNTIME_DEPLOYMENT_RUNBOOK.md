# Auth-5 — Generic OIDC Runtime Deployment Runbook

Date: 2026-06-08
Status: Auth-5 complete — OIDC runtime runbook, smoke-test script, and unit tests validated

## Purpose

Auth-5 makes the Generic OIDC integration deployable and testable in a real runtime
environment. It does not add new auth behavior. It provides:

- Runtime environment variable reference for OIDC deployment
- Safe example configuration using `example.test` domains
- A local smoke-test script (`scripts/auth5_oidc_smoke.py`) that verifies the route
  denies unauthenticated and invalid-token requests, and optionally verifies a real
  token if provided
- Unit tests for the smoke-test script
- Deployment, smoke-test, rollback, and security checklists

## Prerequisites — Prior Auth Slices

All of the following must be closed before deploying with OIDC enabled:

| Slice  | Status    | Key output                                              |
|--------|-----------|---------------------------------------------------------|
| Auth-1 | Complete  | `operator_auth_context.py` — centralized header parsing |
| Auth-2 | Complete  | `operator_auth_trusted_proxy_enabled` gate              |
| Auth-3 | Complete  | `operator_run_authorizations` config-backed store       |
| Auth-4 | Complete  | `operator_token_verifier.py` wired into adapter         |

## Runtime Environment Variables

Set the following in the deployment environment (`.env`, systemd unit, container env, etc.).

### Required for OIDC-enabled deployment

```bash
# Enable the operator private overlay route (default off)
OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED=true

# Set to false when using OIDC (token is the auth mechanism, not proxy headers)
# Set to true only if also running behind a verified upstream proxy
OPERATOR_AUTH_TRUSTED_PROXY_ENABLED=false

# Enable Generic OIDC token verification
OPERATOR_AUTH_OIDC_ENABLED=true

# Your OIDC provider's issuer URL (must match the `iss` claim in tokens)
OPERATOR_AUTH_OIDC_ISSUER_URL=https://your-provider.example.test

# The client ID / audience this backend accepts (must match the `aud` claim)
OPERATOR_AUTH_OIDC_CLIENT_ID=gee-operator-ui

# Your provider's JWKS endpoint (used to fetch public keys for signature verification)
OPERATOR_AUTH_OIDC_JWKS_URI=https://your-provider.example.test/.well-known/jwks.json

# Maps verified OIDC subject (actor_id) to allowed run IDs (JSON object)
# The key must match the `sub` claim in the verified token exactly.
OPERATOR_RUN_AUTHORIZATIONS='{"operator-sub-from-your-provider":["run_id_1","run_id_2"]}'
```

### Safe example values (example.test domains only — not real)

```bash
OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED=true
OPERATOR_AUTH_TRUSTED_PROXY_ENABLED=false
OPERATOR_AUTH_OIDC_ENABLED=true
OPERATOR_AUTH_OIDC_ISSUER_URL=https://auth.example.test
OPERATOR_AUTH_OIDC_CLIENT_ID=gee-operator-ui
OPERATOR_AUTH_OIDC_JWKS_URI=https://auth.example.test/.well-known/jwks.json
OPERATOR_RUN_AUTHORIZATIONS='{"operator-subject-123":["run_screening_01","run_screening_02"]}'
```

**Never commit real issuer URLs, real client IDs, real run IDs, or tokens to the repository.**

## Key Concepts

### OPERATOR_RUN_AUTHORIZATIONS maps actor to run IDs

The `sub` claim from the verified OIDC token becomes the `actor_id`. The backend
checks `operator_run_authorizations[actor_id]` to resolve per-run access.

A verified token alone **does not grant run access**. The backend config must
explicitly list the `actor_id` and the `run_id` in `OPERATOR_RUN_AUTHORIZATIONS`.
Auth-3 remains the final per-run gate regardless of token contents or roles.

Example: a token with `sub=operator-subject-123` will be denied unless
`OPERATOR_RUN_AUTHORIZATIONS` contains `{"operator-subject-123": ["<the-run-id>"]}`.

### Token acquisition is outside Auth-5

Auth-5 does not provide login UI, a provider SDK, or a token acquisition flow.
The token must be obtained outside this application (e.g., via your provider's
authentication flow, a client-side auth library, or a CI/CD credential provider).

The frontend component `OperatorPrivateOverlayPanel` accepts an optional
`operatorAccessToken` prop and forwards it as `Authorization: Bearer <token>`.
How the token is obtained and passed to the component is outside this scope.

### Token security constraints

- **Never store tokens in `localStorage` or `sessionStorage`.**
  Both are accessible to JavaScript running on the same origin and are vulnerable
  to XSS attacks. Use `httpOnly` session cookies or provider-managed storage if
  persistence is needed.
- **Never log raw bearer token values.** Log only redacted actor IDs or `anonymous`.
- **Never persist raw token values** in files, databases, or audit logs.
- **Never include raw token values in API responses.**

## Deployment Checklist

- [ ] Auth-1, Auth-2, Auth-3, Auth-4 are deployed and previously verified.
- [ ] `OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED=true` is set.
- [ ] `OPERATOR_AUTH_OIDC_ENABLED=true` is set.
- [ ] `OPERATOR_AUTH_OIDC_ISSUER_URL` is set to the real provider issuer URL.
- [ ] `OPERATOR_AUTH_OIDC_CLIENT_ID` is set to the real client ID / audience.
- [ ] `OPERATOR_AUTH_OIDC_JWKS_URI` is set to the real JWKS endpoint.
- [ ] `OPERATOR_RUN_AUTHORIZATIONS` contains the correct `sub` → run ID mapping.
- [ ] No tokens, secrets, or credentials are committed to the repository.
- [ ] No `.env` file is committed to the repository.
- [ ] The application has been restarted after setting environment variables.

## Smoke-Test Script

Script location: `scripts/auth5_oidc_smoke.py`

Uses only the Python standard library. No extra dependencies required.
Never prints raw bearer tokens or Authorization header values.

### Modes

| Mode            | Description                                                         |
|-----------------|---------------------------------------------------------------------|
| `no-token`      | No Authorization header → expects 403/denied                        |
| `invalid-token` | Invalid token → expects 403/denied; checks no leaks in body         |
| `valid-token`   | Real token from env var → expects configurable status/outcome        |
| `all`           | Runs no-token + invalid-token + valid-token (skipped if env absent) |
| `self-check`    | Validates arg defaults; no network call                             |

### Quick usage

```bash
# Validate argument parsing (no server needed)
uv run python scripts/auth5_oidc_smoke.py --mode self-check

# Denial smoke tests (server must be running; no token needed)
uv run python scripts/auth5_oidc_smoke.py \
  --base-url http://127.0.0.1:8015 \
  --run-id <your-run-id> \
  --mode no-token

uv run python scripts/auth5_oidc_smoke.py \
  --base-url http://127.0.0.1:8015 \
  --run-id <your-run-id> \
  --mode invalid-token

# Full smoke test including valid token (set token in env, never as CLI arg)
export AUTH5_SMOKE_BEARER_TOKEN="$(your-token-acquisition-command)"
uv run python scripts/auth5_oidc_smoke.py \
  --base-url http://127.0.0.1:8015 \
  --run-id <your-run-id> \
  --mode all
```

### Environment variable overrides

| CLI flag                    | Env var                      | Default                        |
|-----------------------------|------------------------------|--------------------------------|
| `--base-url`                | `AUTH5_SMOKE_BASE_URL`       | `http://127.0.0.1:8015`        |
| `--run-id`                  | `AUTH5_SMOKE_RUN_ID`         | (required unless self-check)   |
| `--artifact-family`         | `AUTH5_SMOKE_ARTIFACT_FAMILY`| `phase_d1_private_geojson`     |
| `--token-env`               | —                            | `AUTH5_SMOKE_BEARER_TOKEN`     |
| `--expected-valid-status`   | —                            | `200`                          |
| `--expected-valid-outcome`  | —                            | `allowed`                      |
| `--timeout-seconds`         | —                            | `10`                           |

### Denial response checks

For any denied response the script verifies the body does not leak:
`preview_payload`, `artifact_family`, `run_id`, `/download/`, `sha256`

### Allowed response checks

For a valid-token allowed response the script verifies:
- `outcome == expected_valid_outcome` (default: `"allowed"`)
- `frontend_visible == "operator_only"` (when present)
- `downloadable_via_api == false` (when present)

## Smoke-Test Checklist

Run after every deployment or config change.

- [ ] `uv run python scripts/auth5_oidc_smoke.py --mode self-check` exits 0.
- [ ] `--mode no-token` returns PASS (server denies unauthenticated request).
- [ ] `--mode invalid-token` returns PASS (server denies bad token).
- [ ] `--mode valid-token` returns PASS with real token (if available).
- [ ] None of the PASS/FAIL lines contain raw token values.
- [ ] Denied response body does not contain run_id, artifact_family, preview_payload.

## Rollback Checklist

If OIDC is causing issues or regressions:

1. Set `OPERATOR_AUTH_OIDC_ENABLED=false` in the deployment environment.
2. Remove `OPERATOR_AUTH_OIDC_ISSUER_URL`, `OPERATOR_AUTH_OIDC_CLIENT_ID`,
   `OPERATOR_AUTH_OIDC_JWKS_URI` from the environment (or leave as unused).
3. Decide whether to keep `OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED=true`
   (trusted-proxy mode only) or set it to `false` (default-off, fully deny).
4. Restart the application.
5. Re-run `--mode no-token` and `--mode invalid-token` smoke tests.
   Both should still return PASS (route should still deny without valid auth).
6. Confirm Auth-1/Auth-2/Auth-3 behavior is intact by running:
   `uv run python -m pytest tests/integration/test_operator_overlay_preview_api.py -v`

## Security Checklist

- [ ] No public overlay or download URL is exposed in any API response.
- [ ] No exact coordinates appear in any operator overlay preview response.
- [ ] No private artifact content (KML, GeoJSON geometry, heatmap points) is returned.
- [ ] No raw bearer token value appears in application logs.
- [ ] No raw bearer token value appears in API responses.
- [ ] `OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED` defaults to `false`; the route
      is inaccessible unless explicitly enabled.
- [ ] `OPERATOR_AUTH_OIDC_ENABLED` defaults to `false`; OIDC is not active
      unless explicitly enabled.
- [ ] A valid token alone cannot grant per-run access without a matching entry in
      `OPERATOR_RUN_AUTHORIZATIONS`.
- [ ] No login/logout UI has been added to the frontend.
- [ ] No tokens are stored in `localStorage` or `sessionStorage`.

## Auth-5 Validation Results

Date: 2026-06-08

### Smoke script syntax check

```
uv run python -m py_compile scripts/auth5_oidc_smoke.py
```

Result: **OK** — no syntax errors.

### Smoke script self-check

```
uv run python scripts/auth5_oidc_smoke.py --mode self-check
```

Result: all 6 default checks pass.

```
PASS  self-check: artifact_family default == 'phase_d1_private_geojson'
PASS  self-check: access_mode default == 'operator_only_preview'
PASS  self-check: token_env default == 'AUTH5_SMOKE_BEARER_TOKEN'
PASS  self-check: expected_valid_status default == 200
PASS  self-check: expected_valid_outcome default == 'allowed'
PASS  self-check: timeout_seconds default == 10
```

### Smoke script unit tests

```
uv run python -m pytest tests/unit/test_auth5_oidc_smoke.py -v
```

Result: **18 passed**, 1 warning — no failures.

### Focused Auth backend validation

```
uv run python -m pytest tests/unit/test_operator_token_verifier.py tests/unit/test_operator_auth_context.py tests/unit/test_config_auth_settings.py tests/unit/test_operator_run_authorization.py tests/integration/test_operator_overlay_preview_api.py -v
```

Result: **68 passed**, 2 warnings — no failures.

### Broad backend regression suite

```
uv run python -m pytest tests/unit/ tests/integration/ -v
```

Result: **482 passed**, 3 warnings — no failures.
(Increase from 464 to 482 reflects the 18 new smoke-script unit tests.)

### Frontend build

```
cd frontend-v2 && npm run build
```

Result: `✓ built in 1.30s` — passed clean.
`frontend-v2/dist/` artifacts unchanged from Auth-4 Step 6 commit.

### Repository state

```
git status --short
```

Result: only `gee_screening_app.egg-info/`, `uv.lock`, `scripts/auth5_oidc_smoke.py`,
and `tests/unit/test_auth5_oidc_smoke.py` untracked — no unexpected changes.
`frontend-v2/dist/` is unchanged (verified via `git ls-files frontend-v2/dist`).

### Confirmed — no violations

- No real tokens, issuer secrets, private keys, `.env`, or credentials committed.
- No login/logout UI added.
- No token storage added (`localStorage`, `sessionStorage`, cookies).
- No Supabase or provider SDK added.
- No backend auth behavior changed (`operator_auth_context.py`, `operator_token_verifier.py`,
  `operator_run_authorization.py`, `operator_overlays.py` all unchanged).
- No frontend source changed (`operatorOverlays.ts`, `OperatorPrivateOverlayPanel.tsx` unchanged).
- No dependencies added (`pyproject.toml` unchanged).
- Auth-1/Auth-2/Auth-3/Auth-4 boundaries remain intact — 68 focused tests confirm.
- No SAR/GRID/H3/H4/notebook parity/screening math files changed.
- No generated/private artifacts committed.
