# Run Metadata Architecture

## Purpose

This document audits the current local-first run metadata architecture and recommends a practical target model for:

- run archive
- status history
- artifact index
- deletion records
- disk usage accounting
- search and filter
- cleanup policy
- future Supabase/Postgres migration

This is a design document only. It does not change API behavior, database schema, pipeline behavior, artifact serving, or notebook parity behavior.

## Current Architecture

### SQLite currently stores

Current persistent SQL tables are minimal and focused:

- `runs`
  - `id`
  - `name`
  - `status`
  - `latitude`
  - `longitude`
  - `created_at`
  - `updated_at`
  - `disk_usage_bytes`
  - `output_file_count`
  - `last_disk_scan_at`
- `artifacts`
  - `id`
  - `run_id`
  - `name`
  - `relative_path`
  - `size_bytes`
  - `sha256`
  - `artifact_class`
  - `http_servable`
  - `created_at`
  - `updated_at`
- `run_deletion_audit`
  - `id`
  - `run_id`
  - `run_name`
  - `deleted_at`
  - `deleted_files_count`
  - `deleted_dirs_count`
  - `freed_bytes`
  - `status`
  - `message`

The API deliberately redacts sensitive fields from public DTOs. The frontend never receives raw coordinates, filesystem paths, hashes, or geometry through public run/list/detail responses.

### Filesystem currently stores

The run directory under `data/runs/<run_id>/` is still the source of truth for most rich run metadata and all large outputs:

- stage manifests such as `stage_<stage>.manifest.json`
- `run_status_history.json`
- notebook parity and QA manifests
- GeoTIFFs
- NPY arrays
- CSVs
- JSON summaries
- operator-visible output files
- internal/non-public files

### Current API composition

Current run APIs are hybrid:

- `POST /runs`
  - creates the run row in SQLite
  - writes initial run directory and grid manifest on disk
  - appends initial status history on disk
- `GET /runs`
  - reads SQLite run rows
  - fills missing disk summary metadata from safe filesystem scan
- `GET /runs/{id}`
  - reads the run row from SQLite
  - reads artifact rows from SQLite
  - fills missing disk summary metadata from safe filesystem scan
  - builds stage progress from filesystem stage manifests
  - builds run history from filesystem `run_status_history.json`, with fallback synthesis if missing
- `GET /runs/deletion-audit`
  - reads retained safe deletion audit rows from SQLite
- `GET /runs/{id}/outputs`
  - does not use the artifact table as the primary source
  - walks the filesystem under the run directory
  - filters through allowlisted operator-visible path patterns
  - reads selected manifests to classify unavailable / not-implemented items
- `DELETE /runs/{id}`
  - refreshes safe disk summary from filesystem immediately before deletion
  - writes retained deletion audit metadata to SQLite
  - deletes `data/runs/<run_id>/`
  - deletes the SQLite run row
  - removes artifact rows by cascade
  - returns deletion counts and freed bytes from filesystem summary

## Current SQLite Summary

### What SQLite is already good enough for

For the current local operator workflow, SQLite is already sufficient for:

- single-machine operation
- single active run guard
- recent run archive list
- core run state tracking
- artifact row persistence
- safe deletion of terminal runs
- future incremental schema growth

The current SQLite scope is small, understandable, and appropriate for a local-first app with one operator and one active run at a time.

### Current weaknesses

SQLite is not yet the full metadata source of truth because several important metadata concerns still live only in files:

- status history is persisted only in `run_status_history.json`
- stage progress is reconstructed from stage manifest files
- operator output tree is built by filesystem scanning
- unavailable / notebook-only output classification is derived from manifest parsing, not indexed rows
- status history is still file-backed rather than query-backed
- operator output tree is still scan-based rather than indexed
- archive search is client-side over the full `/runs` result

## Current Filesystem Responsibilities

The filesystem currently owns responsibilities that should stay there:

- large raster and array payloads
- export bundles
- QA source files
- manifests needed by the science pipeline
- notebook parity artifacts
- FILESYSTEM_ONLY outputs

The filesystem also currently owns some metadata responsibilities that could later move into SQLite summaries:

- stage completion/status source
- status history source
- operator output inventory source
- unavailable/not-implemented output source
- disk-usage source

## Gaps Found

### Gap 1: Run history is file-backed, not query-backed

`app/services/run_history.py` writes public-safe status events to `run_status_history.json`. This works locally, but it means:

- history cannot be filtered or paginated via SQL
- history integrity depends on file presence
- deleted runs lose all history
- future multi-user or remote access would require file syncing or a second persistence path

### Gap 2: Stage progress is manifest-derived

`GET /runs/{id}` reconstructs progress by checking whether `stage_<stage>.manifest.json` exists and reading a `status` field. This is practical, but it means:

- current stage is derived indirectly
- archive analytics by stage are not queryable in SQL
- stage timing is not persisted in structured rows

### Gap 3: Operator output tree is scan-based

`app/services/operator_outputs.py` walks the entire run directory and then filters by allowlisted patterns. This is safe because it is allowlist-based, but it means:

- output tree performance scales with file count and directory size
- search/filter is not DB-backed
- output availability is determined dynamically instead of from a stable artifact index
- some operator-visible items come from files without corresponding indexed metadata rows

### Gap 4: Deletion has no retained audit record

Current delete behavior is correct and safe for local cleanup, but once the run row is deleted:

- there is no tombstone
- there is no retained deletion timestamp
- there is no retained summary of freed bytes or deleted file count
- there is no audit trail for operator actions

### Gap 5: Disk usage is not surfaced as metadata

`DELETE /runs/{id}` computes `freed_bytes`, but the app does not currently persist or expose:

