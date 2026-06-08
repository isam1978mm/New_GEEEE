# Auth-4 — Real Provider Integration Plan

Date: 2026-06-08
Status: Step 5 complete — focused token/auth-context tests added
Implementation status: Focused post-wiring tests added; frontend Authorization header path not started

## Purpose

Auth-4 wires a real authentication and identity provider into the operator overlay
route so that operator identity is no longer supplied by trusted upstream headers
alone.

After Auth-3, the backend has a config-backed per-run authorization store. Auth-4
replaces the trust-on-header model with verified identity from a real provider,
while keeping every prior layer intact.

This planning document records the decision boundary and scope for Auth-4. No
provider is implemented here.

## Plain-English Summary

After Auth-1, Auth-2, and Auth-3:

- Operator header parsing is centralized in `app/services/operator_auth_context.py`.
- The trusted-proxy gate (`operator_auth_trusted_proxy_enabled`) controls whether
  upstream headers are trusted at all.
- Per-run access is resolved by `app/services/operator_run_authorization.py`
  against the backend config store.
- Every request builds a redacted audit event and a coordinate-free operator-only
  preview.

The remaining gap is that "trusted" means the backend accepts whatever identity the
upstream proxy sends. There is no token that the backend itself verifies as coming
from a real authentication provider. A misconfigured proxy could fabricate operator
identity even when trusted-proxy mode is enabled.

Auth-4 should close this gap by verifying identity from a real provider — either
through a signed token the backend validates, or through a reverse-proxy session that
the backend can confirm via a provider API — before accepting any operator identity.

## Current Locked State After Auth-1/Auth-2/Auth-3

```text
Auth-1 complete:
  - Operator header parsing centralized in app/services/operator_auth_context.py
  - app/api/operator_overlays.py routes through the adapter

Auth-2 complete:
  - operator_auth_trusted_proxy_enabled defaults to False
  - When False, all header-based operator context is discarded → fail closed
  - When True, header-based context is parsed through the Auth-1 adapter

Auth-3 complete:
  - operator_run_authorizations: dict[str, list[str]] = {} in Settings
  - app/services/operator_run_authorization.py resolves per-run authorization
  - authorization_result= is wired into OverlayAccessRequest
  - Header-supplied authorized_run_ids is no longer the per-run gate

Current trusted headers (still in use, not yet provider-verified):
  X-Operator-Authenticated
  X-Operator-Id
  X-Operator-Roles
  X-Operator-Authorized-Runs
  X-Request-Id

No real provider integration exists.
No JWT verification exists.
No session management exists.
```

## Explicit Approval Note

Auth-4 real provider integration is explicitly approved to begin **planning only**.
Implementation may not begin until:

1. The provider decision is made and recorded in this document.
2. A separate implementation goal is issued after this planning document is
   committed.

## Provider Decision

**Chosen provider: Option B — Generic OIDC Provider.**

Reason for selection:
- Provider-neutral and portable.
- Works with Auth0, Keycloak, Azure AD, Google Workspace, or a self-hosted OIDC
  server without locking the project to one vendor.
- Avoids silently adopting Supabase, which is not an existing project dependency.
- Keeps implementation independent of a specific vendor.
- Matches the plan recommendation when no specific vendor is required.

Implementation remains not started. No OIDC code, no JWT verification, no provider
SDK, and no login/logout UI has been added.

## Progress Checklist

- [x] Step 1: choose Generic OIDC provider path
- [x] Step 2: add Generic OIDC config settings
  - Added `operator_auth_oidc_enabled`, `operator_auth_oidc_issuer_url`,
    `operator_auth_oidc_client_id`, `operator_auth_oidc_jwks_uri` to `Settings`.
  - All fields default to `False` / `None`.
  - Env parsing tested for all four fields.
  - No runtime authentication behavior changed.
- [x] Step 3: add token verifier service
  - Added `app/services/operator_token_verifier.py` with `TokenVerificationResult` dataclass
    and `verify_operator_token` function.
  - Added `tests/unit/test_operator_token_verifier.py` — 16 tests, all pass; no network calls.
  - Added `PyJWT[crypto]>=2.8.0` to `pyproject.toml`.
  - All fail-closed gates exercised: oidc_disabled, missing_token, missing_issuer,
    missing_client_id, missing_jwks_uri, missing_subject, invalid_token, expired token.
  - No token verifier wiring into auth context yet.
