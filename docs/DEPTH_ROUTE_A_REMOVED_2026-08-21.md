# Depth Route A — Removed

Date: 2026-08-21

## Final decision

Route A is removed from the application.

The runtime test proved that Route A can return provisional metre ranges only when a run footprint contains the already-known reviewed Tyrone test plots. A different normal run returned zero reviewed candidates and zero numerical depth. Therefore Route A does not advance the product requirement of numerical depth for a new unknown run.

Do not describe Route A as solving numerical depth for new sites, and do not restore it without explicit user approval.

## Removed application path

This removal deletes the Tyrone reviewed-zone Route A UI, frontend API client, backend reviewed-zone endpoint/service, Tyrone local package builder, old post-run Route A command/operator guide, and Route A-specific tests. Automatic `local_calibrated` depth-stage registration in the orchestrator is also removed.

## Preserved infrastructure

This removal does not change the classifier, NB formula, Option 5, or the reusable generic depth engine. It also does not claim that unknown-ground numerical depth has been validated.

## Current product status

Numerical depth for a new unknown run remains unresolved. Unknown sites must not receive a Tyrone-derived metre value.

Historical Route A documents and merged PR history are retained only as project history; this document supersedes them for current product behavior.
