# Campaign 014 — EPA Hidden Lane Recent Earthwork — Final Result

Date: 2026-08-09
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: CLOSED — NO SURVIVING CANDIDATES

## Final decision

Campaign 014 completed successfully after strict recovery of the ATL08 acquisition tiles and independent site-relevance proof for the two persistently unreadable, off-site ATL08 resources.

The final accepted scan has:

- 2 completed selected tiles;
- 0 failed tiles;
- 30 retained quality segments after exact EPA-polygon filtering and deduplication;
- 30 exact segment series;
- all 30 exact series classified `insufficient_epochs`;
- 0 raw upward-step series;
- 0 pre-event-window clusters;
- 0 surviving clusters;
- 0 surviving candidates;
- 0 usable calibration rows;
- numerical depth still blocked.

No scientific threshold was weakened.

## Validation

Focused Campaign 014 validation passed before the final accepted rebuild:

```text
37 passed in 0.84s
```

## Live scan result

Campaign ID:

`mid_atlantic_earthwork_pilot_v14_epa_hidden_lane_recent_earthwork`

Region ID:

`epa_hidden_lane_landfill_recent_ou3_earthwork`

Final campaign status:

`no_surviving_candidates_in_epa_hidden_lane_recent_earthwork`

Scanner exit code:

`0`

## Exact counts

```text
bounding-box tile count                               6
selected polygon-intersecting tile count              2
completed tile count                                  2
failed tile count                                     0
cached tile count at scan start                       0

quality segments before EPA polygon filter       58,199
segments rejected outside EPA polygon            58,169
quality segments retained after deduplication         30
exact segment series                                  30

classification: insufficient_epochs                   30
raw step-up segment count                              0
pre-event-window cluster count                         0
event-window rejected count                            0
surviving step cluster count                           0
surviving candidate count                              0
```

All 30 exact repeat-series assessments were classified `insufficient_epochs`.

## Off-site unreadable-resource resolution

The original SlideRule/ATL08 reads remained partial because two specific release-007 resources repeatedly produced H5Coro read failures:

- `ATL08_20210504235905_06291102_007_01.h5` — 2021-05-04, RGT 0629;
- `ATL08_20251226145703_01873002_007_01.h5` — 2025-12-26, RGT 0187.

Campaign 014 did not silently drop these resources.

Independent no-account OpenAltimetry probes were run before the final rebuild and saved locally. The saved proof showed, for each exact date/RGT:

1. the target RGT was present inside the broad Campaign-014 control bounds; and
2. the target RGT was absent from the tight official EPA Hidden Lane envelope.

The saved proof decisions were:

```text
2021-05-04 RGT 0629:
  control decision = target_track_intersects_campaign_bounds
  exact EPA decision = target_track_absent_from_exact_epa_envelope

2025-12-26 RGT 0187:
  control decision = target_track_intersects_campaign_bounds
  exact EPA decision = target_track_absent_from_exact_epa_envelope
```

The exact EPA envelope used by the proof was:

```text
west  = -77.42677485999997
south =  39.052508687000056
east  = -77.41625001099999
north =  39.06693744100005
```

Because a track absent from this envelope cannot contribute observations inside the EPA polygon contained by the envelope, the two failed resources were proven irrelevant to the Hidden Lane site. The final rebuild therefore excluded only those persistently failed, independently proven off-site resources from tile completeness.

The exclusion rule failed closed: missing, malformed, contradictory, or EPA-present saved evidence would have kept the affected tile incomplete.

## Interpretation

The official EPA Hidden Lane spatial targeting and OU3 earthwork timing gate worked as designed, but the retained ATL08 repeat histories did not provide enough epochs to produce a qualifying persistent upward terrain-step signal under the unchanged Campaign 014 scientific thresholds.

Because there were zero raw upward-step series, the campaign never produced a spatial cluster or a candidate requiring records follow-up.

This result does **not** prove that no OU3 landfill-cap/source-area earthwork occurred. EPA documents establish recent OU3 remedial earthwork. The result means that the available qualifying ATL08 repeat observations inside the official EPA Hidden Lane polygon did not produce a qualifying persistent upward-step candidate under the approved method.

The EPA OU3 construction window is timing evidence only. It is not measured depth, placed-material thickness, exact cap as-built geometry, or proof of radar-depth transferability.

## Records research

No additional Hidden Lane records research is justified from Campaign 014 because there is no finalized spatial candidate to investigate.

`records_research_ready = false`

## Calibration effect

```text
Campaign 014 usable calibration rows = 0
Total newly usable rows from Campaign 014 = 0
Numerical depth unlocked = false
```

Numerical depth still requires at least two independent usable measured-depth anchors satisfying the existing calibration, geometry, stability, and radar-comparability requirements.

## Tyrone status

The separate Tyrone EMNRD request `N000019-072826` is CLOSED. EMNRD/MMD confirmed that no additional records exist beyond the package already supplied. There is no agency-response wait remaining on that request.

The remaining Tyrone task is the final audit of the existing records package; Campaign 014 does not change the Tyrone evidence decision.

## Protected areas

No Campaign 014 change was made to:

- classifier behavior or classifier result pages;
- frontend application behavior;
- Option 5 outputs;
- Tyrone Route A evidence files on `main`;
- `main`.

Campaign 014 remains isolated on the protected depth branch.

## Next-action rule

Campaign 014 is closed. Do not spend additional time on the exact EPA Hidden Lane route unless materially new official data or a newly approved scientific approach appears.

Do not start Campaign 015 without explicit user approval.