- [x] Step 4: wire verifier into auth context adapter
  - Extended `resolve_operator_auth_context` with `settings` and `authorization` params (backward compatible).
  - When OIDC enabled: bearer token extracted (case-insensitive), `verify_operator_token` called,
    verified identity populates context from token claims; raw X-Operator-* identity headers cannot override.
  - When OIDC enabled and verification fails: fail-closed; request_id generated, never trusted from header.
  - When OIDC disabled: existing trusted-proxy behavior preserved exactly.
  - Route forwards `Authorization` header; no inline token logic in route.
  - 6 new adapter unit tests added; all 64 focused tests pass.
- [x] Step 5: add focused token/auth-context tests
  - Added 3 integration tests proving: verified OIDC token identity can access route when Auth-3
    backend config authorizes the actor/run; verified OIDC token cannot bypass Auth-3 per-run gate;
    invalid OIDC token fails closed even when raw X-Operator-* headers claim access.
  - Added 1 unit test proving OIDC verified token authenticates regardless of trusted_proxy_enabled.
  - All 68 focused tests pass.
- [ ] Step 6: add frontend Authorization header path only if required
- [ ] Step 7: run focused and broad validation / closeout

## Provider Decision Required Before Implementation

**A provider must be selected before Auth-4 Step 1 begins.**

The provider selection determines which token format is verified, which SDK (if any)
is added as a dependency, and which environment variables are required.

The operator should read the three candidate options below and confirm the choice
before issuing the next implementation goal.

## Candidate Provider Options

### Option A: Supabase Auth

**Appropriate when:** The project already uses or plans to use Supabase for database
or storage, and the operator UI is a web frontend that can use the Supabase client
SDK.

**How it works:**
- The frontend uses the Supabase JS client to sign in (email/password, magic link,
  or OAuth) and receives a JWT signed by Supabase.
