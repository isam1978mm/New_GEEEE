# V6.1-PLAN-1 Next-Version Planning

## Current Status

V6.1-PLAN-1 defines next-version improvements outside the frozen V6 checkpoint.

This is a planning document only. It does not change frozen V6 generation, scoring, reduction, request-zone, package, backend, frontend, deployment, or E2E behavior.

Frozen post-freeze baseline before this plan:

```text
V6-READY-FREEZE-1 -> done and tested
V6-DEPLOY-RUNBOOK-1 -> done and tested
V6-E2E-1 -> done and tested
```

## Purpose

The purpose of V6.1 is to plan safe, versioned improvements that can be evaluated after the frozen V6 package flow is stable.

V6.1 work must be explicitly approved as scoped follow-up tasks. Nothing in this document authorizes editing the frozen V6 checkpoint directly.

## Non-goals

V6.1 planning does not authorize:

- changing frozen V6 formulas without a source-locked task
- changing frozen request-zone schemas without a migration plan
- exposing private candidates publicly
- exposing private spatial payloads publicly
- committing generated V6 artifacts
- adding provider purchase or payment automation
- weakening operator authentication
- adding original classifier labels into app source
- adding real coordinates into documentation, tests, or fixtures

## Planning Rules

Every V6.1 task must follow these rules:

```text
[ ] use a versioned task ID, for example V6.1-PROD-SMOKE-1
[ ] state whether it is docs-only, test-only, frontend-only, backend-only, or algorithmic
[ ] state whether frozen V6 behavior must remain byte-compatible
[ ] include rollback instructions
[ ] include safety assertions
[ ] include tests or a reason tests are not applicable
[ ] keep generated artifacts outside Git
[ ] keep private rows and spatial payload bodies out of public APIs and UI
```

## Priority Tiers

### Tier 1 — Production Readiness

These are the safest first V6.1 tracks because they improve confidence without changing the frozen algorithm.

```text
V6.1-PROD-SMOKE-1
```

Run the frozen package flow in a real approved operator environment and record the result without exposing private rows, spatial payloads, server paths, or provider credentials.

```text
V6.1-OBSERVABILITY-1
```

Add safe metadata-only logs and counters for package review, package generation, validation status, retrieval outcome, denied requests, and rollback toggles.

```text
V6.1-DEPLOY-CHECKS-1
```

Add deployment preflight checks that verify auth, default-off package flow, run storage writability, and no generated package artifacts staged in Git.

### Tier 2 — Operator Workflow Improvements

These improve usability while preserving frozen V6 behavior.

```text
V6.1-UI-POLISH-1
```

Improve the operator package panel for readability, disabled states, copied support references, and clearer error messages while still showing metadata only.

```text
V6.1-E2E-EXPAND-1
```

Extend browser E2E automation to cover denied operator sessions, invalid package inputs, unavailable package state, retrieval failure, and rollback-disabled state.

```text
V6.1-RUNBOOK-VERIFY-1
```

Turn deployment runbook checklist items into repeatable verification commands or a safe operator checklist artifact.

### Tier 3 — Package Quality Enhancements

These may touch package generation, so they require source-lock and targeted tests before implementation.

```text
V6.1-SCORING-AUDIT-1
```

Audit scoring inputs, penalties, warning counts, and rank ordering against a frozen reference package. Do not change formulas unless a source-locked mismatch is proven.

```text
V6.1-ZONE-QA-1
```

Add request-zone quality diagnostics, such as cluster count checks, member count checks, zone sort stability checks, and safe metadata-only summaries.

```text
V6.1-PACKAGE-SCHEMA-1
```

Add stricter schema validation for app-generated V6 package components, with compatibility reports that distinguish frozen-required fields from optional V6.1 fields.

### Tier 4 — Future Algorithmic Work

These are not first-step tasks. They require clear scientific source-lock, frozen references, and explicit approval.

```text
V6.1-FEATURES-SOURCELOCK-1
```

Source-lock any new feature layer or warning rule before implementation. No guessed formulas.

```text
V6.1-REFERENCE-PARITY-1
```

Compare app-generated outputs to an operator-owned frozen reference package outside Git. Use safe summaries in repo; never commit private artifact bodies.

```text
V6.1-PROVIDER-WORKFLOW-PLAN-1
```

Plan provider quote workflow tracking as a manual status tracker only. Do not automate purchasing or payment.

## Recommended Sequence

```text
1. V6.1-PROD-SMOKE-1
2. V6.1-OBSERVABILITY-1
3. V6.1-E2E-EXPAND-1
4. V6.1-PACKAGE-SCHEMA-1
5. V6.1-SCORING-AUDIT-1
6. V6.1-ZONE-QA-1
```

## Frozen Boundary

The frozen V6 checkpoint remains the baseline. V6.1 tasks must either:

```text
[ ] preserve frozen behavior exactly
[ ] add metadata-only validation around frozen behavior
[ ] add optional V6.1-only behavior behind a separately named flag
[ ] document a planned future migration without implementing it
```

Any task that changes generated package contents must explicitly state:

```text
[ ] which fields changed
[ ] whether frozen V6 output remains available
[ ] how the change is tested
[ ] how the change is rolled back
[ ] how private outputs remain protected
```

## Safety Gates

Before any V6.1 implementation task is marked done:

```text
[ ] no generated V6 package artifacts are committed
[ ] no private rows are exposed in public API responses
[ ] no spatial payload bodies are exposed in frontend panels
[ ] no real coordinates are added to repo docs/tests/fixtures
[ ] operator-only routes remain authorized
[ ] denied requests do not read private package inputs
[ ] package retrieval remains a controlled authorized route
[ ] provider ordering remains manual unless a future explicitly approved scope changes it
```

## Completion Criteria For This Planning Task

V6.1-PLAN-1 is complete when:

```text
[x] next-version scope is documented
[x] frozen checkpoint boundary is documented
[x] priority tiers are documented
[x] recommended sequence is documented
[x] safety gates are documented
[x] no production code changes are made
```

## Next Step

Recommended first implementation track:

```text
V6.1-PROD-SMOKE-1: run and document an operator-approved production-like smoke test without changing frozen V6 behavior.
```
