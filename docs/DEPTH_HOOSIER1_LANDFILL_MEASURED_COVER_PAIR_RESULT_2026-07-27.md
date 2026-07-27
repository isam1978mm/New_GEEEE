# Hoosier #1 Landfill measured-cover pair result - 2026-07-27

## Decision

**NOT GOOD TO GO**

Hoosier #1 contains some of the strongest coordinate-tied final-cover measurements found during this search. The evidence still does not create a valid numerical-depth calibration pair for the app.

The measured 2009 closure package covers a 1.85-acre south-slope strip and provides 18 coordinate-tied thickness measurements. Those measurements vary irregularly and do not form two separate broad shallow/deep polygons. The older approximately 39-acre soil cap has a comparable visible surface profile by design, but the recovered public record does not publish its final measured as-built thicknesses.

## Why the site looked promising

The public record describes two large closed areas:

- approximately 39.1 acres with the older soil final cover;
- approximately 27.0 acres with a composite final cover;
- final closure approval granted on December 2, 2010.

The older closure plan and the newer certification package both describe a similar radar-facing upper profile:

- approximately 30 inches of protective soil;
- 6 inches of vegetative soil or vegetative cover.

This made Hoosier a stronger same-surface candidate than many earlier sites.

## Strong measured evidence recovered

The May 2009 *Certification of Partial Closure Report* covers the Cell 1 South Slope, an area of 1.85 acres.

The report includes:

- professional-engineer closure certification;
- final-cover survey results;
- thickness-verification results;
- northing and easting coordinates;
- actual subgrade elevations;
- actual top-of-soil-barrier elevations;
- actual top-of-cover elevations;
- a coordinate-labelled as-built final-cover drawing;
- comparison of design and as-built final grades.

### Measurement geometry

The table contains 18 measurements arranged as six toe/mid-slope/crest transects.

The coordinate range is approximately:

```text
northing: 10,499.96 to 10,691.91
 easting: 10,489.87 to 11,004.44
```

This gives an outer coordinate envelope of roughly:

```text
192 ft by 515 ft
59 m by 157 m
```

The actual certified area is irregular and totals only 1.85 acres.

### Measured thicknesses

The coordinate-tied table reports:

```text
soil-barrier thickness:       2.00 to 3.07 ft
protective-soil thickness:    2.80 to 4.33 ft
combined thickness:           5.12 to 6.42 ft
```

The combined values above exclude the 6-inch vegetative layer.

These are actual measured values, not only design specifications.

## Fatal blocker 1: the measurements do not form two depth zones

The 18 measured values vary irregularly among toe, mid-slope and crest locations.

There is no consistent pattern such as:

- one broad shallow half and one broad deep half;
- a surveyed shallow polygon beside a surveyed deep polygon;
- two independently bounded cells with one certified depth each.

The toe, mid-slope and crest averages are also similar. The variation occurs point by point rather than as two coherent areas.

Creating shallow and deep polygons by interpolating between selected points would violate the locked requirement for exact measured zones.

## Fatal blocker 2: clean Sentinel-1 interiors are not proven

The measured area is a long south-slope strip bounded by the cover edge and adjacent closure features.

Its outer coordinate envelope is wide enough only in a very general sense. The public record does not prove that two independent measured conditions each retain a 30-40 m clean interior after excluding:

- cover boundaries;
- toe and crest transitions;
- drainage features;
- gas and leachate infrastructure;
- access and maintenance areas.

One narrow measured strip cannot supply two robust radar conditions.

## Fatal blocker 3: the older full-scale area lacks measured as-built depths

The approximately 39.1-acre older soil-cover area is documented in the 1995/1996 design and post-closure records.

Those records provide:

- planned final contours;
- closure-layer specifications;
- testing and quality-control requirements;
- survey-control requirements;
- post-closure planning.

They do not publish:

- final coordinate-tied thickness measurements;
- a subgrade-versus-finished-grade table;
- an as-built thickness grid;
- numerical depth uncertainty.

Therefore, the older large area cannot become the second measured condition.

## Fatal blocker 4: the full composite area lacks an absolute thickness grid

The recovered 2008 final-cover as-built drawing covers the broader composite area and shows design and as-built final grades on a State Plane coordinate grid.

However, final surface elevation alone does not establish cover thickness.

The public package does not provide a matching pointwise subgrade or layer-base elevation grid across the entire approximately 27-acre area. The absolute thickness measurements remain limited to the 1.85-acre partial-closure section.

## Fatal blocker 5: numerical uncertainty is missing

The survey drawings identify the coordinate system and carry professional-surveyor certification.

The recovered records do not state a numerical horizontal or vertical uncertainty that can be attached to the calibration values.

## Calibration decision

```text
full-scale vegetated closure areas = yes
coordinate-tied final measurements exist = yes, but only in a 1.85-acre strip
measured survey points = 18
measured barrier thickness = 2.00-3.07 ft
measured protective thickness = 2.80-4.33 ft
combined measured thickness = 5.12-6.42 ft
exact broad shallow/deep polygons = no
older 39.1-acre cap has measured as-built depths = no
full 27-acre composite area has absolute thickness grid = no
two independent 30-40 m clean interiors proven = no
matching visible upper profile supported by design = yes
matching final soil construction fully proven = no
numerical survey uncertainty = no
usable calibration row created = no
Earth Engine query executed = no
training started = no
app depth enabled = no
plan changed = no
```

Final decision:

```text
NOT_GOOD_TO_GO_SECOND_MEASURED_ZONE_AND_UNCERTAINTY_FAILED
```

## Sources reviewed

- IDEM Closure Approval dated December 2, 2010.
- *Certification of Partial Closure Report - Cell 1 South Slope - 1.85 Acres*, May 2009.
- 2008 final-cover certification and as-built drawing set.
- *Revised Solid Waste Closure and Post-Closure Plan*, October 1996.
- 1995 Ransbottom Sanitary Landfill drawing package.
- IDEM Virtual File Cabinet public records recovered through temporary PR #18.

## Next step

Continue the approved search unchanged. Advance only a full-scale vegetated closure package that publishes two coordinate-tied broad final measured depth zones, numerical uncertainty, matching final upper-soil construction, at least 30-40 m clean interior for each condition, and a stable Sentinel-1 observation period.
