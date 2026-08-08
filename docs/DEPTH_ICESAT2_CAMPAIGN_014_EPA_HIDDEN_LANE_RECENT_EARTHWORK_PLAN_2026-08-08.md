# Campaign 014 — EPA Hidden Lane Landfill Recent Earthwork

Date: 2026-08-08
Branch: `claude/depth-measurement-unblock-p2zjpd`
Status: APPROVED / PLAN LOCKED

## Objective

Continue the independent public/official calibration-anchor search after Campaign 013 without weakening any scientific gate and without changing application behavior.

Campaign 014 targets one unusually well-dated official EPA Superfund earthwork site: **Hidden Lane Landfill, Sterling, Virginia (EPA ID `VAD980829030`)**.

EPA identifies Operable Unit 3 as **LANDFILL CAP - SOURCE AREA**. The EPA Superfund schedule records remedial action beginning 2023-09-11 and completing 2025-11-06. EPA's cleanup narrative also reports that in early November 2024 the source-area excavation work had removed approximately 15,000 tons of contaminated soil and debris, after which the excavation was backfilled with clean fill and topsoil, graded, and hydroseeded.

The purpose of Campaign 014 is to test whether ICESat-2 ATL08 contains a persistent spatially supported upward terrain step inside the official EPA site polygon whose transition overlaps the documented OU3 earthwork window.

## Official sources

EPA national Superfund polygon layer:

`https://geopub.epa.gov/ArcGIS/rest/services/NEPAssist/NEPAVELayersPublic_fgdb/MapServer/14/query`

Target:

- EPA ID: `VAD980829030`
- Site: Hidden Lane Landfill
- City/state: Sterling, Virginia

EPA Superfund schedule / cleanup records:

- Site profile internal ID: `0302762`
- OU3: `LANDFILL CAP - SOURCE AREA`
- documented remedial-action window: 2023-09-11 through 2025-11-06
- source-area excavation/backfill/grading completion described by EPA: early November 2024

The EPA national polygon is an official Superfund site boundary. It is a discovery/spatial-control polygon, not an as-built cap survey.

## Why this campaign is materially different

Campaigns 007-010 used Florida FDEP phosphate mining/reclamation polygons.
Campaign 011 used Pennsylvania AML reclamation-complete polygons.
Campaign 012 attempted OSMRE Phase-I bond-release polygons but closed before ICESat-2 because the approved dated target was unavailable.
Campaign 013 used Virginia DMLR current excess-material fills plus regraded-status polygons but all retained repeat series lacked enough epochs.

Campaign 014 instead starts from a single EPA Superfund site with an explicit recent construction window tied directly to a landfill-cap/source-area remedial action and a public administrative record.

## Scientific interpretation limits

The EPA construction window is **event-timing evidence only**. It does not prove:

- placed-material thickness;
- measured depth;
- that an ATL08 step was caused specifically by cap placement rather than another OU3 earthwork activity;
- the exact cap footprint inside the broader official site boundary;
- a clean 30-40 m calibration area;
- radar-depth transferability.

A surviving cluster remains a provisional terrain-step candidate until the existing finalizer and later records/geometry/radar gates pass.

## Official polygon construction

1. Query the EPA Superfund polygon layer for `EPA_ID = 'VAD980829030'`.
2. Require polygon or multipolygon geometry.
3. Retain only polygon components whose WGS84 envelope spans at least 40 m in both dimensions. This is only a cheap footprint pre-screen and does not prove clean usable width.
4. Save the official EPA polygon as campaign evidence.
5. Constrain ATL08 acquisition and retained segments to the exact returned polygon geometry.

## Event-window integrity gate

After the unchanged temporal scan and spatial clustering, every surviving cluster must have its ATL08 transition interval overlap the documented EPA OU3 remedial-action window:

- earliest accepted transition date: 2023-09-11
- latest accepted transition date: 2025-11-06

A cluster entirely before or entirely after that window is rejected before records research.

The event-window gate does not change the step magnitude, plateau stability, neighbour, cluster, context, terminal-stability, or temporal-recovery thresholds.

## Campaign envelope

Discovery bounds around Sterling / eastern Loudoun County, Virginia:

- west: -77.70
- south: 38.80
- east: -77.10
- north: 39.20

The bounds are only for tiling. Exact official EPA polygon geometry controls retained ATL08 segments.

## Existing scientific gates — unchanged

```text
minimum distinct epochs          = 4
minimum observations per side    = 2
minimum upward step              = 0.30 m
maximum plateau NMAD             = 0.25 m
minimum dominant-jump fraction   = 0.60
neighbour connection distance    = 250 m
minimum neighbouring segments    = 3
maximum cluster step NMAD        = 0.25 m
cross-spot diagnostic distance   = 500 m
```

All existing mandatory finalizer, terminal-stability, temporal-recovery, context, and evidence gates remain unchanged.

No scientific threshold may be weakened merely to create a survivor.

## Execution safety

Campaign 014 includes the per-tile subprocess watchdog from the start:

- each live ATL08 tile receives a hard 300-second wall-clock limit;
- completed tiles remain cached and resumable;
- a timed-out tile becomes a recorded failed tile instead of hanging the campaign.

Any failed tile means the campaign is incomplete until the failure is resolved or explicitly documented as unrecoverable.

## Decision rules

### A. EPA source produces no usable Hidden Lane polygon

Campaign 014 remains incomplete/source-blocked. Diagnose only the source failure. Do not describe it as zero ICESat-2 candidates.

### B. Failed ATL08 tiles > 0

Campaign remains incomplete. Retry/fix only failures and preserve successful cache.

### C. No raw upward steps and no failed tiles

Close Campaign 014 with 0 candidates and 0 usable calibration rows. Numerical depth remains blocked.

### D. Raw steps exist but no spatial clusters

Close Campaign 014 as isolated steps rejected by the unchanged neighbour rule. Do not weaken the rule.

### E. Clusters exist but none overlaps the official 2023-09-11 through 2025-11-06 OU3 window

Close Campaign 014 with explicit event-window rejection counts. No records research.

### F. One or more clusters survive the event-window gate

Treat each as provisional only. Run the existing mandatory finalizer, terminal-stability, temporal-recovery, and context gates before records research.

### G. Finalized survivor

Use the existing EPA OU3 public administrative record and reports to recover, where available:

- exact cap/source-area construction footprint;
- remedial design and as-built drawings;
- surveyed elevations / survey control;
- cap or clean-fill layer thicknesses and tolerances;
- construction-quality assurance measurements;
- exact dates of fill/topsoil placement and grading;
- stable post-construction area at least roughly 30-40 m wide;
- surface materials and vegetation relevant to radar comparability.

Only record-supported measured/as-built thickness can become a usable calibration row.

## Protected areas

Campaign 014 may not modify:

- classifier behavior or classifier result pages;
- frontend application behavior;
- Option 5 outputs;
- Tyrone Route A records work;
- `main`.

All Campaign 014 work remains isolated on the protected depth branch.

## Numerical-depth rule

Numerical depth remains blocked unless at least two independent usable measured-depth anchors satisfy every required calibration gate.
