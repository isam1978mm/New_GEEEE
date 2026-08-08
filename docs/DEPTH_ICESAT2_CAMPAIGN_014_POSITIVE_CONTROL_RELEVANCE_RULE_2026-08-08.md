# Campaign 014 Positive-Control Site-Relevance Rule

Date: 2026-08-08

## Purpose

Correct the execution-only site-relevance proof used when a CMR-listed ATL08
resource remains unreadable after the normal Campaign 014 broad-query retries
and explicit per-resource retries.

This does not change any scientific threshold, EPA event gate, finalizer,
classifier, frontend, Option 5 behavior, Tyrone evidence, or application output.

## Why the previous rule was too strict

The previous site-relevance launcher required the failed RGT to be returned by
OpenAltimetry inside the current 25 km acquisition tile and absent from the
tight EPA Hidden Lane envelope.

The final rebuild showed that both known failed resources returned no tracks in
the individual acquisition-tile checks, even though earlier independent probes
had already shown their RGTs inside the broader Campaign 014 control bounds.
That tile-presence requirement therefore kept scientifically irrelevant CMR
near-miss resources blocking the scan.

## Correct proof

A failed resource may be excluded from Campaign 014 tile completeness only if
OpenAltimetry proves both conditions for the resource's exact date and RGT:

1. the RGT is present inside the broad Campaign 014 control bounds
   `(-77.70, 38.80, -77.10, 39.20)`; and
2. the RGT is absent from the tight official EPA Hidden Lane envelope
   `(-77.42677485999997, 39.052508687000056, -77.41625001099999, 39.06693744100005)`.

The positive control prevents an empty EPA-envelope response from being treated
as proof when the OpenAltimetry service/date is unavailable.  EPA-envelope
absence then proves that the track cannot contribute any observation inside the
EPA polygon contained within that envelope.

The failed resource remains blocking if:

- the RGT is absent from the positive-control bounds;
- the RGT is present inside the EPA envelope;
- either OpenAltimetry request fails; or
- the response is otherwise ambiguous.

## Known resources motivating the correction

- `ATL08_20210504235905_06291102_007_01.h5` — RGT 0629, 2021-05-04
- `ATL08_20251226145703_01873002_007_01.h5` — RGT 0187, 2025-12-26

Independent Campaign 014 probes already showed both RGTs in the broad control
bounds and absent from the exact EPA envelope.

## Implementation

Launcher:

`scripts/run_icesat2_epa_hidden_lane_campaign_014_with_control_relevance_recovery.py`

Tests:

`tests/unit/test_run_icesat2_epa_hidden_lane_campaign_014_with_control_relevance_recovery.py`

The launcher layers the corrected proof on top of the existing strict
site-relevance recovery.  It does not alter the underlying scanner or scientific
gates.

## Next action

Run a forced Campaign 014 rebuild with the positive-control launcher.  Accept a
scientific Campaign 014 result only if all selected tiles complete with zero
failed tiles.  If any failed resource cannot meet the positive-control proof,
Campaign 014 remains incomplete.
