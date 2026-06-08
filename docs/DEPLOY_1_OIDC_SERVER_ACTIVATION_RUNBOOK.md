# Deploy-1 — Generic OIDC Server Activation Runbook

Date: 2026-06-08
Status: Deploy-1 complete — OIDC server activation packet prepared

## Purpose

Deploy-1 packages everything an operator needs to safely activate and verify
Generic OIDC on the live/server runtime. It does not add auth code, login UI,
a provider SDK, or Supabase. It provides:

- This server activation runbook (exact env + command sequence)
- A safe `.env` template (`docs/examples/oidc-runtime.env.example`)
- An environment sanity-check script (`scripts/deploy1_oidc_env_check.py`) that
  prints no secrets or tokens
- Unit tests for the sanity-check script
- Activation, smoke-test, and rollback command sequences
- Troubleshooting guidance

No real provider values, tokens, or `.env` files are committed.

## Preconditions

Before activating OIDC on the server, confirm:

- [ ] Auth-1 through Auth-5 are closed (see their plan/runbook docs).
- [ ] The server has the current `main` branch pulled.
- [ ] The app starts locally / on the server without errors.
- [ ] The operator has real OIDC issuer URL, client ID / audience, and JWKS URI.
- [ ] The operator can obtain a real bearer token **outside** this app
      (provider auth flow, client library, or CI/CD credential).
- [ ] The operator knows the OIDC `sub` (subject) value for each authorized operator.

## Server-Safe Environment Variables

Set these on the server (untracked `.env`, systemd unit, or container env).
See `docs/examples/oidc-runtime.env.example` for the annotated template.

```bash
OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED=true
OPERATOR_AUTH_TRUSTED_PROXY_ENABLED=false
OPERATOR_AUTH_OIDC_ENABLED=true
OPERATOR_AUTH_OIDC_ISSUER_URL=<real issuer URL>
OPERATOR_AUTH_OIDC_CLIENT_ID=<real client ID / audience>
OPERATOR_AUTH_OIDC_JWKS_URI=<real JWKS URI>
OPERATOR_RUN_AUTHORIZATIONS='{"<oidc-sub>":["<run-id>"]}'
```

**Never paste real values into the repository or any committed file.**

## Finding the OIDC Subject (`sub`)

The `OPERATOR_RUN_AUTHORIZATIONS` keys must match the verified token's `sub` claim.
To find it safely:

- Use your **provider admin UI** (user/identity detail page) to read the subject, OR
- Decode a token **locally only** (e.g. paste into a local offline JWT decoder, or
  `python -c` with the base64 payload) and read the `sub` field.

Rules:
- Do **not** paste any token into the repository or any committed file.
- Do **not** commit decoded token output or claims.
- Use the `sub` value only to populate `OPERATOR_RUN_AUTHORIZATIONS` on the server.

## Activation Flow (exact sequence)

Run on the server, from the repo root.

```bash
# 1. Pull latest
git pull origin main

# 2. Install / update dependencies
uv sync

# 3. Set environment (untracked .env or exported in the service environment)
#    Use docs/examples/oidc-runtime.env.example as the template.

# 4. Sanity-check the environment (prints no secrets/tokens)
uv run python scripts/deploy1_oidc_env_check.py --strict

# 5. Restart the app (use your process manager; example only)
#    systemctl restart gee-app    # or your container/orchestrator restart

# 6. Smoke test: no-token must be denied
uv run python scripts/auth5_oidc_smoke.py \
  --base-url http://127.0.0.1:8015 \
  --run-id <run-id> \
  --mode no-token

# 7. Smoke test: invalid-token must be denied
uv run python scripts/auth5_oidc_smoke.py \
  --base-url http://127.0.0.1:8015 \
  --run-id <run-id> \
  --mode invalid-token

# 8. Provide a real token ONLY in the shell environment (never as a CLI arg,
#    never committed). Acquire it via your provider flow.
export AUTH5_SMOKE_BEARER_TOKEN="$(your-token-acquisition-command)"

# 9. Smoke test: valid-token should be allowed (when subject/run authorized)
uv run python scripts/auth5_oidc_smoke.py \
  --base-url http://127.0.0.1:8015 \
  --run-id <run-id> \
  --mode valid-token

# 10. Unset the token immediately after
unset AUTH5_SMOKE_BEARER_TOKEN
```

## Rollback Flow (exact sequence)

If OIDC causes problems:

