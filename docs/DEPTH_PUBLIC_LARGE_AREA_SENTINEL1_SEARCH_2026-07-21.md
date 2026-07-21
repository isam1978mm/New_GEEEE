# Public Large-Area Sentinel-1 Calibration Search — 2026-07-21

Status: public-only search continued. No contact, survey, fieldwork, calibration import, training, or app-depth enablement occurred.

## Search objective

Find public sources that combine independently documented buried depth with a large enough footprint, construction timing, and Sentinel-1 observations to support the current private depth-research contract.

## Public infrastructure inventories screened

The search found public inventories for:

- pipelines;
- drainage and structural culverts;
- railway and roadway tunnels;
- municipal sewer and utility networks;
- rural gas-distribution as-built geometry;
- underground-utility survey extents.

Typical available attributes include location, asset type, diameter, material, status, year built, invert elevation, or survey extent.

Typical missing fields include:

```text
exact depth to target top
numerical reference uncertainty
verified empty-ground controls
precise installation interval
matched pre/post Sentinel-1 acquisition contract
independent site-group split metadata
```

Decision:

```text
supporting_context_usable = yes_for_selected_sources
known_depth_calibration_usable = no
confirmed_negative_usable = no
```

Absence from a public infrastructure map must not be interpreted as confirmed empty ground.

## Sentinel-1 archaeology evidence screened

A published Qubbet el-Hawa study uses Sentinel-1 and Sentinel-2 to examine an archaeological site. It reports radar sensitivity to exposed structures, excavation/erosion disturbance, and some shallow subsurface structure patterns under arid conditions.

Qualification:

```text
sentinel_1_subsurface_or_disturbance_relevance = yes_exploratory
independent_numeric_depth_labels = not_available
multiple_known_depth_physical_sites = no
confirmed_negative_sites = no
calibration_import = prohibited
```

The study supports the limited statement that Sentinel-1 backscatter may respond to surface or near-surface disturbance and context. It does not validate numerical buried-depth estimation.

## OpenTrench3D confirmation

OpenTrench3D remains useful excavation truth across seven areas, but records open trenches rather than buried-state Sentinel-1 observations.

```text
physical_geometry_truth = strong
buried_state_truth = no
sentinel_1_match = no
app_depth_calibration = no
```

## Current public-search result

No public source was found that satisfies the complete contract:

```text
independent depth-to-top truth
+ numerical uncertainty
+ multiple independent physical sites
+ confirmed negatives
+ exact construction/acquisition timing
+ supportable Sentinel-1 footprint
+ public reuse terms
```

## Current project boundary

```text
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
numerical_depth_status = not_available
app_depth_enabled = false
```

## Next public-only search direction

1. inspect public sewer datasets where surface elevation, invert elevation, and pipe diameter may permit a source-defined top-of-pipe depth calculation;
2. require explicit vertical datum and uncertainty before any derived depth is considered;
3. search public construction-project archives for exact installation windows and as-built cross-sections;
4. continue screening large-area controlled disturbance sites;
5. keep all ground-method and Sentinel-1 evidence roles separate.
