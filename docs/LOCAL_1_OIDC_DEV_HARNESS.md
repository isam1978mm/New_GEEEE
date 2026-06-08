# Local-1 — Local-Only Generic OIDC Dev Harness

Date: 2026-06-08
Status: Local-1 complete — local OIDC harness validated

## Purpose

Local-1 provides a complete **local-only** development harness so a developer can
exercise the full Generic OIDC valid-token path on their own machine — with no
real identity provider, no real secret, no real token, no VPS, and no deployment.

It lets you prove, locally:
- A request with **no token** is denied.
- A request with an **invalid token** is denied.
- A request with a **valid local fake token** is allowed **only** when Auth-3
  (`OPERATOR_RUN_AUTHORIZATIONS`) authorizes that subject for that run.
- A valid token for a run **not** in the Auth-3 mapping is still denied.

## Explicit Boundary

- **Local only.** Everything runs on `127.0.0.1`.
- **No VPS.** No server activation, no deployment.
- **No real provider.** A throwaway RSA keypair is generated in memory.
- **No real token.** Only a short-lived local fake JWT is minted.
- **No deployment automation.** No systemd, nginx, Docker, or process-manager files.

VPS deployment remains a separate future milestone and is not started. See
`docs/DEPLOY_1_OIDC_SERVER_ACTIVATION_RUNBOOK.md` (prepared reference only).

## What the Harness Does

Script: `scripts/local_oidc_dev_harness.py` (stdlib + existing PyJWT only).

- Generates a throwaway 2048-bit RSA keypair **in memory**.
- Mints a short-lived (default 300s) RS256 JWT with claims:
  `iss`, `aud`, `sub`, `roles: ["operator"]`, `iat`, `exp`, and header `kid=local-dev-key`.
- Builds a matching **public** JWKS (no private fields) PyJWT can consume.
- Serves that JWKS on `http://127.0.0.1:<port>/.well-known/jwks.json`.
- Prints local-only env export commands, including the Auth-3 run mapping.

## What the Harness Does NOT Do

- Does not contact any real OIDC provider.
- Does not write or print private key material.
- Does not print the full token unless you pass `--print-token`.
- Does not bind to anything other than localhost (non-localhost bind is rejected).
- Does not add login/logout UI, token storage, a provider SDK, or Supabase.
- Does not modify backend auth behavior or the operator overlay response shape.

## Modes

| Mode         | Purpose                                                                |
|--------------|------------------------------------------------------------------------|
| `self-check` | Validate defaults without network; exit 0 if valid.                    |
| `env`        | Print local-only env export commands (incl. Auth-3 run mapping).       |
| `make-token` | Generate a local fake signed JWT + matching public JWKS.               |
| `serve-jwks` | Serve a matching JWKS on `127.0.0.1` and print a matching token.       |
| `all`        | Print the full local test sequence (3 terminals).                      |

## Run the Self-Check

```bash
uv run python scripts/local_oidc_dev_harness.py --mode self-check
```

Expected: all PASS lines, exit 0.

## Generate a Local Fake Token

```bash
# Redacted summary by default (never prints the full token):
uv run python scripts/local_oidc_dev_harness.py --mode make-token --run-id local_run_001

# Reveal the full token (local dev only — never commit it):
uv run python scripts/local_oidc_dev_harness.py --mode make-token --run-id local_run_001 --print-token

# Also print the public JWKS:
uv run python scripts/local_oidc_dev_harness.py --mode make-token --print-jwks
```

The private key is generated in memory and is never written or printed.

## Serve Local JWKS

```bash
uv run python scripts/local_oidc_dev_harness.py --mode serve-jwks --port 8765 --print-token
```

This serves `http://127.0.0.1:8765/.well-known/jwks.json` and prints a token that
**matches** the served key (because both come from the same in-memory keypair).
Copy that token for the valid-token smoke test. Press Ctrl+C to stop.

## Export Local Env Values

```bash
eval "$(uv run python scripts/local_oidc_dev_harness.py --mode env --run-id local_run_001)"
```

Sample output (local-only placeholders):

```bash
export OPERATOR_PRIVATE_OVERLAY_PREVIEW_ENABLED=true
export OPERATOR_AUTH_TRUSTED_PROXY_ENABLED=false
export OPERATOR_AUTH_OIDC_ENABLED=true
export OPERATOR_AUTH_OIDC_ISSUER_URL=http://127.0.0.1:8765
export OPERATOR_AUTH_OIDC_CLIENT_ID=gee-local-operator-ui
export OPERATOR_AUTH_OIDC_JWKS_URI=http://127.0.0.1:8765/.well-known/jwks.json
export OPERATOR_RUN_AUTHORIZATIONS='{"local-operator": ["local_run_001"]}'
```

## Full Local Test Sequence

Print the exact steps:

