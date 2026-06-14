# V6.1-OBSERVABILITY-1 Safe Package-flow Observability

## Current Status

V6.1-OBSERVABILITY-1 adds safe metadata-only counters and logs for the V6 private package flow.

This is a versioned V6.1 follow-up. It does not change frozen V6 generation, scoring, reduction, request-zone, package contents, frontend behavior, deployment behavior, or browser E2E behavior.

## Scope

The observability hooks record only safe operational metadata for these actions:

```text
generate
review
retrieve
```

They record these safe outcomes:

```text
generated
available
not_available
invalid_package_inputs
denied
```

They also record the default-off rollback state:

```text
enabled  -> V6_PACKAGE_FLOW_ENABLED=true for an approved window
disabled -> V6_PACKAGE_FLOW_ENABLED=false
```

## Files

```text
app/services/v6_package_observability.py
app/services/v6_app_flow.py
tests/unit/test_v6_package_observability.py
docs/V6_1_OBSERVABILITY_1.md
```

## Safe Log Fields

The logger name is:

```text
app.v6_package_flow
```

A safe event may include only:

```text
action
outcome
status_code
request_id
run_id
package_ready
rollback_state
actor_authenticated
operator_role_present
denial_reason
validation_status
payload_count
zip_entry_count
issue_count
warning_count
```

The log event must not include package bodies, candidate rows, feature rows, spatial payloads, raw file paths, bearer tokens, provider credentials, or coordinates.

## Counters

The in-memory counters track:

```text
action|{action}|{outcome}
status|{action}|{status_code}
rollback_state|{enabled|disabled}|{outcome}
denied|{denial_reason}|{action}
```

Examples:

```text
action|generate|generated
status|review|200
rollback_state|disabled|denied
denied|package_flow_disabled|retrieve
```

## Denial Reasons

Denied requests are still returned with the existing generic denial response. Internal observability records one safe denial reason:

```text
package_flow_disabled
operator_not_authenticated
operator_role_missing
run_not_authorized
```

Denied requests continue to short-circuit before private package inputs are read.

## Safety Guarantees

```text
[x] no generated artifacts are committed
[x] no package input bodies are logged
[x] no candidate rows are logged
[x] no request-zone payload bodies are logged
[x] no coordinate or geometry bodies are logged
[x] no bearer tokens are logged
[x] no provider credentials are logged
[x] denied requests do not read private package inputs
[x] package retrieval remains authorized and controlled
```

## Validation

Run:

```powershell
cd C:\Dev\New_GEE
python -m pytest tests/unit/test_v6_package_observability.py -q
python -m pytest tests/unit/test_v6_app_flow.py -q
```

Expected:

```text
all tests pass
```

## Rollback

This change can be rolled back by reverting the V6.1 observability files and hooks. Operational rollback for the package flow remains:

```text
V6_PACKAGE_FLOW_ENABLED=false
```

## Next Recommended Track

```text
V6.1-E2E-EXPAND-1: extend browser E2E coverage for denied, invalid-input, unavailable, retrieval-failure, and disabled rollback states.
```
