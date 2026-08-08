# Campaign 012 Result — OSMRE Recent Phase I Bond Release

Date: 2026-08-08
Campaign ID: `central_appalachia_earthwork_pilot_v12_osmre_recent_phase1_bond_release`
Protected branch: `claude/depth-measurement-unblock-p2zjpd`

## Final status

**CLOSED — approved target unavailable in the live OSMRE source.**

Campaign 012 did not reach ICESat-2 acquisition. It therefore did **not** produce a scientific zero-candidate ICESat-2 result. The campaign closed at the official-source eligibility gate because the live OSMRE Phase I records needed to construct the approved 2019–2024 Virginia/West Virginia/Kentucky target did not contain a usable reclamation-bond status date.

Numerical depth remains blocked.

## Validation

The Campaign 012 scanner, live-source compatibility layer, and watchdog tests passed locally:

- 17 tests passed.

No scientific threshold was changed.

## First live attempt

The original combined OSMRE server-side query returned no eligible polygons and the scanner exited before ICESat-2 acquisition.

Because that could have been an ArcGIS query-compatibility issue, Campaign 012 was not closed at that point.

## Source-compatibility retry

The retry deliberately broadened only the **server fetch expression**, not the approved campaign target:

1. fetch all OSMRE records with `reclamation_bond_status = 1` (Phase I Release) inside the fixed Central Appalachia envelope;
2. enforce the approved Virginia / West Virginia / Kentucky contact gate locally;
3. require the approved 2019-01-01 through 2024-12-31 bond-status-date window locally;
4. retain the existing identity and >=40 m component-envelope gates locally.

The approved scientific target and all downstream ICESat-2 gates were unchanged.

## Live OSMRE diagnostics

The compatibility retry returned:

- raw Phase I feature count: **747**
- retained approved feature count: **0**
- outside approved contacts: **27**
- missing or unparseable reclamation-bond status date: **720**

The filter checks contact before date. Therefore the 720 date failures are the Phase I features that passed the Virginia / West Virginia / Kentucky contact gate but did not provide a usable reclamation-bond status date for the approved 2019–2024 screen.

No feature survived to the 40 m geometry screen because none survived the required date gate.

## ICESat-2 execution status

Because there were zero eligible official polygons:

- ICESat-2 ATL08 tile acquisition: **not started**
- campaign summary: **not created**
- tile cache: **not created**
- failed ATL08 tiles: **not applicable**
- raw terrain step-up series: **not evaluated**
- spatial clusters: **not evaluated**
- surviving candidates: **not evaluated**
- usable calibration rows: **0**
- numerical depth unlocked: **false**

Do not report Campaign 012 as an ICESat-2 scan with zero surviving candidates. The correct result is that the approved dated OSMRE Phase I target could not be instantiated from the live official source.

## Interpretation

The live source does show that Phase I records exist in the regional envelope, so the problem is not absence of Phase I features generally. The decisive blocker is missing/unusable `reclamation_bond_status_date` values on every Phase I feature that passed the approved state/contact gate.

Relaxing the date requirement would materially change the approved Campaign 012 design and would remove the feature that made Campaign 012 stronger than a status-only screen. That relaxation is not authorized and was not performed.

## Protected areas

Campaign 012 did not modify:

- classifier behavior;
- frontend behavior;
- Option 5 behavior;
- Tyrone Route A;
- main application depth behavior; or
- scientific thresholds.

## Final project state after Campaign 012

- Campaign 007: closed
- Campaign 008: closed
- Campaign 009: closed
- Campaign 010: closed
- Campaign 011: closed
- Campaign 012: **closed — official source lacks usable dated in-scope Phase I target**
- Tyrone Route A: pending EMNRD response
- usable numerical-depth calibration rows: **0**
- numerical depth: **blocked**

A Campaign 013 must not start automatically. It requires explicit user approval.
