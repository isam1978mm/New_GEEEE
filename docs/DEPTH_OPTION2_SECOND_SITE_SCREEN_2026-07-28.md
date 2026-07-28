# Option 2 — second-site ordering screen — 2026-07-28

## Decision

**NOT GOOD TO GO FOR A SECOND RADAR TEST**

`Option 2 — Ordering Test` remains the selected strategy, but no second site from the current candidate set is execution-ready.

The Rocky Mountain Arsenal test already returned `ordering_inconsistent`. A new site was therefore screened before any further Earth Engine query. Every available candidate failed the cheap geometry, surface-matching, or stability screen.

## Candidates screened

- **Aitik:** matching 1.0 m and 1.5 m protective-layer designs and long monitoring, but no public trial-corner coordinates or map that identifies the two exact plateaus.
- **NAS Alameda Site 2:** measured grid exists, but the strongest deeper band follows drainage and monitoring infrastructure, so thickness cannot be isolated.
- **Mount Morgan:** plots are only about 30 m wide before excluding edges, slope breaks, collectors, and instruments.
- **Mt Whaleback:** large 2 m and 4 m plots, but intentionally unvegetated rough surfaces inside an active mine.
- **Century:** large cells, but the compared cells use the same total cover thickness.
- **Cannington:** treatment cells are too narrow after exclusions and change barrier/layer design, not thickness alone.
- **Kidston:** one uniform 2 m cover, not a shallow/deep pair.
- **Mt Leyshon:** variable thickness is not divided into two mapped comparable zones and surface conditions differ.
- **Cadia:** the alternative design changes the liner system, so thickness is not the only difference.
- **Kestrel:** covered waste versus uncovered waste, not shallow versus deep.
- **South Bison Hill:** strongest remaining near-miss, but exact D1 and D3 strip geometry is not publicly coordinate-tied.

## Strongest remaining near-miss: South Bison Hill

The public record proves three adjacent approximately one-hectare, 50 m by 200 m vegetated plots constructed in 1999:

- D1: nominal 50 cm total cover;
- D2: nominal 35 cm total cover;
- D3: nominal 100 cm total cover.

D1 and D3 are the most promising pair because both prescribe a 20 cm peat/glacial surface layer over different subsoil thicknesses.

However, an honest radar test still cannot run because the public record does not provide:

- surveyed D1 and D3 plot-corner coordinates;
- a georeferenced GIS or CAD plot file;
- an exact map of clean interiors after excluding neutron tubes, midslope stations, interflow collectors, runoff swales, and weirs;
- proof that the exact proposed interiors remained unchanged during the selected Sentinel-1 period.

The published general South Bison Hill coordinate is not enough to reconstruct the three strip boundaries. Drawing the strips from appearance alone would invent geometry.

The D3 surface also contained unintended secondary-material inclusions and initially different vegetation, which weakens the matched-surface assumption even if geometry is later recovered.

## Execution decision

```text
second_site_selected = no
second_earth_engine_query_executed = no
radar_values_inspected = no
calibration_row_created = no
training_started = no
app_depth_enabled = no
numerical_depth_ready = no
```

No second radar test should run from the current candidate set.

## Exact evidence that would reopen South Bison Hill

Reopen only if one of the following is recovered:

1. surveyed D1/D2/D3 corner coordinates;
2. a georeferenced GIS, CAD, or survey plan showing the plot boundaries;
3. the map and appendices from the 2012 field survey referenced by the 2013 *South Bison Hill Soil Capping Research Synthesis*;
4. a later official map preserving the D1 and D3 boundaries and identifying post-2014 repairs or disturbances.

After geometry is recovered, the clean-interior and matched-surface checks must pass before preregistering a new radar protocol.

## Current strategy status

```text
Option 2 strategy = active but blocked
RMA test = closed, ordering inconsistent
second executable site = none
Option 3 = on hold pending EMNRD request N000019-070026
```

## Next action

Do not broaden into random sites or weaken the ordering-test rules. The next defensible action is either:

- recover the exact South Bison Hill D1/D3 survey geometry; or
- wait for the Tyrone Dam 3X response under Option 3.
