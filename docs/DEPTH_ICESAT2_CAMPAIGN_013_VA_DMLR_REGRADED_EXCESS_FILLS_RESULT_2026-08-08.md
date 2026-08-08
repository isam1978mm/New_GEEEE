# Campaign 013 — Virginia DMLR Regraded Excess-Material Fills — Final Result

Date: 2026-08-08
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: CLOSED — NO SURVIVING CANDIDATES

## Final decision

Campaign 013 completed successfully with no failed ATL08 tiles and no persistent upward terrain-step candidates inside the approved Virginia DMLR excess-material fill polygons.

The campaign therefore closes under Decision Rule C from the controlling plan:

- no raw upward steps;
- no failed tiles;
- no spatial clusters;
- no fill/regraded gate survivors;
- no records research;
- 0 usable calibration rows;
- numerical depth remains blocked.

No scientific threshold was weakened.

## Validation

Focused Campaign 013 validation passed before the live scan:

```text
13 passed in 0.50s
```

## Live scan result

Campaign ID:

`central_appalachia_earthwork_pilot_v13_va_dmlr_regraded_excess_fills`

Region ID:

`va_dmlr_regraded_excess_material_fills`

Final campaign status:

`no_surviving_candidates_in_va_dmlr_regraded_fills`

Scanner exit code:

`0`

## Exact counts

```text
bounding-box tile count                         78
selected polygon-intersecting tile count        11
completed tile count                            11
failed tile count                                0
cached tile count at scan start                  0

quality segments before polygon filter      153,668
segments rejected outside DMLR fill polygons153,432
quality segments retained after deduplication   236
exact segment series                            211

classification: insufficient_epochs             211
raw step-up segment count                         0
pre fill/regraded gate cluster count              0
fill/regraded gate rejected count                 0
surviving step cluster count                      0
surviving candidate count                         0
```

All 211 exact repeat-series assessments were classified `insufficient_epochs`.

## Interpretation

The official DMLR fill/regraded spatial targeting worked as designed, but the retained ATL08 repeat histories did not produce any persistent upward step satisfying the unchanged temporal and step gates.

Because there were zero raw upward-step series, the campaign never reached spatial clustering or the strict final fill + `Regraded` + same-permit identity gate.

This result does **not** mean the DMLR fills lack reclamation or regrading. It means the available ATL08 repeat coverage inside the retained official fill polygons did not provide a qualifying persistent upward terrain-step signal under the approved scientific thresholds.

## Records research

No Virginia DMLR records research is justified from Campaign 013 because there is no finalized spatial candidate to investigate.

`records_research_ready = false`

## Calibration effect

```text
Campaign 013 usable calibration rows = 0
Total newly usable rows from Campaign 013 = 0
Numerical depth unlocked = false
```

Numerical depth still requires at least two independent usable measured-depth anchors satisfying all calibration, geometry, stability, and radar-comparability requirements.

## Protected areas

No Campaign 013 change was made to:

- classifier behavior or classifier result pages;
- frontend application behavior;
- Option 5 outputs;
- Tyrone Route A records work;
- `main`.

Campaign 013 remains isolated on the protected depth branch.

## Next-action rule

Campaign 013 is closed. Do not spend additional time on this exact Virginia DMLR fill/regraded route unless materially new official data or a new approved scientific approach appears.

Do not start Campaign 014 without explicit user approval.
