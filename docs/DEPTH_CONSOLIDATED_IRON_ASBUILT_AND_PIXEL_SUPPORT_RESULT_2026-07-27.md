# Consolidated Iron As-Built and Pixel-Support Result — 2026-07-27

## Decision

```text
NOT GOOD TO GO FOR THE CURRENT 20 M SENTINEL-1 DEPTH TEST
```

Consolidated Iron and Metal is the strongest same-surface measured-depth candidate recovered so far. New York DEC publicly provides the 2012 Final Engineering Report and the 2014 Final Site Management Plan. Those records contain the final as-built drawings, excavation-depth map, post-excavation cross section, measured cover depths, licensed-surveyor documentation, and a numerical survey tolerance.

The site nevertheless fails the clean 20 m geometry gate. The only fully documented shallow cell whose uncertainty range remains separate from the broad 6-foot deep area is 50 feet wide, or 15.24 metres. It cannot contain one clean 20 m Sentinel-1 footprint even before applying any boundary-position or infrastructure margin.

No Earth Engine query was run and no calibration row was created.

## Evidence recovered

```text
Final Engineering Report = recovered
Final Site Management Plan = recovered
Final as-built plan = recovered
Depth-of-excavation map = recovered
Post-excavation cross section = recovered
Licensed surveyor = yes
Survey elevation tolerance = +/- 0.5 ft
Measured final cover range = 3.0 to 6.2 ft
```

The final surface assembly is comparable across the site:

```text
clean structural/backfill soil
+ minimum 6 inches topsoil
+ hydroseeded vegetative cover
```

A geotextile demarcation layer separates the clean backfill from the remaining soil. The relevant depth is the final vegetated surface to that geotextile interface.

## Survey and depth evidence

The Final Engineering Report states that excavation and backfill surveying was performed by a New York State licensed surveyor. Excavation elevations and lift-layer depths were verified to within +/- 0.5 feet.

The report's design/as-built table provides actual excavation elevation, final regrade elevation and final cover depth at the site grid points. Measured final cover values range from 3.0 to 6.2 feet.

The broad interior contains many 6.0-foot points. The local shallow cluster contains:

```text
G12 = 3.6 ft
H12 = 3.0 ft
G10 = 4.8 ft
H10 = 4.2 ft
```

## Conservative depth-ordering test

Use the same +/- 0.5-foot tolerance on both conditions.

For a 6.0-foot deep reference:

```text
deep lower bound = 6.0 - 0.5 = 5.5 ft
```

To remain non-overlapping, a shallow measured depth must be no greater than:

```text
shallow upper bound <= 5.5 ft
measured shallow depth + 0.5 <= 5.5
measured shallow depth <= 5.0 ft
```

The only complete grid cell whose four corners all satisfy that limit is the G-to-H cell between Lines 200 and 300.

```text
cell corner depths = 3.6, 3.0, 4.8, 4.2 ft
east-west spacing = 50 ft = 15.24 m
north-south spacing = 100 ft = 30.48 m
```

A footprint fully contained in that cell can have at most 15.24 m of clean interior diameter. The required diameter is 20 m.

```text
clean 20 m shallow footprint = no
pixel-support decision = HOLD_PIXEL_SUPPORT_FAILED
```

Expanding westward would include F10 at 5.7 feet and lose robust non-overlap. Expanding eastward reaches the site edge or I10 at 6.0 feet. The second shallow feature near I4-I6 is also a narrow strip surrounded by 6-foot points.

Interpolating beyond the surveyed cell or drawing an analyst-estimated shallow zone is not approved.

## Surface stability

EPA and New York DEC continue to inspect and manage the soil cover. The most recent federal review reports that the remedy remains protective. Surface stability was not used to approve execution because the geometry gate failed first.

## What remains valid

```text
same final radar-facing surface = yes
actual measured depth values = yes
numerical survey tolerance = yes
professional as-built drawings = yes
physical site size = sufficient for deep reference zones
```

## What is not approved

```text
clean 20 m shallow zone = no
WGS84 execution polygons = no
Sentinel-1 catalogue query = no
Earth Engine query = no
calibration row = no
numerical depth training = no
app depth output = no
```

## Machine-readable result

```text
data/consolidated_iron_depth_pair_pixel_support_result.json
```

## Current status

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
consolidated_iron_same_surface = yes
consolidated_iron_actual_depths = yes
consolidated_iron_survey_uncertainty = yes
consolidated_iron_clean_20m_shallow_zone = no
consolidated_iron_calibration_row_ready = no
```

## Next step

Continue only with a larger completed project that provides the same final vegetated surface, exact as-built depth geometry, supported uncertainty, and at least one shallow and one deep zone wider than 20 metres after all margins.
