# ICESat-2 Campaign 007 Final Closure

Date: 2026-08-06

## Controlling decision

Campaign 007 is closed with zero usable numerical-depth anchors.

Candidate 001 is rejected as a depth anchor. Its persistent ICESat-2 terrain rise remains a valid surface-elevation observation, but the official Ona Mine records do not support corresponding HI-3 mining, disturbance, reclamation, or measured placed-material thickness during the candidate event window.

```text
campaign_id                     = southeast_us_earthwork_pilot_v7_fdep_active_mines
candidate                       = rank 001
candidate status                = rejected as numerical-depth anchor
campaign usable anchor count    = 0
records_research_ready          = false
numerical_depth_unlocked        = false
```

This decision supersedes the active Campaign 007 search plan for Candidate 001.

## Candidate 001 automated evidence

Candidate 001 passed the automated discovery and context gates that were required before records review:

```text
median persistent terrain rise  = 0.5614787936210632 m
supporting ATL08 segments       = 4
support-line spatial extent     = about 225.6 m
event start                     = 2022-10-01
event end                       = 2024-03-29
recovery-like segments          = 0 / 4
follow-up segments              = 4 / 4
terminal reversal-like segments = 0 / 4
terminal retention fraction     = 1.0682540354591497
context-priority status         = context_review_priority
cross-spot support              = false
```

The Earth Engine context audit did not detect an agricultural, built, bare-ground, or water-dominated rejection condition. The footprint was predominantly grass and shrub context before, during, and after the event.

These results support a persistent terrain change. They do not establish its cause or placed-material thickness.

## Exact official footprint identity

The point-by-point FDEP audits resolved one shared active-mine and reclamation-unit footprint for all four supporting segments:

```text
mine                            = Ona
operator                        = Mosaic
FDEP site ID                    = 169281
reclamation unit                = HI-3
2021 reclamation status         = WF / Work Future
2021 mined-unit matches         = 0 / 4
```

This passed the geometry-identification gate and permitted review of the existing official annual-report package. It did not itself prove activity during the ICESat-2 event window.

## Official records package inspected

Source package:

```text
Ona_HI3_2022_2024_FDEP_Documents.zip
```

The package contains the 2022, 2023, and 2024 Ona annual-report records, including nested annual-report archives. After extraction, the package included 80 PDF documents, two XLSX files, and the nested ZIP archives.

The decisive records were:

```text
2022/Form 2/2022_Form 2_Ona_signed.pdf
2022/Spreadsheets/2022_ONA Spreadsheet.pdf
2023/Form 2/2023_Form 2_Ona_signed.pdf
2023/Spreadsheets/2023_ONA Spreadsheet.pdf
2024/Form 2/2024_Form 2_Ona_Signed.pdf
2024/Spreadsheets/2024_ONA Spreadsheet.pdf
```

The package also contained as-built or certification records for other named areas, including East Horse Creek phases and West Fork Horse Creek. None was identified as HI-3 or tied to the Candidate 001 ATL08 support line.

## Decisive annual-report findings

### 2022

The 2022 Form 2 states that no reclamation occurred in 2022. It also states that no sand-tailings disposal occurred within Ona in 2022.

The 2022 Ona spreadsheet lists HI-3 as:

```text
parcel area                      = 293.7 acres
release status                   = NR
reported mined/disturbed values = 0
revegetated/released values      = 0
```

### 2023

The 2023 Form 2 states that no reclamation occurred in 2023. It reports waste-clay deposition in O1-B and sand-tailings placement in utility or dragline walkpath corridors, but it does not identify HI-3 as an activity area.

The 2023 Ona spreadsheet again lists HI-3 with NR status and zero reported mined, disturbed, revegetated, and released values.

### 2024

The 2024 Form 2 reports 87.0 mined acres and 4.3 disturbed acres contoured to final grade at the mine level. It identifies sand-tailings backfill in O2 and HC-3, not HI-3.

The 2024 Ona spreadsheet again lists HI-3 with NR status and zero reported mined, disturbed, revegetated, and released values.

The mine-wide 2024 totals cannot be transferred to HI-3 or to the Candidate 001 support line.

## Missing required depth-anchor evidence

No reviewed HI-3 record provides any of the following:

```text
HI-3 activity confirmed during 2022-10-01 through 2024-03-29
coordinate-tied HI-3 as-built survey covering all supporting segments
pre-placement and post-placement HI-3 elevations
certified placed-material thickness
lift-thickness measurements
cross-sections tied to the ATL08 support line
final grading quantities or contours identified as HI-3
proof that one uniform placed-material layer caused the 0.561 m rise
```

Therefore, the ICESat-2 terrain rise must not be relabeled as fill depth, cover thickness, buried-object depth, or radar calibration depth.

## Candidate 001 final decision

```text
location inside Ona Mine                = supported
location inside HI-3                    = supported
persistent surface-elevation rise       = supported
obvious land-cover confounder            = not detected
HI-3 event-window activity              = not supported
HI-3 measured placed thickness          = not supported
candidate_is_depth_anchor               = false
candidate_is_placed_thickness_measurement = false
candidate accepted for radar calibration = false
```

Candidate 001 is closed and rejected as a numerical-depth anchor.

Do not continue the Ona HI-3 route unless a new official document is independently supplied that contains a coordinate-tied HI-3 as-built survey, certified pre/post elevations, or measured placed-material thickness covering the Candidate 001 support line.

No recurring HI-3 monitoring task is active.

## Campaign 007 final decision

```text
source spatial candidates        = 3
final context-review candidates  = 1
accepted depth anchors           = 0
record lookup priority           = empty
records_research_ready           = false
numerical_depth_unlocked         = false
campaign status                  = closed_no_usable_depth_anchor
```

Candidate 002 remains deferred for insufficient spatial support.

Candidate 003 remains deferred for direct-thickness magnitude and insufficient spatial support.

Candidate 001 is rejected by the official activity-and-thickness evidence gate.

Campaign 007 is closed. Do not run more Campaign 007 searches, finalizers, Earth Engine audits, Ona document searches, or FDEP unit checks.

## Current numerical-depth status

```text
Campaign 006                     = closed, zero official-footprint survivors
Campaign 007                     = closed, zero usable depth anchors
Tyrone official measured depths = available
Tyrone exact georeference        = still pending existing records route
Tyrone usable radar calibration  = not yet established
numerical depth                  = blocked
```

The existing Tyrone records route remains pending. This closure does not change the Tyrone Test Plot 5 and Test Plot 6 measured-depth evidence or authorize a substitute georeference.

## Next campaign control

Campaign 008 is not approved or started.

A new Campaign 008 requires the user's explicit `go`. Do not infer approval from this closure and do not begin a new geographic search automatically.

Until that explicit approval:

```text
new campaign work                = stopped
new public-record requests       = not authorized
classifier changes               = not authorized
frontend changes                 = not authorized
Option 5 changes                 = not authorized
production depth changes         = not authorized
main branch changes              = not authorized
```

## Protection boundary

This closure is documentation-only. It does not modify:

- classifier behavior or classifier results;
- Option 5 anomaly or surface-change outputs;
- frontend panels;
- production numerical-depth behavior;
- calibration records;
- app artifacts;
- Tyrone Route A or Route B evidence;
- `main`.
