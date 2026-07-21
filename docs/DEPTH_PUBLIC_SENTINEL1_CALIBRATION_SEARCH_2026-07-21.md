# Public Sentinel-1 Buried-Depth Calibration Search — 2026-07-21

Status: focused public search completed for datasets pairing Sentinel-1 observations with independently known buried-object depths. No suitable matched calibration dataset was found. App depth remains disabled.

## Search question

The search targeted a package containing all or most of:

```text
Sentinel-1 GRD or SLC observations
independently measured buried-object depth
traceable depth reference such as depth to top
known installation or survey dates
multiple independent physical sites
confirmed negative or empty-site records
public licence and acquisition mapping
```

## Search result

No public dataset was found that directly pairs Sentinel-1 backscatter with independently measured buried-object depths.

The public results separated into unrelated categories:

1. generic Sentinel-1 GRD, SLC, interferogram, terrain-corrected, and displacement products without buried-target truth;
2. Sentinel-1 datasets for surface subsidence, flooding, wind, land cover, bathymetry, ships, or above-ground infrastructure;
3. buried-pipe engineering datasets without matched satellite observations;
4. GPR and ground-method datasets with physical depth truth but target dimensions far below defensible Sentinel-1 resolution;
5. SAR method and despeckling datasets whose labels do not represent independently verified buried depth.

## Important scientific boundary

Public GPR depth truth cannot be silently converted into Sentinel-1 depth labels.

For direct Sentinel-1 calibration, each retained physical unit would need a defensible satellite-scale footprint and a sensor acquisition relationship to the known subsurface state. Compact pipes, drums, buckets, cables, trenches, and utility cross-sections do not create independent target-level Sentinel-1 samples merely because Sentinel-1 images exist over the location.

The current supported unit remains:

```text
physical_site_or_large_isolated_section
```

A usable record would require a large enough isolated site change, known subsurface geometry or depth, traceable before/after or state timing, and an independently reviewed background or negative case.

## Netherlands trial-trench dataset scale decision

The Netherlands dataset documented in `DEPTH_PUBLIC_CANDIDATE_NETHERLANDS_TRIAL_TRENCH_GPR_2026-07-21.md` is the strongest public ground-method candidate found in this pass because it includes:

- thirteen construction projects;
- 125 activities;
- 959 raw SEG-Y radargrams;
- trial-trench physical verification;
- potential excavated free-subsoil controls.

However, it is not approved for direct Sentinel-1 depth calibration because:

- individual utilities are sub-pixel or mixed-pixel targets at Sentinel-1 scale;
- the utilities were not documented as newly installed during the 2020–2021 GPR observation period;
- the public ground-truth georeferencing is withheld;
- no matched Sentinel-1 acquisition contract is provided;
- numerical depth and uncertainty still require per-activity extraction.

It may support GPR method validation, evidence-method research, and negative-control policy development, but not target-level app depth training.

## Generic Sentinel-1 products screened out

Public Sentinel-1 sources provide excellent sensor data but no buried-depth labels, including:

- Copernicus Sentinel-1 GRD and SLC archives;
- NASA/JPL OPERA radiometric-terrain-corrected backscatter;
- NASA/JPL OPERA surface-displacement products;
- ARIA Sentinel-1 interferograms;
- public Sentinel-1 despeckling and classification datasets.

These sources can supply observations only after a legitimate physical calibration site is identified. They cannot create the missing labels.

## Current classification

```text
public_matched_sentinel1_buried_depth_dataset = not_found
public_ground_method_depth_candidates = found
public_direct_app_calibration_records = 0
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
training_started = false
app_depth_enabled = false
```

## Next public-only search direction

The remaining public-only search should focus on uncommon large-area cases rather than more compact GPR test pits:

1. controlled civil-engineering sites with large isolated buried structures;
2. documented construction or remediation sites with known subsurface depth and exact dates;
3. large void, tunnel, mine, landfill-cell, or engineered subsurface sections with independent as-built records;
4. public before/after remote-sensing studies where the physical state is independently documented;
5. public empty or unchanged control sites matched to the same sensor and time period.

No user survey, review, outreach, or field work is required. Source-owner contact remains disabled unless the user explicitly changes that rule.
