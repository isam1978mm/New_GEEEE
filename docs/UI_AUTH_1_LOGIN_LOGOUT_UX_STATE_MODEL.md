# UI-AUTH-1 — Login/Logout UX Wireframe and State Model

Date: 2026-06-08
Status: UX/state model defined — no UI implementation started

## Purpose

UI-AUTH-1 turns the operator auth UI checklist into a concrete UX and state model before any frontend code is changed. It defines the screens, controls, states, transitions, and safety rules for a future operator login/logout UI.

This is still documentation only. It does not implement login/logout UI, token acquisition, provider callbacks, token storage, provider SDKs, backend auth changes, frontend behavior changes, VPS deployment, public overlay exposure, H3/H4, or notebook-parity work.

## Inputs From Completed Work

- `docs/UI_AUTH_OPERATOR_LOGIN_PLAN_AND_CHECKLIST.md` defines the pre-implementation checklist and missing auth UI pieces.
- `docs/LOCAL_2_OPERATOR_UI_TOKEN_HANDOFF.md` proves the existing frontend can forward an already-obtained token through `operatorAccessToken`.
- `docs/LOCAL_3_FULL_AUTH_REGRESSION_CLOSEOUT.md` freezes the local auth readiness track and keeps Auth-3 as the final run gate.
- The current frontend has an operator private overlay panel/client hook, but no login/logout UI and no token storage.

## UX Scope

The future operator auth UI should provide:

- Login entry point.
- Logout action.
- Operator auth status indicator.
- Operator identity display.
- Operator role/access summary.
- Expired-token state.
- Unauthorized-run state.
- Provider/callback error state.
- Safe handoff into the existing `operatorAccessToken` path.

The future UI must not display coordinates, geometry, exact locations, artifact paths, hashes, CRS transforms, or public download links.

## Text Wireframe

### 1. Signed-out header state

```text
┌────────────────────────────────────────────────────────────┐
│ GEE Screening App                              [Log in]    │
│ Operator access: signed out                                │
└────────────────────────────────────────────────────────────┘
```

Expected behavior:

- Login button is visible.
- Operator private overlay panel may remain available only as a disabled/denied state, or hidden behind the existing local setting.
- No token exists in app state.
- No Authorization header is sent by the operator overlay helper.

### 2. Login in progress

```text
┌────────────────────────────────────────────────────────────┐
│ GEE Screening App                       Signing in...      │
│ Operator access: redirecting to provider                   │
└────────────────────────────────────────────────────────────┘
```

Expected behavior:

- Disable repeated login clicks.
- Do not show private overlay data.
- Do not create token storage.
- If redirect/callback fails, move to `auth_error`.

### 3. Signed-in operator state

```text
┌────────────────────────────────────────────────────────────┐
│ GEE Screening App              Operator: <actor_id> [Logout]│
│ Roles: operator                         Access: verified   │
└────────────────────────────────────────────────────────────┘
```

Expected behavior:

- Show actor identity using a safe non-sensitive display value.
- Show role/access summary without leaking claims or token contents.
- Pass the current in-memory access token to `OperatorPrivateOverlayPanel` as `operatorAccessToken`.
- Auth-3 remains the final per-run gate; signed-in does not mean every run is allowed.

### 4. Run unauthorized state

```text
┌────────────────────────────────────────────────────────────┐
│ Operator overlay preview                                   │
│ Access denied for this run.                                │
│ Reason: your operator session is valid, but this run is not │
│ authorized for your account.                               │
└────────────────────────────────────────────────────────────┘
```

Expected behavior:

- Do not expose private artifact metadata.
- Do not expose run-private fields in denial details.
- Keep messaging clear: valid auth can still be unauthorized for a run.

### 5. Expired session state

```text
┌────────────────────────────────────────────────────────────┐
│ Operator session expired.                         [Log in] │
│ Please sign in again to view operator-only previews.       │
└────────────────────────────────────────────────────────────┘
```

Expected behavior:

- Clear in-memory token.
- Do not persist stale token.
- Do not retry forever.
- Allow the operator to start login again.

### 6. Auth error state

```text
┌────────────────────────────────────────────────────────────┐
│ Could not complete operator sign-in.              [Retry]  │
│ No private overlay data was loaded.                        │
└────────────────────────────────────────────────────────────┘
```

Expected behavior:

- No private data displayed.
- No token stored.
- Error message stays generic and does not reveal provider internals or tokens.

## State Model

