# UI-AUTH-0 — Operator Auth UI Plan and Checklist

Date: 2026-06-08
Status: Planning/checklist only — no UI implementation started

## Purpose

This document prevents blind operator-auth UI work. It records what is already complete, what is missing, what must be decided before coding, and the safe order for future UI-auth implementation.

This slice is documentation only. It does not implement login/logout UI, token acquisition, provider callbacks, token storage, provider SDKs, backend auth changes, frontend behavior changes, VPS deployment, H3/H4, public overlay exposure, or notebook-parity work.

## Current Completed UI/Auth Pieces

| Area | Status | Notes |
|---|---|---|
| Operator private overlay frontend panel/client hook | Done | The operator-only preview panel and API helper already exist. |
| API helper bearer-token handoff | Done | The helper can forward an already-obtained bearer token when supplied. |
| `OperatorPrivateOverlayPanel` token prop | Done | The panel can receive `operatorAccessToken` and pass it into the API helper. |
| LOCAL-2 handoff contract | Done | Static tests validate `operatorAccessToken -> Authorization: Bearer <trimmed token>` when nonblank. |
| Backend Generic OIDC verifier path | Done locally | Auth-4/LOCAL-1/LOCAL-3 closeout covers local verifier readiness. |
| Backend per-run authorization | Done | Auth-3 remains the final run gate through `operator_run_authorizations`. |
| Local auth regression closeout | Done | LOCAL-3 freezes the local-only auth readiness track. |
| Token storage | Not present | No localStorage, sessionStorage, or cookie token storage exists. |
| Login/logout UI | Not present | No real operator login/logout UI has been implemented. |

## Current Missing UI/Auth Pieces

These are not implemented yet:

- Login entry point / login button.
- Logout button.
- Auth status indicator.
- Operator identity display.
- Role/access display.
- Provider redirect/callback handling.
- Token acquisition.
- Token refresh / expiry handling.
- Safe in-memory session lifecycle.
- Denied / expired / unauthorized UX.
- Provider configuration UX documentation.
- Production deployment / runtime activation.

## Explicit Non-Goals for the First UI Implementation

The first future UI implementation must not include:

- Public overlay exposure.
- Coordinate, geometry, bounds, path, exact-location, CRS, or hash display.
- Public downloads.
- Token persistence unless separately approved.
- localStorage, sessionStorage, or cookie token storage.
- Supabase unless separately approved.
- Provider SDK coupling unless separately approved.
- H3 training.
- H4 private inference.
- VPS deployment unless explicitly started by the operator.
- Backend auth behavior changes mixed into UI work.
- Operator overlay response-shape changes.

## Required Decisions Before Coding

No implementation should start until these are answered:

- [ ] Choose the real provider name or confirm Generic OIDC without a provider-specific SDK.
- [ ] Confirm provider flow: Authorization Code + PKCE, or another explicitly approved flow.
- [ ] Confirm frontend auth library choice, or confirm no SDK.
- [ ] Confirm where the access token lives: memory only, or another approved method.
- [ ] Confirm token refresh strategy.
- [ ] Confirm logout behavior and whether provider logout is required.
- [ ] Confirm callback route/path.
- [ ] Confirm operator identity claim name.
- [ ] Confirm operator roles claim name.
- [ ] Confirm Auth-3 run authorization source remains backend config for now.
- [ ] Confirm denied/expired/unauthorized UX requirements.
- [ ] Confirm no public coordinate/geometry/hash exposure.
- [ ] Confirm deployment target remains local, or explicitly start the VPS milestone separately.

## Pre-Implementation Checklist

Before any UI-auth coding slice:

- [ ] Read `docs/LOCAL_2_OPERATOR_UI_TOKEN_HANDOFF.md`.
- [ ] Read `docs/LOCAL_3_FULL_AUTH_REGRESSION_CLOSEOUT.md`.
- [ ] Confirm the exact provider and flow decision.
- [ ] Confirm no frontend source changes are mixed into planning-only work.
- [ ] Confirm no provider SDK dependency is added unless approved.
- [ ] Confirm no token storage is added unless approved.
- [ ] Confirm no login/logout UI is added before the implementation slice is approved.
- [ ] Confirm no backend auth behavior changes are mixed into the UI slice.
- [ ] Confirm no VPS/server activation instructions are added as current work.
- [ ] Confirm public/private overlay exposure rules remain unchanged.

## Proposed Safe Future Milestone Sequence

These are future milestones only. They are not implemented by this document.

1. **UI-AUTH-1 — Login/logout UX wireframe and state model, docs only**
   - Define screens, states, transitions, expired-token behavior, denied-state behavior, and operator identity display.
2. **UI-AUTH-2 — Provider selection and PKCE/client decision doc**
   - Choose provider strategy, callback path, claim names, token lifetime handling, and SDK/no-SDK approach.
3. **UI-AUTH-3 — Local mock login shell, no real provider**
   - Add a local-only mock auth shell that feeds an already-obtained token into the existing `operatorAccessToken` path.
4. **UI-AUTH-4 — Real provider callback integration, local only**
   - Add real provider callback/token acquisition locally after provider decisions are locked.
5. **UI-AUTH-5 — Role/identity display and denied-state UX**
   - Display operator identity/role status and clear denied/expired/unauthorized states without exposing private fields.
6. **UI-AUTH-6 — Full auth UI regression closeout**
   - Freeze UI-auth behavior with tests and documentation.
7. **Future separate milestone — VPS deployment**
   - Starts only if the operator explicitly says: `start VPS deployment milestone`.

## Risk Checklist

- [ ] Token persistence risk: accidental localStorage/sessionStorage/cookie usage.
- [ ] Accidental public overlay exposure risk.
- [ ] Provider SDK coupling risk.
- [ ] Provider callback route mismatch risk.
- [ ] Role claim mismatch risk.
- [ ] Auth success but run unauthorized risk.
- [ ] Expired token UX risk.
- [ ] Refresh loop / stale token risk.
- [ ] Mixing local UI work with VPS deployment risk.
- [ ] Showing private details in denied/error states risk.

## Acceptance Checklist for This Planning Slice

- [x] Document created.
- [x] Existing completed UI/auth pieces listed.
- [x] Missing UI/auth pieces listed.
- [x] Required decisions checklist added.
- [x] Pre-implementation checklist added.
- [x] Safe future milestone sequence added.
- [x] Risk checklist added.
- [x] No implementation performed.
- [x] No frontend source changed.
- [x] No backend source changed.
- [x] No dependencies changed.
- [x] No token storage added.
- [x] No login/logout UI added.
- [x] No provider activation added.
- [x] No VPS work added.

## Closeout

UI-AUTH-0 is documentation only. UI implementation is not started.

The next step is operator review of this checklist. Coding should begin only after the required provider/session/UX decisions are answered and a future implementation slice is explicitly approved.
