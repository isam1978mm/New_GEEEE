# Depth Public-Only Infrastructure Search — 2026-07-21

Status: public-only search advanced; no calibration record approved and app depth remains disabled.

This note continues the depth-evidence search without asking the user to conduct surveys, contact source owners, review papers, or perform research. Only openly accessible public sources were screened.

## Current decision

```text
public_search_status = major_infrastructure_classes_screened
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

The search found stronger public provenance and date fields, but still did not find a source that combines independently measured depth-to-top, numerical uncertainty, multiple independent physical sites, confirmed negatives, exact construction dates, and defensible Sentinel-1-scale support.

## Candidate class A — Connecticut underground storage tanks

Primary public sources:

- Connecticut Open Data dataset `utni-rddb`
- Socrata API Foundry documentation for `utni-rddb`

Verified public fields include:

- facility identifier, name, address, city, and ZIP;
- tank identifier and status;
- estimated tank capacity;
- stored substance;
- last-used date and closure type;
- tank and piping construction type;
- notified installation date;
- tank latitude and longitude;
- public-domain licence.

The dataset contains approximately 45,000 historical and current commercial tanks and is updated weekly. The public documentation explicitly warns that records may be incomplete or contain notification and data-entry errors.

Current classification:

```text
independent_asset_registry = yes
installation_date = yes
coordinates = yes
capacity_and_material = yes
site_specific_depth_to_top = no
reference_uncertainty = no
exact_footprint_or_orientation = no
confirmed_negative = no
sentinel_1_scale_support = not_demonstrated
private_pack_import_approved = no
```

Use rule:

This source may support public construction-date screening or facility-level disturbance research. Tank capacity must not be converted into burial depth, and generic regulatory cover requirements must not be substituted for site-specific depth truth.

## Candidate class B — large tunnel projects

Public project sources screened include:

- Canada Line tunnel construction records;
- Crossrail Learning Legacy records;
- LA Metro tunnel guidance;
- Ontario Line public construction records.

Verified examples include:

- Canada Line tunnel depth generally reported as 10–30 m from surface to tunnel top, with tunnel-boring dates in 2006–2008;
- Crossrail land/property workflows using tunnel depth Z-values and a 9 m subsoil-rights threshold;
- LA Metro reporting that most tunnels are approximately 50–70 ft underground and twin-bore tunnels are generally about 20 ft in diameter;
- Ontario Line documentation reporting a 16 m launch shaft and tunnels operating as deep as approximately 40 m, with tunnelling beginning in 2026.

Current classification:

```text
satellite_scale_structure = yes
construction_period = public_for_some_projects
public_depth_range = yes
exact_segment_depth_table = not_recovered
survey_uncertainty = not_recovered
matched_neutral_sentinel_1_unit = not_defined
shallow_depth_domain_match = no
private_pack_import_approved = no
```

Use rule:

These projects are physically large enough for satellite-scale change research, but public pages mostly provide project-level ranges rather than survey-grade segment depths. Their 10–40 m depth range also does not match the current shallow 0.5–3 m candidate domain. Any Sentinel-1 response would likely reflect construction disturbance or surface deformation rather than direct depth sensitivity.

## Candidate class C — 2026 purpose-built tunnel GPR dataset

Primary public sources:

- arXiv `2607.04882`
- public code repository referenced by the paper
- public Kaggle dataset referenced by the paper

Verified public facts:

- a purpose-built field site contains three buried tunnels at 1.5–3 m depth;
- anomaly-free radargrams were used as normal/background data;
- the study reports 1,600 field test windows across 55 survey lines;
- code and a public dataset are referenced by the publication.

Current classification:

```text
known_depth_positive = promising_for_gpr_method_research
same_site_normal_background = yes
independent_physical_sites = no_single_site
reference_uncertainty = not_recovered
satellite_scale_support = not_demonstrated
sentinel_1_data = no
private_pack_import_approved = no
```

Use rule:

This is a useful public GPR detection and background dataset. It must remain one physical-site group and must not be converted into multiple independent holdout sites or Sentinel-1 depth labels.

## Candidate class D — landfills and landfill cells

Public sources screened include:

- Ontario landfill inventory;
- Ontario historical large-landfill dataset;
- Ontario landfill-gas reporting data;
- UK authorised and historic landfill boundaries;
- US EPA LMOP landfill technical data.

Verified public fields across these sources include:

- facility coordinates or boundaries;
- operational status;
- opening and closure years for some sources;
- approved volume, design capacity, fill rates, or waste-in-place for some sources;
- public engineering-design or monitoring descriptors in historical inventories.

Current classification:

```text
satellite_scale_area = yes
public_site_boundaries = yes_for_some_sources
opening_or_closure_year = yes_for_some_sources
cell_level_depth_to_top = no
cell_construction_date = not_consistently_available
numerical_depth_uncertainty = no
confirmed_empty_cell_holdout = no
private_pack_import_approved = no
```

Use rule:

Landfill inventories may support large-area change or confounder research, but site volume, capacity, or waste-in-place must not be treated as burial depth. Without cell-level as-built elevations and dates, these sources cannot enter the depth-calibration pack.

## Public-only search boundary reached

The major plausible public classes have now been screened:

1. controlled GPR test sites;
2. trial-trench and open-trench utility datasets;
3. municipal sewer and as-built depth schemas;
4. underground storage-tank registries;
5. large tunnel projects;
6. landfill and large buried-infrastructure inventories;
7. Sentinel-1 archaeology and construction-change studies.

The recurring missing combination is:

```text
exact depth_to_top
+ numerical reference uncertainty
+ independently confirmed positive and negative records
+ several independent physical sites
+ exact construction or acquisition dates
+ defensible Sentinel-1-scale analysis units
```

## Current scientific boundary

```text
public_ground_method_truth = available
public_engineering_depth_context = available
public_large_area_construction_context = available
public_sentinel_1_buried_depth_calibration = not_found
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
training_status = blocked
app_depth_enabled = false
```

## Next internal work

The next work should remain repository-side and public-only:

1. consolidate all screened candidates into a machine-readable eligibility matrix;
2. encode explicit rejection reasons for depth, uncertainty, scale, date, and split eligibility;
3. prevent method-only and context-only datasets from entering the calibration pack;
4. identify whether any already-public source has enough information for a whole-site exploratory Sentinel-1 screen without claiming depth;
5. keep numerical and relative depth disabled until the calibration contract is actually satisfied.
