# Threat Model

This project is a local-first screening tool with a deliberately narrow public surface.

## Primary risks

1. Coordinate leakage through JSON, CSV, logs, or exception text.
2. Sensitive local artifacts being downloaded when the app is exposed beyond loopback.
3. Experimental classifier outputs being served or shown through the app.
4. Unsafe Earth Engine auth flows being reintroduced.
5. Notebook-era assumptions reappearing as direct filesystem streaming or unguarded responses.

## Controls

### Redaction boundary

- Public JSON responses pass through `verify_redacted()`.
- Public error handlers emit generic safe messages.
- Redaction tests cover coordinates, geometry, paths, hashes, and request-body echoing.

### Artifact boundary

- Public downloads go only through `serve_artifact_response()`.
- `can_serve_artifact()` blocks `FILESYSTEM_ONLY`.
- `LOCAL_SENSITIVE` artifacts are blocked under network bind.
- Policy tests reject direct file streaming in API routes.

### Experimental containment

- Import is env-gated.
- Execution is CLI-only.
- Outputs stay under `experimental/` and are `FILESYSTEM_ONLY`.
- The frontend filters them out.
- The API returns 404 for any attempt to fetch them through the artifact route.

### Auth boundary

- Earth Engine initialization uses service-account credentials only.
- Tests scan for `ee.Authenticate()` and fail if it appears.

## Residual assumptions

- The operator controls the local machine and filesystem.
- The operator is responsible for protecting service-account credentials.
- Enabling network bind changes the trust boundary, so Class I artifact serving is reduced automatically.
