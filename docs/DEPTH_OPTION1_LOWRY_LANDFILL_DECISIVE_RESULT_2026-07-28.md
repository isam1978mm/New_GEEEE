# Option 1 — Lowry Landfill decisive documentary result — 2026-07-28

## Decision

**NOT GOOD TO GO for numerical-depth calibration.**

Lowry is a strong public near-miss because it is large, vegetated, construction-complete, managed over the long term, and publicly described as having substantial cover-thickness variation. It still fails the calibration evidence contract.

## What the official record establishes

EPA documents the following:

- municipal waste disposal ended in 1990;
- a soil cover was installed over the roughly 200-acre main landfill;
- the cover is at least 4 feet thick and up to 12 feet thick in some places;
- in 1999, 2 additional feet of soil were placed on the 29-acre north face to provide a minimum cover thickness of 4 feet over the entire closed landfill area;
- EPA certified site construction complete in 2006;
- the site remains in long-term operations, maintenance, and monitoring.

Reviewed official sources:

- EPA site profile: https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0800186
- EPA Information Update No. 17: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1016WLK.TXT
- EPA 1994 Record of Decision: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=91001SW5.TXT
- EPA Return to Use summary: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1007WT2.TXT

## Why the thickness statements are insufficient

### 1. No exact deeper reference polygon

The phrase “up to 12 feet in some places” does not identify a named polygon, surveyed boundary, or broad area with one final measured depth.

A maximum observed somewhere on a 200-acre landfill cannot be converted into a calibration zone.

### 2. The north face provides only a minimum

The 29-acre north face is geographically meaningful, but the public statement says that 2 feet were added to provide a **minimum** total cover of 4 feet.

It does not provide:

- the final point-by-point or polygon-level cover depth;
- a mean or bounded depth interval for the north face;
- a second exact measured zone elsewhere on the landfill.

### 3. No numerical measurement uncertainty

The reviewed public official sources did not provide a numerical horizontal or vertical survey tolerance, depth measurement uncertainty, or confidence interval for the final cover thicknesses.

### 4. Cover variation is tied to grading, not a frozen pair

The broad 4-to-12-foot range reflects site grading and variable fill thickness. Without final as-built top-and-bottom surfaces or a certified thickness grid, two zones would have to be invented from terrain or satellite appearance.

That is prohibited by the calibration contract.

### 5. No confirmed control area

The reviewed sources do not identify a nearby, surface-comparable confirmed no-target area that can be used as an independent negative record.

## Gate result

```text
full-scale vegetated area = yes
construction complete and managed = yes
broad public thickness variation = yes
two exact final measured depth polygons = no
coordinate-tied as-built thickness grid = no
numerical depth or survey uncertainty = no
confirmed control area = no
matching-surface pair proven = no
stable Sentinel-1 period for exact pair = not established
```

## Scientific decision

Lowry cannot create a positive calibration row.

Do not:

- draw a 12-foot zone from imagery;
- treat the entire non-north-face area as a deeper reference;
- assign exactly 4 feet to every point on the north face;
- infer depth from final terrain elevation;
- run Earth Engine as a substitute for the missing as-built evidence.

## App status

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
Earth Engine query executed = no
training started = no
numerical depth ready = no
app depth enabled = no
```

## Reopening rule

Reopen Lowry only if a new official record supplies all of the following:

1. certified final as-built top and underlying-reference surfaces, or an equivalent thickness grid;
2. at least two broad coordinate-tied depth polygons with final measured values;
3. numerical survey or measurement uncertainty;
4. matching radar-facing surface construction;
5. a documented unchanged observation period.

## Next action

Close Batch 2 with no passing candidate. Continue Option 1 only through another bounded candidate batch, while Tyrone Dam 3X remains pending under EMNRD request `N000019-070026`.
