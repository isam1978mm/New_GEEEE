# Syncrude 1990 tailings-capping depth screen result

## Decision

**NOT GOOD TO GO**

This is one of the strongest measured-depth near-misses found so far. It contains large replicated plots and real post-construction thickness measurements, but the public record still cannot support a calibration row under the locked rules.

## What the primary report proves

- Four cover treatments were constructed in 1990.
- Three treatments used replaced soil from the same fair-quality source at nominal depths of 30, 50 and 70 cm.
- Each treatment was replicated in three blocks.
- Each plot measured approximately **60 m × 60 m**.
- Four species subplots occupied approximately 50 m × 50 m inside each plot, leaving approximately 5 m perimeter buffers.
- All plots contained the same four planted species: jack pine, white spruce, aspen and dogwood.
- Cap thickness was measured by band augering to the tailings-sand base.
- **Fifty measurements were taken per plot.**
- Mean measured thicknesses for the fair-source treatments were approximately:
  - 80 cm for the nominal 70 cm treatment;
  - 58 cm for the nominal 50 cm treatment;
  - 39 cm for the nominal 30 cm treatment.
- The report states that the three fair-source treatment means were statistically different.

## Fatal blockers

### 1. Numerical depth uncertainty is not published

The report does not provide:

- confidence intervals for the cap-thickness means;
- standard errors or standard deviations for the treatment depths;
- construction or measurement tolerance;
- the raw 50-point measurement table for each plot.

A chart of block means and a statement of statistical significance are not enough to populate the required numerical uncertainty field honestly.

### 2. The plots are not geographically coordinate-tied

The report provides a local engineering layout with plot and block dimensions. It locates the experiment generally on the Cell 5 tailings-pond toe berm, but it does not publish:

- surveyed geographic plot-corner coordinates;
- northing/easting values;
- a benchmark or survey-control table;
- a georeferenced GIS or CAD file.

The exact 60 m × 60 m plots therefore cannot be transferred to modern imagery without speculative georeferencing.

### 3. Radar-facing surface conditions were not uniform

The report states that peat and mineral material were not uniformly mixed during stripping and placement. Large portions of plots contained little or no peat, and herbaceous cover varied strongly according to near-surface peat distribution.

Although the fair-source treatments came from the same source area and used the same planted species, the actual upper soil and vegetation conditions were not demonstrated to be equivalent broad surfaces.

### 4. No stable Sentinel-1 period is proven

The report follows the plots through 1993, and a later secondary review mentions vegetation observations in 1996. No public record was found proving that:

- the exact plots remained identifiable after 2014;
- their boundaries were preserved;
- they avoided later earthworks, operational changes or redevelopment;
- one unchanged Sentinel-1 observation period exists.

The original report also records initial wind deposition, one locally ponded construction area, and a small erosion gully on one plot.

## Gate result

```text
two large exact final measured depth zones = yes
coordinate-tied measured depth geometry = no
matching upper soil and vegetation = no
numerical depth uncertainty = no
30-40 m clean interior for each = possible by dimensions, but not geographically locatable
stable Sentinel-1 period for exact zones = no
```

## Recovery record

```text
Temporary PR: #31
Initial workflow run: 30366891572
Scholaris API recovery run: 30367136391
Artifact ID: 8691273127
Merge: no
```

## Current app status

```text
Usable calibration rows: 0
Numerical depth ready: No
App depth enabled: No
Earth Engine query executed: No
Training started: No
Plan changed: No
```

## Next action

Continue the approved search for a completed large vegetated depth experiment whose public record adds numerical depth uncertainty, surveyed geographic polygons and a documented unchanged Sentinel-1 period to comparably strong measured thickness evidence.
