# Option 1 Aitik WRD6 decisive result — 2026-07-29

## Decision

**NOT GOOD TO GO for numerical-depth calibration from the recovered public record.**

Aitik WRD6 is one of the strongest physical designs reviewed so far. It contains two large, long-monitored cover-system configurations that use the same nominal lower and upper materials and differ mainly by a 0.5 m protective-till increment. However, the public papers do not provide the final measured, coordinate-tied and uncertainty-qualified ground truth required by Option 1.

This work is classified as **Option 1 — Global Numerical Depth evidence research**. Option 3 is not active.

## Sources inspected

1. McKeown, Christensen, Taylor and Mueller (2015), *Evaluation of Cover System Field Trials with Compacted Till Layers for Waste Rock Dumps at the Boliden Aitik Copper Mine, Northern Sweden*, 10th ICARD / IMWA Annual Conference.
2. McKeown, Christensen, Cunningham and Mueller (2025), *Assessing mine closure and cover system design strategies with consideration for climate change risks at Aitik mine*, Mine Closure 2025, DOI `10.36487/ACG_repo/2515_93`.
3. The recovered PR #30 artifact `aitik-cover-trial-records`, including searchable text and rendered pages.

Recovered-file hashes:

```text
2015_construction.pdf = 831e8cedb538f3177aacc26a537fb701d18b89e66fce84d7c4e32672ae4ec33d
2025_climate_monitoring.pdf = 3cbd9630327d2e84e3f8401c9352de4fbb3339d427a3bb8943fc11b85d9da006
```

## What was proven

### Large, potentially radar-usable zones

- Two cover-system field trials were constructed on WRD6 in summer 2013.
- Both include relatively flat plateau sections approximately 50 m by 50 m, plus approximately 3H:1V slopes.
- The combined trial footprint is approximately one hectare.
- A plateau could potentially retain a 30–40 m clean interior after excluding boundaries and instrumentation, subject to exact surveyed geometry.

### Strong nominal shallow/deep pair

The published construction profiles are:

```text
Field Trial 1:
0.3 m compacted till
+ 1.0 m non-compacted protective till
+ 0.3 m till/organic mixture
= 1.6 m nominal total cover

Field Trial 2:
0.3 m compacted till
+ 1.5 m non-compacted protective till
+ 0.3 m till/organic mixture
= 2.1 m nominal total cover
```

This is a strong design comparison because the nominal compacted-till layer and surface growth-medium layer are the same, while the protective-till layer differs by 0.5 m.

### Construction and material-quality evidence

- The compacted till was constructed using a maximum 0.3 m lift thickness.
- The reported method used at least six passes with a 10-ton smooth-drum roller.
- Compaction trials included nuclear-densometer, water-content and hydraulic-conductivity testing.
- Reported density uncertainty in the compaction-treatment table applies to dry-density measurements from separate compaction trial pads. It is not final total-cover-thickness uncertainty for the two WRD6 polygons.

### Long-term stability evidence

- The 2025 paper reports eleven years of monitoring.
- Vegetation was established from approximately the 2014–2015 monitoring period.
- The monitored compacted-till layer was not reported to experience freeze/thaw or wet/dry cycling.
- No macro-scale erosion was observed.

This is unusually strong evidence that a stable Sentinel-1-era period may exist.

## Decisive failures

### 1. Final measured as-built thickness is missing

The 2015 paper states that the two systems were constructed using 1.0 m and 1.5 m protective-layer alternatives. Those numbers are construction-design descriptions.

Neither recovered paper publishes:

- final surveyed thickness for Field Trial 1;
- final surveyed thickness for Field Trial 2;
- polygon-level mean, minimum, maximum or standard deviation of final thickness;
- final surface-minus-subgrade survey calculations;
- an as-built thickness table tied to the plateau polygons.

The compaction tests measured dry density, water content and hydraulic conductivity. They do not establish that the nominal total depths of 1.6 m and 2.1 m were achieved uniformly across the trial plateaus.

### 2. Numerical thickness uncertainty is missing

The public record contains uncertainty or variation for some density and hydraulic measurements, but not for final layer or total-cover thickness.

No recovered source provides:

- construction-thickness tolerance;
- survey vertical accuracy;
- confidence interval for final cover depth;
- acceptance limits tied to final plateau thickness;
- uncertainty that can be assigned to a calibration depth value.

### 3. Coordinate-tied trial polygons are missing

Neither paper publishes:

- surveyed corners;
- northing/easting coordinates;
- coordinate reference system or datum;
- CAD/GIS treatment polygons;
- an official georeferenced as-built plan.

The statements `approximately 50 m by 50 m` and `approximately 1 ha` are not enough to assign the two depth conditions to exact Sentinel-1 polygons.

Satellite interpretation, DEM patterns or manually estimated corners cannot replace official treatment geometry.

### 4. Clean-interior and surface equivalence cannot be finalized

The nominal design is well matched, but exact surveyed geometry is needed to exclude:

- monitoring stations;
- plateau edges and slope breaks;
- roads and access areas;
- drains or local grading features;
- disturbed zones.

The public papers do not provide enough spatial information to prove that both trial plateaus contain equivalent 30–40 m clean interiors with comparable slope, aspect, roughness, vegetation and maintenance history.

### 5. Stability is strong but not sufficient by itself

The eleven-year monitoring record and absence of reported macro-scale erosion make Aitik stronger than many rejected candidates. However, stability cannot compensate for missing measured depth, uncertainty and official polygon geometry.

## Gate result

| Gate | Aitik result |
|---|---|
| Full-scale clean zones | Potentially yes |
| Strong nominal shallow/deep pair | Yes: 1.6 m versus 2.1 m total design |
| Same nominal near-surface construction | Yes in design |
| Final measured numerical depths | **No** |
| Numerical depth uncertainty | **No** |
| Coordinate-tied polygons | **No** |
| Equivalent clean radar interiors | Not proven |
| Stable Sentinel-1 period | Strongly supported in general, not polygon-finalized |
| Confirmed control for Option 4 | No |

## Final state

```text
candidate = Aitik WRD6 cover-system field trials
strategy_classification = Option 1 evidence research
documentary_gate = failed
failure_type = official_as_built_depth_and_geometry_missing
usable_positive_depth_site_groups_added = 0
usable_confirmed_negative_site_groups_added = 0
usable_calibration_rows_added = 0
earth_engine_query_executed = false
calibration_record_created = false
training_started = false
numerical_depth_ready = false
app_depth_enabled = false
option_3_active = false
```

## Reopening rule

Do not reopen Aitik because the nominal design is attractive or because monitoring is long.

Reopen only if a concrete official package becomes available containing:

1. final surveyed layer or total-cover thicknesses for both trial plateaus;
2. numerical thickness tolerance or survey accuracy;
3. coordinate-tied CAD/GIS/as-built polygons;
4. instrumentation and exclusion geometry sufficient to establish clean interiors;
5. plot-specific maintenance and disturbance history for the selected observation period.

## Next Option 1 action

Check whether the pending New Mexico EMNRD response for Tyrone Dam 3X has arrived. If it has not, continue only with another candidate whose missing records are explicitly identifiable as official CQA, as-built survey or construction-completion records. Do not run Earth Engine for Aitik.
