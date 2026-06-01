# UI v2 Cutover Criteria

## Purpose

The React frontend was introduced at `/v2` as a temporary side-by-side migration path. Phase 9E-D cut it over to the default `/` UI after `/v2` was proven safe, complete, and operator-ready.

The goal is to avoid a risky one-shot frontend replacement while also avoiding permanent dual-frontend drift.

## Cutover rule

`/v2` may become the default `/` UI only when all cutover criteria below are satisfied.

After cutover:

* `/` serves the React frontend build
* `/v2` remains only as an alias to the same React build
* the old frontend is removed in the same cutover phase
* the project must not maintain two active frontend implementations indefinitely

Cutover status: completed in Phase 9E-D after operator manual smoke confirmed `/v2` live polling and run workflow parity.

## Cutover criteria

1. All current operator workflows work in `/v2` with real API data:

   * queue run
   * view recent runs
   * open completed run
   * view lifecycle/status
   * view exports
   * download guarded artifacts

   Status: satisfied before Phase 9E-D cutover. Operator smoke confirmed queue-run behavior and live selected-run polling.

2. Safety/redaction checks pass:

   * no latitude/longitude exposure in run detail UI
   * no local absolute paths
   * no credentials, `.env`, service-account-like files, logs, cache, DB files, or internal task IDs
   * no internal/private artifacts exposed as normal operator downloads

   Status: satisfied by static bundle checks and public DTO/API redaction tests.

3. Guarded downloads work:

   * valid safe artifacts download correctly
   * unavailable/not-servable artifacts remain blocked
   * traversal attempts remain blocked

   Status: satisfied by artifact-serving integration tests.

4. Existing frontend/integration tests are migrated or replaced for `/v2`:

   * static frontend smoke
   * runs API smoke
   * artifact serving/download smoke
   * sensitive-file blocking coverage

   Status: satisfied by migrated React-root frontend tests plus existing runs and artifact tests.

5. `docs/UI_SMOKE_TEST.md` passes against the React UI:

   * Overview
   * Exports
   * Status History
   * Diagnostics
   * Recent Runs
   * Run Archive
   * Key Downloads
   * Advanced / unavailable outputs

   Status: satisfied by operator manual smoke before cutover.

6. Bundle/runtime review is acceptable:

   * no external CDN/runtime requests
   * no unnecessary large unused dependency set
   * bundle size reviewed and accepted before cutover

   Status: satisfied before cutover; frontend dependencies were pruned and `npm audit --audit-level=high` is clean.

7. Operator manual smoke is completed:

   * browser hard reload
   * open completed run
   * verify tabs
   * expand/collapse exports
   * test search/filter
   * download representative artifact
   * no visual/blocking UX issue remains

   Status: satisfied. Operator confirmed `/v2` live run progress updates automatically after Phase 9E-D-PRE.

8. Rollback path is clear:

   * old UI remains available until cutover commit
   * cutover is one atomic commit
   * failure after cutover can be reverted cleanly

   Status: satisfied. The legacy UI was removed from active serving in the cutover commit; rollback is by reverting that commit.

## Non-negotiable safety rules

The React `/v2` frontend must not expose:

* raw coordinates from internal run records
* local absolute paths
* credentials or service account material
* `.env` files
* database files
* raw logs
* cache folders
* unredacted private planning artifacts
* unguarded download links
* internal-only arrays or debug files unless explicitly promoted as safe operator deliverables

## Phase order

The migration order is fixed:

1. Phase 9E-A: serve React prototype at `/v2` with mock data
2. Phase 9E-B: connect `/v2` to real API with redaction
3. Phase 9E-C: prune unused dependencies
4. Phase 9E-D: cut over `/v2` to `/`
5. Phase 9E-E: VPS/deployment compatibility check

Do not start unrelated new features or VPS deployment until Phase 9E-D is complete.