```bash
uv run python scripts/local_oidc_dev_harness.py --mode all --run-id local_run_001
```

The sequence (three terminals, all local):

1. **Terminal A** — serve the local JWKS and print a matching token:
   ```bash
   uv run python scripts/local_oidc_dev_harness.py --mode serve-jwks --port 8765 --print-token
   ```
2. **Terminal B** — export local env and start the app:
   ```bash
   eval "$(uv run python scripts/local_oidc_dev_harness.py --mode env --run-id local_run_001)"
   uvicorn app.main:app --host 127.0.0.1 --port 8015
   ```
3. **Terminal C** — run the Auth-5 smoke tests:
   ```bash
   # no-token must be denied
   uv run python scripts/auth5_oidc_smoke.py --base-url http://127.0.0.1:8015 --run-id local_run_001 --mode no-token

   # invalid-token must be denied
   uv run python scripts/auth5_oidc_smoke.py --base-url http://127.0.0.1:8015 --run-id local_run_001 --mode invalid-token

   # supply the local fake token from terminal A (shell only, never committed)
   export AUTH5_SMOKE_BEARER_TOKEN=<paste local fake token from terminal A>
   uv run python scripts/auth5_oidc_smoke.py --base-url http://127.0.0.1:8015 --run-id local_run_001 --mode valid-token
   unset AUTH5_SMOKE_BEARER_TOKEN
   ```

## Testing the Four Cases

| Case                                   | Expected result                                          |
|----------------------------------------|----------------------------------------------------------|
| No token                               | HTTP 403, `outcome: denied`                              |
| Invalid token                          | HTTP 403, `outcome: denied`                              |
| Valid local fake token, run authorized | HTTP 200, `outcome: allowed`                             |
| Valid local fake token, run NOT in map | HTTP 403, `outcome: denied` (Auth-3 is the final gate)   |

To test the last case, export env with `--run-id local_run_001` but call the smoke
test with a different `--run-id` that is not in `OPERATOR_RUN_AUTHORIZATIONS`. A
valid token alone does not grant access — Auth-3 backend config decides per-run.

## Frontend Note

- The frontend can forward an already-obtained bearer token via the
  `operatorAccessToken` prop on `OperatorPrivateOverlayPanel`.
- **No login/logout UI** is added by this harness or anywhere in the project.
- **No token storage** is added; tokens are never placed in `localStorage`,
  `sessionStorage`, or cookies.
- How a token reaches the prop in real use is outside this local harness.

## Troubleshooting

| Symptom                                  | Likely cause                                                       |
|------------------------------------------|--------------------------------------------------------------------|
| valid-token returns 403                  | The run id is not in `OPERATOR_RUN_AUTHORIZATIONS` for that subject.|
| valid-token returns invalid_token        | Token expired (default TTL 300s), or JWKS server not running / wrong port. |
| JWKS server will not start               | Port already in use, or a non-localhost host was passed (rejected).|
| no-token/invalid-token return 200        | App not started with OIDC env, or wrong base URL — investigate.    |

## Validation Results

Date: 2026-06-08

| Check                                   | Command                                                                 | Result        |
|-----------------------------------------|-------------------------------------------------------------------------|---------------|
| Harness syntax                          | `uv run python -m py_compile scripts/local_oidc_dev_harness.py`         | OK            |
| Harness self-check                      | `uv run python scripts/local_oidc_dev_harness.py --mode self-check`     | exit 0        |
| Harness unit tests                      | `pytest tests/unit/test_local_oidc_dev_harness.py`                      | 15 passed     |
| Auth-5 smoke unit tests                 | `pytest tests/unit/test_auth5_oidc_smoke.py`                            | 18 passed     |
| Deploy-1 env-check unit tests           | `pytest tests/unit/test_deploy1_oidc_env_check.py`                      | 15 passed     |
| Focused Auth backend                    | `pytest <token_verifier+auth_context+config+run_auth+overlay_api>`      | 68 passed     |
| Broad backend regression                | `pytest tests/unit/ tests/integration/`                                 | 512 passed    |
| Frontend build                          | `cd frontend-v2 && npm run build`                                       | built clean   |

The broad count increased from 497 to 512, reflecting the 15 new harness unit tests.

## Closeout

Local-1 is complete and local-only.

- No VPS or server activation was added as current work.
- No real provider values, tokens, or keys were committed.
- No backend auth behavior changed.
- No frontend source changed.
- No dependencies changed (stdlib + existing PyJWT only).
- No login/logout UI added.
- No token storage added (no localStorage/sessionStorage/cookie reads).
- No Supabase or provider SDK added.
- No systemd/nginx/Docker/VPS automation added.
- Auth-1/Auth-2/Auth-3/Auth-4/Auth-5 boundaries remain intact.
- No SAR/GRID/H3/H4/notebook parity/screening math changed.
- Auth-3 per-run config remains the final run gate.