```bash
# 1. Disable OIDC
#    Set OPERATOR_AUTH_OIDC_ENABLED=false in the server environment.

# 2. Remove OIDC env vars (issuer, client id, jwks uri) from the environment.

# 3. Restart the app
#    systemctl restart gee-app    # or your restart mechanism

# 4. Re-run denial smoke tests — both must still PASS (route still denies)
uv run python scripts/auth5_oidc_smoke.py --base-url http://127.0.0.1:8015 --run-id <run-id> --mode no-token
uv run python scripts/auth5_oidc_smoke.py --base-url http://127.0.0.1:8015 --run-id <run-id> --mode invalid-token
```

With OIDC disabled, the route falls back to the Auth-2 trusted-proxy gate. If
`OPERATOR_AUTH_TRUSTED_PROXY_ENABLED` is also false, the route is fully default-off.

## Security Checks

- [ ] No raw bearer token appears in any application log.
- [ ] No `.env` file is committed.
- [ ] No public overlay or download URL is present in any response.
- [ ] Denied responses do **not** contain `run_id`, `artifact_family`, or `preview_payload`.
- [ ] Auth-3 (`OPERATOR_RUN_AUTHORIZATIONS`) remains the final per-run gate —
      a valid token alone does not grant run access.
- [ ] `scripts/deploy1_oidc_env_check.py` output shows no full secrets or subjects.

## Troubleshooting

| Symptom                                  | Likely cause                                                                 |
|------------------------------------------|------------------------------------------------------------------------------|
| 403 with a valid token                   | `OPERATOR_RUN_AUTHORIZATIONS` is missing the token's `sub` or the run ID.     |
| 403 with reason resembling invalid_token | Issuer/audience/JWKS mismatch, or the token is expired or malformed.          |
| no-token request returns 200             | Misconfiguration — investigate immediately; the route must deny no-token.     |
| invalid-token request returns 200        | Misconfiguration — investigate immediately; the route must deny bad tokens.   |
| Frontend shows denied even when authorized | The caller did not supply the `operatorAccessToken` prop to the panel.       |

Note: the frontend will not authenticate via OIDC unless the caller supplies the
already-obtained token through the `operatorAccessToken` prop. Token acquisition
and login UI are intentionally outside this scope.

## Final Acceptance Checklist

- [ ] `deploy1_oidc_env_check.py --strict` exits 0 on the server.
- [ ] no-token smoke returns PASS (denied).
- [ ] invalid-token smoke returns PASS (denied).
- [ ] valid-token smoke returns PASS (allowed for an authorized subject/run).
- [ ] Denied responses leak no run_id/artifact_family/preview_payload.
- [ ] No token value appears in logs or command output.
- [ ] Rollback verified to still deny without valid auth.

## Deploy-1 Validation Results

Date: 2026-06-08

### Env-check script syntax + help

```
uv run python -m py_compile scripts/deploy1_oidc_env_check.py
uv run python scripts/deploy1_oidc_env_check.py --help
```

Result: **OK** — compiles cleanly; help text renders.

### Env-check unit tests

```
uv run python -m pytest tests/unit/test_deploy1_oidc_env_check.py -v
```

Result: **15 passed**, 1 warning — no failures.

### Auth-5 smoke-test unit tests

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

Result: **497 passed**, 3 warnings — no failures.
(Increase from 482 to 497 reflects the 15 new env-check unit tests.)

### Frontend build

```
cd frontend-v2 && npm run build
```

Result: `✓ built in 1.23s` — passed clean. `frontend-v2/dist/` unchanged.

### Repository state

```
git status --short
```

Result: only the four new Deploy-1 files plus pre-existing untracked
`gee_screening_app.egg-info/` and `uv.lock`. No tracked files modified.

## Deploy-1 Closeout Note

- No real secrets, tokens, `.env`, or private keys were committed.
- No backend auth behavior changed (auth context, token verifier, run
  authorization, and route are all unchanged).
- No frontend source changed.
- No dependencies changed (env-check script is stdlib-only; `pyproject.toml` untouched).
- No login/logout UI added.
- No token storage added (no localStorage/sessionStorage/cookie reads).
- No Supabase or provider SDK added.
- Auth-1/Auth-2/Auth-3/Auth-4/Auth-5 boundaries remain intact (68 focused tests confirm).
- No SAR/GRID/H3/H4/notebook parity/screening math changed.
- **Ready for real server activation by the operator.**
