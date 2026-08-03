# Measured elevation change — operator guide

Status: implemented, default-off, not wired into the automatic pipeline.

## What this is

A way to get a depth in metres without a site visit, a records request, or
contact with any organisation.

When material is placed on the ground, the ground gets higher. Public elevation
data has already measured the height of the ground, repeatedly, over many years.
Subtract an old surface from a new one and the difference is the thickness of
what was placed.

That is a measurement, not a model. It has no fitted parameters, so it needs no
calibration records at all.

## Why it exists

The depth workstream was blocked on ground truth. The engine at
`app/pipeline/depth/interpolation.py` has always worked, but it needs at least
two polygons whose real depth is known, and the only routes to those polygons
were an operator's survey records or an agency records request.

The public-literature search screened around forty sites and ended at
`usable_global_calibration_rows = 0`, mostly because papers report design
thickness rather than measured, without numerical uncertainty, and without
coordinate-controlled polygons.

The repository had 139 mentions of `dem`, three of `lidar`, and none of `icesat`
or `gedi`. The project had searched exhaustively for depth *written down in
documents* and had not looked for depth *measured by machines*.

## What it measures, and what it does not

| Measures | Does not measure |
|---|---|
| Thickness of material placed between two elevation epochs | Depth to a buried object at undisturbed ground |
| Thickness of material removed (reported separately, never as depth) | Anything that changed outside the two epochs |

This distinction is enforced in code, not just documented. The summary carries
`measures: placed_material_thickness` and
`does_not_measure: depth_to_a_buried_object`, and removal is flagged with
`material_removed_not_added` rather than returned as a depth.

## What it can and cannot see

Selection is by expected vertical noise, not by epoch separation: a long
baseline is worthless if neither surface can resolve the cover.

| Coverage | Pair chosen | Thinnest cover it can see |
|---|---|---|
| United States | Two `USGS/3DEP/1m` lidar vintages | **0.28 m** |
| Global | NASADEM (2000) against Copernicus GLO-30 | **7.07 m** |

The United States tier works for the 0.6–1.0 m covers this project cares about.
The global tier does not, and says so: requesting a 0.7 m target globally
returns `target_thickness_below_detection_floor` rather than a confident number.

Two overlapping lidar vintages are not guaranteed at any given location. The
catalogue cannot know that, so a same-source pair always carries
`requires_two_overlapping_vintages_at_this_location`. Only a live footprint
query can confirm it.

## Running it

Measurement only:

```bash
python scripts/measure_elevation_depth_for_existing_run.py \
  --run-dir ./data/runs/<run_id> \
  --coverage united_states \
  --target-thickness-m 0.7
```

Also drive the existing local-depth engine with the measured zones:

```bash
python scripts/measure_elevation_depth_for_existing_run.py \
  --run-dir ./data/runs/<run_id> \
  --drive-depth-engine
```

Without Earth Engine credentials, supply two GeoTIFFs already on the run grid:

```bash
python scripts/measure_elevation_depth_for_existing_run.py \
  --run-dir ./data/runs/<run_id> \
  --offline-early ./early.tif \
  --offline-late ./late.tif
```

The run must already have completed its grid stage, so that
`grid_manifest.json` exists and both epochs land on the same locked grid as the
run's other rasters.

## Outputs

All under `<run_dir>/elevation_change/`, all `FILESYSTEM_ONLY` and never
HTTP-servable. The zone file carries real polygon coordinates and the raster
carries the site's elevation surface.

| File | Contents |
|---|---|
| `elevation_change_m.tif` | Co-registered thickness in metres, on the run grid |
| `measured_zones.geojson` | Reviewed anchor and candidate zones |
| `elevation_change_summary.json` | Source pair, co-registration evidence, per-zone measurements, warnings |

## How the measurement works

1. **Fetch two epochs** on the run's locked grid, using the same tiling as the
   DEM stage, so both surfaces and the run's radar rasters are co-located by
   construction.
2. **Remove the vertical datum offset.** Two surfaces years apart rarely share a
   datum; a metre of constant bias is ordinary. The offset is the median
   difference over ground unlikely to have changed — low slope, and within three
   robust deviations of the median. This is iterated, because the stable-ground
   selection and the offset estimate depend on each other.
3. **Take the residual spread as the noise floor.** The NMAD of the difference
   over that same stable ground is the honest accuracy of this particular pair,
   and every downstream interval derives from it. It usually exceeds the
   published nominal accuracy of either product.
4. **Measure per area, allowing for correlated error.** Neighbouring DEM pixels
   are wrong in the same direction, so averaging a thousand of them does not
   reduce the error thirtyfold. The spatially-correlated treatment (Rolstad et
   al. 2009) is used instead. Treating pixels as independent would understate
   intervals by an order of magnitude.
5. **Abstain when change is within the noise floor.** No metre values are
   emitted for ground that cannot be shown to have changed.

## How the zones are derived

