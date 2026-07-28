# Option 1 — Fort Dix Landfill decisive review — 2026-07-28

## Decision

**NOT GOOD TO GO for numerical depth.**

Fort Dix is large and stable, but its two remedy areas do not form a valid numerical-depth calibration pair.

## What the official record supports

EPA documents a 126-acre landfill and a selected remedy that:

- capped the southernmost 53 acres;
- maintained two feet of existing final cover over the remaining landfill;
- completed Phase II in fiscal year 1997;
- uses long-term inspections, mowing, erosion control and site security;
- was still functioning as intended in the 2023 five-year review, with no condition changes affecting protectiveness.

The site therefore passes the broad size and stability screens.

## Fatal blockers

### 1. The northern area is not a confirmed control

The remaining northern area is still part of the same landfill. Maintaining existing cover over waste does not establish a no-target or background condition.

### 2. The two-foot statement is not final measured as-built truth

The reviewed public record states that two feet of existing cover must be maintained. It does not provide a coordinate-tied final survey proving a measured two-foot thickness throughout a clean polygon.

A design or maintenance minimum cannot be used as `known_depth_top_m` under the calibration contract.

### 3. The southern cap is not published as a measured numerical polygon

The ROD identifies a clay or geomembrane cap over the southern area, but the reviewed public record does not provide:

- a final pointwise thickness grid;
- two exact numerical depth polygons;
- numerical vertical uncertainty;
- a certified as-built depth table tied to radar-ready polygons.

### 4. Surface construction and vegetation are not matched

EPA describes older landfill portions as re-vegetated with ash and pine trees, while newer portions naturally re-vegetated and the completed remedy is maintained by mowing. These histories do not establish one matching radar-facing surface assembly across the two areas.

### 5. No second valid numerical reference remains

Without a measured northern depth, measured southern depth, or confirmed control, the site cannot produce a calibration record, local calibration, or ordering test under the locked plan.

## Gate table

| Requirement | Result |
|---|---|
| Full-scale areas | Pass |
| 30–40 m clean-interior potential | Plausible |
| Stable Sentinel-1 period | Pass in principle |
| Final measured as-built numerical depth | Fail |
| Exact second measured depth or confirmed control | Fail |
| Coordinate-tied thickness geometry | Fail |
| Numerical uncertainty | Fail |
| Matching radar-facing surface | Fail |

## Final status

```text
candidate = Fort Dix Landfill
decision = not_good_to_go
fatal_blocker = no_two_coordinate_tied_final_measured_depth_conditions_and_no_confirmed_control
calibration_record_created = false
earth_engine_query_executed = false
training_started = false
usable_calibration_rows = 0
numerical_depth_ready = false
app_depth_enabled = false
```

## Official sources

- EPA Fort Dix cleanup profile: https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0201164
- EPA Fort Dix Record of Decision: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=9100Q06P.TXT
- EPA Fort Dix site summary: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P10143E3.txt

## Reopening rule

Do not reopen Fort Dix unless a new official package provides all of the following:

1. certified final as-built thickness measurements for the southern cap;
2. certified final thickness measurements for a second large area or an independently confirmed no-target control;
3. coordinate-tied polygons;
4. numerical survey uncertainty;
5. matching near-surface construction and vegetation;
6. disturbance-free Sentinel-1 dates for both areas.