- The frontend includes the JWT in requests (e.g., `Authorization: Bearer <token>`).
- The backend verifies the JWT signature using the Supabase project's public key
  (available from the project's JWKS endpoint or `SUPABASE_JWT_SECRET`).
- On verification, the backend extracts `sub` (actor ID), roles (from JWT claims or
  Supabase `user_metadata`), and request context.

**New dependencies:**
- `python-jose` or `PyJWT` for JWT verification (backend).
- `@supabase/supabase-js` for the frontend client (already present or to be added).

**Environment variables required:**
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_JWT_SECRET` (for backend verification) or a JWKS fetch from the project

**Existing architecture fit:**
- The project does not currently use Supabase. Adding it introduces a new external
  service dependency. This is only appropriate if Supabase is separately approved
  for the broader project.

**Recommendation:** Only choose this option if Supabase is separately approved for
the project.

---

### Option B: Generic OIDC Provider

**Appropriate when:** The deployment environment already has an OIDC-capable identity
provider (e.g., Auth0, Keycloak, Azure AD, Google Workspace, or a self-hosted
OIDC server), or when provider portability is more important than a single vendor.

**How it works:**
- The operator authenticates with the OIDC provider and receives an access token
  or ID token (JWT).
- The frontend includes the token in the `Authorization: Bearer` header.
- The backend fetches the provider's JWKS endpoint to obtain public keys, then
  verifies the token signature, `iss` (issuer), `aud` (audience), and expiry.
- On verification, the backend extracts claims: `sub`, custom role claims, and
  optionally authorized run IDs.

**New dependencies:**
- `python-jose` or `PyJWT` plus `cryptography` (backend JWT verification).
- A JWKS fetch/cache layer (can be minimal; no heavy OIDC client library required).

**Environment variables required:**
- `OIDC_ISSUER_URL` (e.g., `https://accounts.google.com` or provider's discovery URL)
- `OIDC_CLIENT_ID` (for audience validation)
- Optional: `OIDC_JWKS_URI` (if not auto-discoverable from `/.well-known/openid-configuration`)

**Existing architecture fit:**
- Provider-neutral. Works with any standards-compliant OIDC server.
- Most portable option. Does not tie the project to a specific vendor.

**Recommendation:** Preferred if no specific vendor is required and provider
portability matters. This is the lowest-friction path if a JWKS endpoint is already
available.

---

### Option C: Existing Trusted Reverse Proxy with Signed Identity Headers

**Appropriate when:** The deployment already uses a trusted reverse proxy (e.g.,
nginx, Caddy, Traefik, Cloudflare Access, or AWS ALB with OIDC) that handles
authentication and forwards verified identity in signed headers or a proxy-issued
token.

**How it works:**
- The reverse proxy authenticates the operator externally (via OIDC, SAML, or its
  own credential store) and then forwards a signed assertion to the backend
  (e.g., a signed JWT in a custom header, or Cloudflare Access `Cf-Access-Jwt-Assertion`).
- The backend verifies the proxy-issued token signature using the proxy's public key.
- The existing `X-Operator-*` header model can be replaced with a single
  verified-token header, with the Auth-1 adapter updated to extract fields from the
  verified token instead of trusting raw headers.

**New dependencies:**
- Backend: lightweight JWT or HMAC verification only (no heavy OIDC library needed
  if the proxy issues a simple signed token).

**Environment variables required:**
- Provider-specific public key or JWKS endpoint for the proxy's tokens.

**Existing architecture fit:**
- Aligns most naturally with the current Auth-1/Auth-2 trusted-proxy architecture.
- If the proxy already handles authentication, this keeps the backend boundary thin.
- Auth-3's config-backed per-run store still applies independently of the proxy.

**Recommendation:** Natural fit if a trusted reverse proxy is already in the
deployment architecture. Preserves the Auth-2 trusted-proxy concept while adding
actual signature verification.

---

## Recommended Provider Path

**Provider decision is required before implementation begins.**

If the project has no existing provider preference, the recommended default is:

> **Option B (Generic OIDC)** if a JWKS-capable identity provider is available.
> **Option C (Signed proxy token)** if a trusted reverse proxy already handles auth.
> **Option A (Supabase)** only if Supabase is separately approved for the project.

The operator should confirm the choice and add it to this document before the first
implementation goal is issued.

## Backend Trust Boundary

Auth-4 must update the backend trust boundary so that:

1. The `operator_auth_trusted_proxy_enabled` gate (Auth-2) is supplemented or
   replaced by token verification — the backend no longer accepts raw identity
   headers without a verified token.
2. Token verification happens inside or alongside `resolve_operator_auth_context()`
   in `app/services/operator_auth_context.py`.
3. On verification failure the result is the same fail-closed `OperatorAuthContext`
   returned when trusted-proxy mode is disabled.
4. On verification success the existing flow continues: actor ID, roles, and request
   ID are extracted from the verified token and passed to the Auth-3 per-run resolver.
5. No new inline policy is added to the route (`app/api/operator_overlays.py`); the
   route remains thin and routes through the Auth-1 adapter.

## Frontend/Session Boundary

Auth-4 must not:

- Add browser-side token storage in a way that creates XSS risk (no
  `localStorage` for raw tokens; use `httpOnly` cookies or session
  management handled by the provider SDK if the provider requires it).
- Fabricate or simulate provider authentication in the frontend.
- Change the existing operator-only preview panel's coordinate-free behavior.
- Add a public-facing login route that bypasses operator-only access control.
- Add UI management for per-run authorization (that is a separate later slice).

Auth-4 may:

- Add a login/logout flow to the operator-only section of the frontend when a
  provider is confirmed and the flow is scoped to operator-only access.
- Add a minimal session hook or token retrieval helper in the frontend so that the
  `Authorization: Bearer` header (or equivalent) is forwarded to the backend route.

## Token Verification Boundary

The backend token verifier must:

- Verify the token signature using a public key or JWKS endpoint.
- Validate `iss` (issuer), `aud` (audience), and token expiry.
- Extract `sub` (actor ID) and role claims.
- Reject expired, malformed, or unsigned tokens with the same fail-closed response
  as an unauthenticated request.
- Not log or persist raw token values (log only the redacted actor ID or `anonymous`).
- Not expose token contents or verification errors in the public API response.

## Environment/Config Requirements

Auth-4 will require one or more new `Settings` fields depending on the provider
chosen. Candidates (exact names to be decided at implementation time):

```text
# Option A — Supabase
operator_auth_supabase_url: str | None = None
operator_auth_supabase_jwt_secret: str | None = None

# Option B — Generic OIDC
operator_auth_oidc_issuer_url: str | None = None
operator_auth_oidc_client_id: str | None = None
operator_auth_oidc_jwks_uri: str | None = None

# Option C — Signed proxy token
operator_auth_proxy_jwks_uri: str | None = None
operator_auth_proxy_token_header: str = "X-Operator-Token"
```

All new settings should default to `None` / disabled. When `None`, the verifier
must fail closed (same as trusted-proxy disabled).

## Allowed Implementation Scope

Auth-4 implementation may change only:

```text
app/config.py                                  (new auth settings fields)
app/services/operator_auth_context.py          (add token verification)
app/services/operator_token_verifier.py        (new — token verification logic)
tests/unit/test_operator_auth_context.py       (cover verified-token paths)
tests/unit/test_operator_token_verifier.py     (new — token verifier unit tests)
tests/integration/test_operator_overlay_preview_api.py
                                               (only if a real coverage gap is found)
frontend-v2/src/app/api/operatorOverlays.ts    (add Authorization header forwarding)
frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx
                                               (add login/logout flow if provider confirmed)
docs/AUTH_4_REAL_PROVIDER_INTEGRATION_PLAN.md  (progress/status updates)
```

Auth-4 may:

- Add one new token verifier service module.
- Add one new `Settings` field per required provider config value.
- Update the Auth-1 adapter to extract identity from a verified token instead of raw
  headers when a token is present.
- Keep existing fail-closed behavior when no token is present or verification fails.
- Preserve existing route path, response shape, and operator-only preview boundaries.
- Add a provider-specific dependency to `pyproject.toml` only when the provider is
  confirmed.

## Forbidden Scope

Auth-4 must not:

- Change artifact-serving policy.
- Change public/private exposure behavior.
- Expose exact coordinates, raw geometry, KML contents, heatmap point payloads,
  local filesystem paths, or private hashes.
- Change H3/H4 behavior.
- Change SAR math.
- Change GRID logic.
- Change notebook parity logic.
- Change candidate screening math.
- Commit generated/private artifacts.
- Remove the trusted-proxy gate (Auth-2).
- Remove the auth-context adapter (Auth-1).
- Remove the per-run authorization resolver (Auth-3).
- Add public overlay exposure.
- Add public artifact downloads.
- Add browser-side raw token storage in `localStorage`.
- Add login UI accessible to non-operator roles.
- Add UI management for per-run authorization.

Auth-4 is not an excuse to bypass or weaken the Auth-1/Auth-2/Auth-3 layers.
Each prior layer must remain in place and continue to function correctly.

## Proposed Implementation Steps

These are proposals for the later implementation slice. No step begins before the
provider decision is recorded in this document.

1. **Provider selection** — Record the chosen provider in this document under
   "Provider Decision." No code changes in this step.

2. **Add provider config settings** — Add the smallest set of new `Settings` fields
   needed for the chosen provider. All fields default to `None`. Add unit tests for
   defaults and explicit values.

3. **Add token verifier service** — Add
   `app/services/operator_token_verifier.py`:
   - Accept a raw token string and settings.
   - Return a `TokenVerificationResult` dataclass with `verified: bool`,
     `actor_id: str | None`, `roles: tuple[str, ...]`, and `reason: str`.
   - Fail closed when settings fields are `None`, token is absent, or verification
     fails.
   - Do not log raw token values.

4. **Wire verifier into auth context adapter** — Update
   `app/services/operator_auth_context.py`:
   - Accept an optional `token: str | None` argument.
   - When a token is present and provider settings are configured, call the verifier
     and populate `OperatorAuthContext` from the verified claims.
   - When no token is present or settings are not configured, fall back to the
     existing trusted-proxy header path (so Auth-2 and Auth-3 remain intact).

5. **Update route** — Update `app/api/operator_overlays.py` minimally:
   - Extract the `Authorization` header (if present) and pass it to the adapter.
   - Keep the route thin; no inline token logic.

6. **Add focused unit and integration tests** for:
   - Verified token → operator identity resolved correctly.
   - Expired/invalid token → fail closed.
   - Missing token → falls back to trusted-proxy path.
   - Provider config absent → fail closed.

7. **Frontend update** (only if provider confirmed):
   - Add token retrieval to `frontend-v2/src/app/api/operatorOverlays.ts`.
   - Pass `Authorization: Bearer <token>` in the operator overlay request.
   - Add minimal login/logout to the operator-only section.

8. **Re-run focused and broad tests** to confirm all prior layers remain intact.

## Expected Changed Files for Later Implementation

```text
app/config.py
app/services/operator_auth_context.py
app/services/operator_token_verifier.py        (new)
app/api/operator_overlays.py
tests/unit/test_operator_token_verifier.py     (new)
tests/unit/test_operator_auth_context.py
tests/integration/test_operator_overlay_preview_api.py
frontend-v2/src/app/api/operatorOverlays.ts
docs/AUTH_4_REAL_PROVIDER_INTEGRATION_PLAN.md
```

Optionally, if a frontend login flow is added:

```text
frontend-v2/src/app/components/OperatorPrivateOverlayPanel.tsx
```

## Validation Commands

Recommended commands for the later implementation slice:

```bash
uv run python -m pytest tests/unit/test_operator_token_verifier.py -v
uv run python -m pytest tests/unit/test_operator_auth_context.py -v
uv run python -m pytest tests/unit/test_config_auth_settings.py -v
uv run python -m pytest tests/unit/test_operator_run_authorization.py -v
uv run python -m pytest tests/integration/test_operator_overlay_preview_api.py -v
uv run python -m pytest tests/unit/ tests/integration/ -v
cd frontend-v2 && npm run build
git status --short
git diff --stat
```

## Acceptance Criteria

Auth-4 should be accepted only if all are true:

- Provider decision is recorded in this document.
- A token verifier service exists and is unit-tested.
- Token verification is wired into `resolve_operator_auth_context(...)`.
- Invalid or missing tokens fail closed identically to the Auth-2 disabled state.
- The Auth-1 adapter boundary remains intact.
- The Auth-2 trusted-proxy gate remains in place.
- The Auth-3 per-run config resolver remains in place.
- Operator overlay response shape is unchanged.
- Redaction behavior is unchanged.
- No public overlay or artifact-serving behavior changes are introduced.
- No H3/H4/SAR/GRID/notebook parity/screening math behavior changes.
- Focused unit tests for the token verifier pass.
- Broad unit and integration tests pass without regressions.
- Frontend build passes if frontend changes are made.

## Rollback Plan

If the Auth-4 implementation causes regressions:

1. Revert the token verifier wiring in `app/services/operator_auth_context.py` so
   the adapter returns to the Auth-3 trusted-proxy-header path.
2. Remove or disable the new token verifier service.
3. Remove any new provider config settings if they are not yet in use.
4. Re-run the focused unit and integration tests for operator auth context, operator
   run authorization, and operator overlay preview.
5. Leave real provider integration blocked until a smaller or clearer Auth-4
   implementation is approved.

## Codex Goal Template for the Next Implementation Slice

Use a later scoped goal in this shape after the provider decision is recorded:

```text
goal Auth-4 Step 1 — provider config settings

Repo / branch / sync rules
- Repo: C:\Dev\New_GEE
- Remote: https://github.com/max2026-lab/New_GEE.git
- Branch: main
- Pull latest main before starting.
- Do not force push.
- Push the final commit to origin main.

MUST READ FIRST
- docs/AUTH_4_REAL_PROVIDER_INTEGRATION_PLAN.md  (especially Provider Decision section)
- app/config.py
- tests/unit/test_config_auth_settings.py

CURRENT LOCKED STATE
- Auth-1 is fully closed.
- Auth-2 is fully closed.
- Auth-3 is fully closed.
- Auth-4 provider decision is recorded in docs/AUTH_4_REAL_PROVIDER_INTEGRATION_PLAN.md.
- Auth-4 Step 1 provider config settings are not started.

SCOPE
Add the smallest set of new Settings fields needed for the chosen provider.
All fields default to None.
Add unit tests for defaults and explicit values.

STRICT DO NOT CHANGE
- Do not start token verification yet.
- Do not modify app/services/operator_auth_context.py.
- Do not modify app/api/operator_overlays.py.
- Do not modify any parity/SAR/GRID/notebook/screening files.
- Do not change artifact-serving or exposure policy.
- Do not commit generated/private artifacts.

Allowed files:
- app/config.py
- tests/unit/test_config_auth_settings.py
- docs/AUTH_4_REAL_PROVIDER_INTEGRATION_PLAN.md (status update only)

Validation commands:
- uv run python -m pytest tests/unit/test_config_auth_settings.py -v
- uv run python -m pytest tests/unit/ tests/integration/ -v
- git status --short
- git diff --stat

Commit message: feat: add Auth-4 provider config settings

Final report requirements:
1. Commit SHA
2. Exact changed files
3. Full validation command output or clear pass/fail summary
4. Confirmation only allowed files changed
5. Confirmation provider config fields default to None
6. Confirmation no token verification or auth logic was added
7. Confirmation Auth-1/Auth-2/Auth-3 boundaries unchanged
8. Confirmation commit was pushed to origin main
```
