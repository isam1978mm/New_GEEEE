# Dixie Auto Salvage final engineering report result - 2026-07-27

## Decision

**NOT GOOD TO GO**

The official 205-page Final Engineering Report was recovered and reviewed, including the final top-of-HDPE and topsoil as-built survey drawings.

Dixie is a strong near-miss because the report documents both a vegetated capped area and a separate excavated/restored area. It still cannot support a defensible Sentinel-1 positive/negative calibration pair from the public package.

## What the report confirms

### Positive area - uplands consolidation cap

The completed cap contains:

- 30 inches of protective soil;
- a minimum 6 inches of topsoil;
- a minimum combined soil thickness of 36 inches, or 0.9144 m;
- hydroseeding with a Class 2 roadside seed mix.

During construction, protective-soil thickness and combined cover thickness were measured every 50 to 75 feet using a probe. Additional soil was placed where necessary until the minimum thicknesses were reached.

The report includes:

- an as-built top-of-HDPE drawing based on a June 1999 professional field survey;
- an as-built topsoil drawing based on a July 1999 professional field survey.

### Possible negative area - former residential yard and driveway

The report confirms that:

- the yard and driveway were excavated one foot;
- 23 confirmation samples were collected on an approximate 50-foot grid;
- two corner areas failed initially and were excavated another foot;
- the replacement samples passed;
- the area was then backfilled and restored;
- later construction reporting refers to topsoil placement in the former Burris yard;
- all disturbed areas were to be seeded, fertilized and mulched.

This provides strong removal/restoration evidence.

## Fatal blockers

### 1. No final surveyed negative polygon

The public package does not provide a final as-built excavation boundary or final coordinate table for the former residential yard and driveway.

The excavation drawing is a design/construction plan, not a final surveyed empty-area polygon. The 23 sample locations are described as an approximate 50-foot grid, but their final coordinates are not published.

An analyst-drawn boundary from the planning sheet would not satisfy the geometry gate.

### 2. No defensible WGS84 conversion

The cap as-built drawings use a local station grid. The public drawings do not state a horizontal datum or publish survey control coordinates that can be converted directly to WGS84.

The property boundary and several site features are explicitly labelled approximate. Georeferencing only from roads, structures or aerial imagery would create analyst-derived geometry rather than authoritative final survey geometry.

### 3. No numerical uncertainty

The report does not state:

- horizontal survey accuracy;
- vertical survey accuracy;
- a boundary tolerance;
- a numerical uncertainty for the probe-based cover measurements.

The 36-inch value is a verified construction minimum, not a surveyed exact depth with reported uncertainty.

### 4. Final surface equivalence is incomplete

Both candidate areas received soil/vegetation restoration, which is encouraging. However:

- the cap has a documented minimum 6-inch topsoil layer;
- the former yard's restored topsoil thickness is not stated;
- the report does not explicitly certify that both areas received the same complete final surface assembly.

### 5. Clean 20 m negative support is not confirmed

The possible negative area is constrained by the access road, workshop, former house area, woods and cap edge. Without a final surveyed excavation polygon, a clean interior wider than 20 m cannot be confirmed after margins.

## Calibration decision

```text
positive depth evidence = strong minimum-thickness evidence
confirmed removal/restoration = yes
same radar-facing surface = partial, not proven identical
exact positive survey geometry = local-grid only
exact negative survey geometry = no
numerical uncertainty = no
clean 20 m negative footprint = not confirmed
calibration row created = no
earth_engine_query_executed = no
app_depth_enabled = no
```

Final decision:

```text
HOLD_NEGATIVE_GEOMETRY_AND_NUMERICAL_UNCERTAINTY_NOT_PUBLIC
```

## Source reviewed

- EPA SEMS document 313667, *Final Engineering Report, Dixie Auto Salvage Site, Danville, Illinois*.
- Report pages 4-13: completed excavation, restoration and final-cover construction.
- Drawing pages 18-24: excavation, subgrade and final grading plans.
- Construction reporting pages 68 and 77-80: yard excavation, grade stakes, topsoil and site-wide seeding/restoration.
- Survey drawing pages 204-205: as-built top of geomembrane and as-built topsoil layer.

Temporary extraction PR #11 was used only to recover and render the report. It should remain unmerged and be closed.

## Next step

Move to another large completed site that publishes all of the following together:

1. a final surveyed shallow/deep or positive/negative boundary;
2. actual measured depth values with numerical uncertainty;
3. the same final surface assembly;
4. clean interiors wider than 20 m;
5. a stable Sentinel-1-era observation period.
