# BDM Warren Steel pond-closure result - 2026-07-27

## Decision

**NOT GOOD TO GO**

BDM Warren Steel is the strongest Ohio near-miss reviewed in this route, but it still cannot create a defensible numerical-depth calibration pair.

## Why it initially looked promising

The September 2016 closure certification documents two large, completed areas with broadly comparable visible surfaces:

- **Pond #5:** residual-bearing controlled fill placed inside the former pond, then covered with fine-grained soil, topsoil, and seeding;
- **56-inch Hot Mill Lagoon:** residuals removed to the bentonite layer, confirmatory samples accepted, then backfilled with slag, topsoil, and seeding.

Both areas are physically large enough in principle to investigate further.

## Strong positive-depth evidence at Pond #5

Appendix H contains a professional survey drawing comparing:

- the existing base surface surveyed on March 8, 2016; and
- the final clay-fill surface surveyed on March 29, 2016.

The drawing reports:

```text
surveyed area = 2.358 acres
required cover thickness = 2.5 ft
required volume = 9,511 cubic yards
reported placed volume = 10,190.25 cubic yards
```

Using the reported area and placed volume gives an area-average fine-grained thickness of approximately:

```text
2.679 ft
0.816 m
```

This is a derived area average, not a public point-by-point final thickness grid. A minimum 4-inch topsoil layer was placed above it.

## Confirmed-negative evidence at the Hot Mill Lagoon

The report states that residuals were removed down to the bentonite layer. Twelve confirmatory samples were collected, and the area was backfilled after analytical acceptance.

This is strong removal evidence.

## Fatal problems

### 1. Exact negative geometry is missing

The public general-layout drawing labels the Hot Mill Lagoon boundary as an **approximate lagoon limit**.

The closure report states that as-built drawings for waste-in-place closure were not applicable. No final surveyed boundary or final coordinate table for the restored negative area was recovered.

Therefore, an exact conservative WGS84 negative polygon cannot be created from the public package.

### 2. The positive survey is not a public execution grid

The Pond #5 survey proves that the cover was professionally measured, but it does not publish:

- a final coordinate table for the survey points;
- a pointwise thickness grid;
- stated horizontal or vertical survey uncertainty.

The reported total volume supports an area-average thickness only. It does not prove a specific 30-40 m shallow or deep sub-zone.

### 3. Near-surface construction is not identical

The visible surfaces are similar, but the shallow substrate is not:

- Pond #5 has fine-grained cover soil beneath the topsoil;
- the Hot Mill Lagoon has slag backfill beneath the topsoil.

A radar difference could therefore reflect shallow soil-versus-slag moisture and roughness rather than only the buried residual condition.

### 4. Stable Sentinel-1 timing is not established

The former steel-mill property was undergoing demolition, remediation and redevelopment during and after closure. Major industrial structures and infrastructure were immediately adjacent to the lagoon areas, and later federal removal work occurred at the abandoned facility.

The public record does not establish a clean post-closure Sentinel-1 interval in which both areas and their surroundings remained unchanged.

## Calibration decision

```text
full-scale areas = yes
same visible grass surface = broadly yes
positive professional depth survey = yes
positive pointwise thickness grid = no
confirmed removal negative = yes
exact final negative survey polygon = no
same near-surface assembly = no
stable Sentinel-1 observation period = no
calibration row created = no
Earth Engine query executed = no
app depth enabled = no
```

Final decision:

```text
NOT_GOOD_TO_GO_GEOMETRY_AND_STABILITY_FAILED
```

## Sources reviewed

- BDM Warren Steel Holdings, *Closure Certification for Warren Steel Pond #5 and 56-Inch Hot Mill Lagoon*, September 2016.
- Appendix H, Pond #5 elevation survey drawing.
- Ohio EPA public eDocument record 499754.
- U.S. EPA Warren Steel Holdings removal-action site records.
- Public redevelopment and demolition records for the former Republic/Warren Steel property.

## Next step

Continue the approved plan unchanged. The next candidate must provide:

1. a full-scale vegetated area with at least 30-40 m clean interior width;
2. final measured as-built depths tied to exact survey coordinates;
3. an exact surveyed negative or a second measured depth zone;
4. the same near-surface assembly;
5. a stable Sentinel-1 observation period.