- per-run disk usage estimate before deletion
- aggregate disk usage by all runs
- cleanup candidate ranking by size

### Gap 6: Search/filter is frontend-local only

The archive UI filters the in-memory run list by name/ID/state. This is acceptable now, but later it will become limited if:

- run count grows large
- pagination is required
- disk-usage or lifecycle filters are needed

## Recommended Target Architecture

### Keep in SQLite

SQLite should remain the primary metadata store for small, queryable, structured run metadata.

Recommended target rows and fields:

- `runs`
  - keep current fields
  - add later:
    - `current_stage`
    - `detail`
    - `started_at`
    - `completed_at`
    - `last_event_at`
    - `disk_usage_bytes`
    - `public_artifact_count`
    - `operator_output_count`
- `run_history_events`
  - `id`
  - `run_id`
  - `timestamp`
  - `event_type`
  - `stage_name`
  - `label`
  - `message`
- `run_stage_status`
  - `run_id`
  - `stage_name`
  - `status`
  - `started_at`
  - `completed_at`
  - optional summary counts such as `artifact_count`
- `artifact_index`
  - can reuse the current `artifacts` table and expand carefully
  - later add:
    - `group`
    - `operator_visible`
    - `operator_status`
    - `download_name`
    - `source_manifest`
- `run_deletion_audit`
  - `id`
  - `run_id`
  - `run_name`
  - `deleted_at`
  - `prior_status`
  - `deleted_files_count`
  - `deleted_dirs_count`
  - `freed_bytes`
  - no absolute paths

### Keep on filesystem

The filesystem should remain the home of all large or file-native outputs:

- GeoTIFFs
- NPY files
- CSVs
- JSON QA files
- manifests needed by stages
- export bundles
- large notebook parity artifacts
- FILESYSTEM_ONLY outputs

### Never store or expose in public DTOs

These should remain forbidden in public JSON and UI surfaces:

- credentials
- `.env`
- service-account files
- local absolute paths
- raw logs with sensitive content
- private/internal artifacts unless explicitly promoted
- coordinates outside allowed queue-input/pre-submit contexts

## Deletion And Tombstones

### Current behavior

Current delete behavior is correct for local cleanup:

- only terminal runs can be deleted
- active runs are blocked
- the run directory is deleted safely under `data/runs/`
- the DB row is removed
- the run disappears fully from `/runs`, `/runs/{id}`, and `/runs/{id}/outputs`

### Recommendation

For the current local-first operator workflow:

- deleted runs should continue to disappear from the archive by default
- do not show tombstones in the operator UI yet
- add a retained deletion audit table later, but keep it internal-only

This preserves clean archive UX while still allowing future operator/admin audit if needed.

## Archive And Search Recommendation

### Current recommendation

Current `/runs` plus client-side search is acceptable now because:

- the app is local-first
- single-operator usage is expected
- one active run at a time is enforced
- current run volume is likely modest

### Later recommendation

If run count grows or cleanup workflows expand, move archive/search to DB-backed queries:

- filter by state
- filter by created/updated date
- sort by updated/created
- search by run name and ID
- optional filter by disk usage range

Pagination is not needed immediately, but should be the next step before any remote multi-user migration.

## Disk Usage Recommendation

### Current state

Disk usage is only computed on delete.

### Recommended next step

Add lightweight per-run disk summary metadata later:

- `disk_usage_bytes`
- `output_file_count`
- `last_disk_scan_at`

This should be computed:

- after successful pipeline completion
- after deletion planning / cleanup actions
- optionally on demand for archive refresh, not every request

Do not store per-file binary metadata in SQLite beyond the artifact index fields already needed for serving and listing.

## Supabase / Login Recommendation

### Recommendation now

Supabase is not needed now.

The current local operator workflow is better served by SQLite plus local filesystem because:

- the app is explicitly local-first
- there is no public auth in v1
- one operator / one active run is the design target
- local file outputs are large and not natural DB payloads
- current guarded download model assumes local file access

### What would need to change later for Supabase/Postgres

If the product later becomes remote and multi-user, a true backend architecture change would be needed:

- auth and user/session ownership
- Postgres schema for runs/history/stages/artifact index/deletion audit
- remote object storage for artifacts
- signed URL or brokered download design
- clearer ownership/visibility rules per user/team
- migration of local SQLite rows into remote DB
- replacement of local filesystem assumptions in operator output browsing

### Migration readiness assessment

Current code is reasonably migration-friendly because:

- SQLAlchemy is already used
- SQLite usage is basic
- API DTOs are redaction-aware
- filesystem serving is centralized through guarded helpers

Current blockers to a clean future migration are not SQLite itself. They are the metadata responsibilities that still live only in files.

## Proposed Phase 10F Items

These are small, low-risk follow-up items worth considering. They are not implemented here.

1. Add an internal `run_history_events` table while continuing to write the current JSON file during transition.
2. Add `current_stage`, `started_at`, and `completed_at` to the `runs` table.
3. Persist `disk_usage_bytes` after terminal completion and before deletion.
4. Expand the artifact index so operator-visible outputs do not require full directory scans for common archive views.
5. Add an internal `run_deletion_audit` table with no public exposure.
6. Add DB-backed archive filtering before adding pagination.
7. Keep filesystem manifests as stage-local source files, but also persist safe summaries in SQL.

## Final Recommendation

For the current local operator workflow:

- keep SQLite
- do not add Supabase or login yet
- keep large outputs on the filesystem
- gradually move query-worthy metadata from files into SQLite
- keep public DTO redaction strict
- add internal deletion audit and disk summaries before considering any remote multi-user architecture

This keeps the architecture aligned with the local-first v1 product while making a later Postgres/Supabase migration much easier if the product scope changes.