The measurement draws its own boundaries. Where material was placed the ground
rose, so the raised ground *is* the outline and its height *is* the depth. No
surveyed polygon is required.

Zone geometry is the largest axis-aligned rectangle inscribed inside a measured
region, not a traced outline of it. A traced outline hugs the edge of the
change, where co-registration error, mixed pixels and construction batter are
worst, and can produce self-touching rings that nothing downstream validates
for. Losing area at the margin is the right trade against a boundary that
quietly contaminates the number.

The generated file matches the schema the browser preflight and
`scripts/extract_operator_depth_signals.py` already accept. Nothing in the depth
engine changed; a test asserts that `interpolation.py` contains no reference to
this work.

## The withheld validation zone

By default the zone nearest the middle of the measured depth range becomes the
candidate, and its measured depth is kept out of the anchor set. Predicting a
zone whose true depth is known, from anchors that never saw it, is the only
self-check available without external truth.

The middle zone is chosen deliberately. The engine abstains rather than
extrapolate, so withholding an extreme zone would guarantee an abstention and
prove nothing.

The withheld measurement travels under `withheld_measured_depth_*` property
names, deliberately unlike the anchor depth fields, so no consumer can mistake
it for a supplied depth and quietly calibrate on it.

## Honest limits

**This does not repeal the physics of the radar route.** Sentinel-1 C-band
penetrates centimetres of moist soil, not metres. Measured anchors make the
radar-to-depth model *trainable* for the first time; they do not make it
*correct*. Keep the preregistration and holdout gates in
`docs/DEPTH_VALIDATION_GATES_SPEC.md`. If the radar model fails its holdout, that
is a real result — and the measured thickness still stands on its own.

**Tyrone is not a validation site for this.** The measured depths at Test Plots
5 and 6 are documented, but official coordinate-controlled plot geometry was
never recovered, and
`docs/DEPTH_LOCAL_MVP_TYRONE_MULTI_PLACEMENT_SENSITIVITY_RESULT_2026-07-29.md:43`
records `ordering_inconsistent` from 36 plausible placements. Measuring
elevation change over the wrong ground gives a wrong answer regardless of
instrument quality.

**Two zones are not a model.** A single AOI with a withheld zone is a self-check,
not evidence of transferability. Multiple independent sites, split by site with
an untouched holdout, remain required before any transferable claim.

## Validation status

| Check | Status |
|---|---|
| Recovers a known synthetic datum offset | Passing |
| Recovers the pair noise floor | Passing |
| Recovers known cover thicknesses | Passing, within 6 mm on a synthetic scene |
| Abstains on undisturbed ground | Passing |
| Reports removal separately from depth | Passing |
| Generated zones satisfy every preflight rule | Passing |
| Generated zones drive the unmodified engine | Passing |
| Runs against live Earth Engine | **Passing** — verified on real runs |
| Refuses a pair that shares data | **Passing** — refused two real pairs |
| Produces a trustworthy noise floor on real data | **Passing** — see below |

## What the first live runs established

Ten real runs were screened. Nine had genuinely independent global sources; one
did not, and it happened to be the first one tried.

**The contaminated site.** Copernicus GLO-30's Filling Mask showed no pixel over
that area was measured by TanDEM-X at all: 38.8% filled from one source, 61.0%
from another. 37.7% of its difference against NASADEM was exactly zero, because
the fill is SRTM and NASADEM is SRTM. ALOS was worse at 44.1%, since it fills
from SRTM too. The pair reported a 0.41 m noise floor, a vertical offset of
exactly 0.000 m, and nine zones. All of it was an artefact of differencing SRTM
against itself. This is what the shared-data guard now refuses.

**A clean site.** NASADEM against Copernicus, 0.0% shared:

```text
vertical offset removed          = -0.80 m      (real, not zero)
measured noise floor sigma       =  2.67 m
measured detection floor         =  5.23 m
zones found                      =  0
status                           =  no_measurable_change
```

That is the method working. A non-zero datum offset and a physically plausible
noise floor are what two independent 30 m products should produce, and the
correct answer at that site is that nothing moved by more than about 5 m between
2000 and 2013.

**The practical ceiling for global sources.** A measured detection floor of
around 5 m is the realistic best case for 30 m public DEMs. Large earthworks are
in reach: landfill cell construction, quarry cut and fill, dam works. Soil covers
of 0.6-1.0 m are not, and no processing changes that.

Sub-metre work requires US lidar, and US lidar is only available in the United
States. Outside it, the free elevation record cannot resolve a soil cover.

## Not yet done

- Not wired into the orchestrator. That needs a settings gate and a decision
  about Earth Engine quota on every run.
- No UI. The operator panel at
  `frontend-v2/src/app/components/OperatorLocalDepthPanel.tsx` is still the
  two-line stub left by commit `72ddb05`.
- Asset identifiers in `app/pipeline/elevation_change/sources.py` are unverified
  against the live Earth Engine catalogue, since this work was done without
  credentials. An unavailable asset surfaces as an explicit failure rather than
  a silent substitution.