```text
signed_out
  └─ click_login → login_starting

login_starting
  ├─ provider_redirect_started → provider_redirected
  ├─ login_error → auth_error
  └─ cancel/reset → signed_out

provider_redirected
  ├─ callback_success(token, identity, roles) → signed_in
  ├─ callback_error → auth_error
  └─ callback_missing_token → auth_error

signed_in
  ├─ token_expired → expired
  ├─ click_logout → logout_starting
  ├─ run_allowed → overlay_allowed
  └─ run_denied_by_auth3 → run_unauthorized

expired
  ├─ click_login → login_starting
  └─ clear_session → signed_out

run_unauthorized
  ├─ select_authorized_run → signed_in
  ├─ token_expired → expired
  └─ click_logout → logout_starting

logout_starting
  ├─ local_session_cleared → signed_out
  └─ logout_error_but_local_cleared → signed_out

auth_error
  ├─ retry_login → login_starting
  └─ dismiss → signed_out
```

## State Definitions

| State | Meaning | Private data allowed? | Token handling |
|---|---|---:|---|
| `signed_out` | No operator token in memory | No | No token |
| `login_starting` | Operator clicked login | No | No token yet |
| `provider_redirected` | Provider flow/callback pending | No | No persisted token |
| `signed_in` | Token exists in approved runtime state | Only through backend + Auth-3 | In memory only unless later approved |
| `run_unauthorized` | Auth valid but Auth-3 denies selected run | No | Keep or refresh token according to later decision |
| `expired` | Token expired or unusable | No | Clear token |
| `logout_starting` | Logout requested | No | Clear local token first |
| `auth_error` | Provider/callback/login failed | No | Clear token |

## Component Placement Model

Future implementation should keep concerns separated:

```text
App shell / auth shell
  ├─ owns operator auth state
  ├─ renders login/logout/status UI
  ├─ obtains token only after provider decision is approved
  └─ passes operatorAccessToken down

Selected run view
  └─ OperatorPrivateOverlayPanel
       └─ receives operatorAccessToken prop
       └─ calls existing API helper

API helper
  └─ trims token
  └─ sends Authorization: Bearer <token> only when nonblank
```

The operator private overlay panel should not become responsible for provider login, logout, token acquisition, refresh, or storage.

## Token Lifecycle Rules

Until a later provider/session decision explicitly changes this, the safe target is:

- Access token is held in memory only.
- No localStorage.
- No sessionStorage.
- No cookie token reads/writes by frontend UI code.
- No URL token fragments retained after callback.
- Clear token on logout.
- Clear token on expiry/error.
- Do not log token contents.
- Do not show token contents in UI.
- Do not pass token anywhere except the existing operator overlay API helper path.

## Error and Denial UX Rules

- `401/403` from the backend should not reveal verifier internals.
- If the operator is signed in but not authorized for a run, message should explain run-level authorization without showing private run metadata.
- If token is expired, show a re-login prompt.
- If provider callback fails, show generic retry guidance.
- Denied states must not show coordinates, geometry, artifact family internals, file paths, hashes, CRS transforms, or download links.

## Decisions Still Required Before Coding

- [ ] Provider name or explicit Generic OIDC/no-SDK decision.
- [ ] Authorization Code + PKCE confirmation.
- [ ] Callback route/path.
- [ ] Token storage policy confirmation, preferably memory-only.
- [ ] Refresh behavior: silent refresh, manual re-login, or no refresh.
- [ ] Logout behavior: local-only logout or provider logout too.
- [ ] Identity claim for display.
- [ ] Roles claim for display/access summary.
- [ ] Error wording for denied vs expired vs provider failure.
- [ ] Whether login UI appears globally or only near operator overlay controls.

## Acceptance Criteria for Future UI-AUTH-1 Implementation

When this plan is later implemented in code, acceptance should require:

- [ ] Signed-out state renders login entry point.
- [ ] Signed-in state renders safe operator identity and logout action.
- [ ] Expired state clears token and offers login.
- [ ] Unauthorized-run state explains Auth-3 run denial without private fields.
- [ ] Token is passed into `OperatorPrivateOverlayPanel` through `operatorAccessToken` only.
- [ ] No localStorage/sessionStorage/cookie token storage is introduced.
- [ ] No provider SDK is added unless separately approved.
- [ ] No public overlay/download/geometry/exact-coordinate/hash display is introduced.
- [ ] Existing LOCAL-2 token handoff contract tests continue passing.
- [ ] Existing LOCAL-3 local auth closeout contract tests continue passing.

## Closeout

UI-AUTH-1 defines the login/logout UX wireframe and state model. It is documentation only. No UI implementation has started, and all provider/session decisions remain pending until explicitly approved.
