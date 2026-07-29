# Option 1 Aurora Soil Capping Study decisive result — 2026-07-29

## Decision

**NOT GOOD TO GO for numerical-depth calibration from the recovered public record.**

Aurora remains a valuable large-scale reclamation experiment, but the recovered sources do not provide the strict ground-truth package required by Option 1.

This work is classified as **Option 1 — Global Numerical Depth evidence research**. It does not activate Option 3.

## Sources inspected

1. Alam, Barbour and Huang (2020), *Characterizing uncertainty in the hydraulic parameters of oil sands mine reclamation covers and its influence on water balance predictions*, HESS 24, 735–759, DOI `10.5194/hess-24-735-2020`.
2. Korbas (2013), *Degradation and Mobility of Petroleum Hydrocarbons in an Oil Sands Waste at Aurora Fort Hills Disposal Area*, University of Saskatchewan thesis.
3. The recovered PR #41 artifact `aurora-cover-study-records`, including extracted text, the HESS treatment-layout figure and the Korbas Appendix A site plan.

Recovered-file hashes:

```text
aurora_hess_2020.pdf = e65ff750becd47700e14568bfa4c0b71193c4a3e9050a4af6a46d1d2f059a61b
aurora_korbas_thesis_2013.pdf = 3d8b470daa301ad4fe91ea606d1e46b29f9499d9721d4dedc6fbbfc8f534e25c
```

## What was proven

- The Aurora Soil Capping Study contains 12 alternate cover designs replicated in triplicate, producing 36 treatment cells.
- Each treatment cell is approximately one hectare.
- The treatment covers were constructed in 2012 over lean oil sands overburden.
- The public treatment figure identifies peat or LFH surface layers, multiple subsoil materials and several nominal layer thicknesses.
- Some nominal designs are potentially useful for a shallow/deep documentary comparison. The strongest example is the contrast between a 30 cm peat-only cover over overburden and a 30 cm peat plus 120 cm subsoil profile.
- Each treatment cell had a point monitoring location with water-content, temperature and suction sensors at several depths.
- Monitoring data used in the HESS paper cover 2013–2016.

## Decisive failures

### 1. Final measured as-built depth is missing

The recovered sources describe the treatment **designs** and model domains. They do not publish a panel-by-panel or polygon-level table of final surveyed constructed thicknesses.

No recovered source states final measured values such as:

```text
cell polygon X final thickness = value ± uncertainty
cell polygon Y final thickness = value ± uncertainty
```

Point sensors installed at several depths are monitoring instruments. They are not proof that a nominal design thickness was achieved uniformly across an entire one-hectare polygon.

### 2. Numerical construction uncertainty is missing

The HESS paper quantifies uncertainty in hydraulic model parameters and water-balance predictions. That is not construction-thickness uncertainty.

The recovered sources do not publish:

- thickness tolerance;
- survey accuracy;
- confidence interval for final constructed depth;
- cell-level standard deviation of constructed thickness;
- construction-quality acceptance range tied to each polygon.

### 3. Exact coordinate-tied treatment polygons are missing

The HESS treatment map shows the relative arrangement of the 36 cells and treatment numbers, but it does not provide surveyed corners, northing/easting coordinates, a coordinate reference system, CAD/GIS geometry or a georeferenced treatment-polygon file.

Korbas Appendix A provides a local site plan with a scale and gas-sampling locations. It does not provide final coordinate-tied treatment polygons. It was prepared for gas-flux work and cannot replace a final as-built treatment survey.

A site centre coordinate or broad mine location is insufficient for assigning exact depth values to Sentinel-1 interiors.

### 4. Surface and landscape comparability are not controlled tightly enough

The 36 cells were randomly placed across a watershed. The paper expressly discusses spatial variation associated with construction/placement conditions, topography and vegetation establishment.

The treatment designs also change several properties:

- peat versus LFH surface material;
- surface-layer thickness;
- selected subsoil versus blended B/C or Bm material;
- total cover thickness;
- root depth and vegetation response.

The strongest nominal shallow/deep comparison shares a 30 cm peat surface, but the available record still does not prove equal slope, aspect, roughness, drainage, vegetation, maintenance history and final measured thickness across a clean radar interior.

### 5. Stable Sentinel-1 period is not proven

The site began bare and developed vegetation during the early monitoring years. Vegetation density and species differed by treatment material. The public record reviewed here does not identify a plot-specific, repair-free and surface-stable Sentinel-1 observation period for a matched pair.

## Gate result

| Gate | Aurora result |
|---|---|
| Full-scale clean zones | Potentially yes; one-hectare cells |
| Different nominal depths | Yes |
| Final measured numerical depths | **No** |
| Numerical depth uncertainty | **No** |
| Coordinate-tied polygons | **No** |
| Matched radar-facing surfaces | Not proven |
| Stable Sentinel-1 period | Not proven |
| Confirmed control for Option 4 | No |

## Final state

```text
candidate = Aurora Soil Capping Study
strategy_classification = Option 1 evidence research
documentary_gate = failed
failure_type = public_as_built_record_missing
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

Do not reopen Aurora merely because the experiment is large or replicated.

Reopen only if a concrete official package becomes available containing:

1. final surveyed thickness for each treatment cell or defensible polygon-level measured depth statistics;
2. numerical construction tolerance or survey uncertainty;
3. coordinate-tied CAD/GIS/as-built treatment polygons;
4. a documented matched pair with comparable surface, slope, aspect, drainage, vegetation and maintenance;
5. a plot-specific stable Sentinel-1 period.

## Next Option 1 action

Continue the targeted evidence search with the next strongest existing candidate, prioritizing official construction-quality and as-built packages over design or performance papers. Aitik WRD6 is the next targeted route unless a new Tyrone agency response supplies stronger official ground truth first.
