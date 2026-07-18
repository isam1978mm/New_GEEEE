# Depth Satellite-Scale Compatibility Screen — 2026-07-18

Status: first scale screen complete for four controlled physical-site candidates. The result changes how the sources may be used; it does not stop evidence acquisition and does not enable app depth output.

## Sensor scale used for screening

For Sentinel-1 Interferometric Wide swath Level-1 GRD High Resolution products, official product documentation gives:

```text
spatial_resolution_range_x_azimuth = approximately_20_m_x_22_m
pixel_spacing = 10_m_x_10_m
```

Pixel spacing is not the same as independent spatial resolution. Resampling to 10 m pixels does not create target separation below the approximately 20 m by 22 m resolution footprint.

## Controlled-site scale comparison

### TU1208 / IFSTTAR Nantes

```text
useful_site_length = approximately_30_m
useful_site_width = approximately_5_m
sentinel_1_target_level_separation = not_supported
site_level_aggregate_screen = possible_with_caution
```

Reason: the narrow test pit is substantially smaller than one Sentinel-1 IW GRD resolution element across its width, and many different targets and host materials are closely packed along its length. Individual pipes, drums, walls, and voids cannot be assigned separate Sentinel-1 feature vectors.

Allowed use:

- GPR method and uncertainty validation;
- whole-site or broad-section satellite sanity checks only;
- no target-level satellite depth rows.

### IAG/USP controlled test site

```text
site_size = approximately_30_m_x_50_m
sentinel_1_target_level_separation = not_supported
whole_site_or_large_section_screen = possible_with_caution
```

Reason: the site spans only a few independent Sentinel-1 resolution footprints and contains seven closely spaced target lines. Line-level and target-level satellite features would mix nearby targets, trench disturbance, surface context, and urban background.

Allowed use:

- exact target-level truth for GPR research;
- whole-site or broad-section satellite screening;
- no assumption that eight target depths create eight independent satellite samples.

Historical limitation:

The site was installed before the Sentinel-1 mission. A same-sensor Sentinel-1 pre-installation negative is therefore unavailable. Later Sentinel-1 observations can only represent the long-established post-installation site.

### Texas A&M University–Corpus Christi controlled test site

```text
site_size = approximately_50_m_x_50_m
sentinel_1_target_level_separation = not_supported
whole_site_pre_post_screen = high_priority_candidate
```

Reason: the field spans several Sentinel-1 resolution footprints, but its seven target lines still contain multiple mixed objects. Individual installed depths cannot be associated with independent Sentinel-1 pixels.

Why it remains high priority:

- the site construction occurred during the Sentinel-1 mission era;
- the official project description records a pre-installation survey and a February–March 2020 construction period;
- public Sentinel-1 acquisitions before and after construction may support a whole-site change experiment if orbit, season, moisture, and surface-disturbance controls can be matched.

Allowed use:

- whole-site pre/post exploratory analysis;
- possible confirmed-background period before installation;
- no target-level numerical-depth calibration unless a larger isolated target footprint is independently demonstrated.

### Ahmadu Bello University geophysics test site

```text
site_size = approximately_55_m_x_55_m
sentinel_1_target_level_separation = not_supported
whole_site_pre_post_screen = priority_candidate_pending_dates
```

Reason: the field spans several Sentinel-1 resolution footprints, but many metallic and non-metallic target groups are distributed across a compact area. Individual target depths remain mixed at Sentinel-1 scale.

Why it remains useful:

- published studies include explicit pre-burial and post-burial geophysical surveys;
- the site was developed during the modern satellite era, although the exact installation date still must be recovered;
- the pre-burial state supplies a professionally documented background condition for ground methods;
- matched satellite acquisitions may support a whole-site change experiment after date verification.

Allowed use:

- whole-site pre/post exploratory analysis after construction dates are confirmed;
- possible confirmed-background period before installation;
- no target-level numerical-depth calibration from mixed Sentinel-1 cells.

## Correct experiment unit

For the current controlled sites, the honest satellite experiment unit is:

```text
physical_site_or_large_isolated_section
```

It is not:

```text
individual_small_buried_target
individual_GPR_profile
individual_10_m_resampled_pixel
```

Multiple GPR profiles or target labels inside one compact site must not be treated as independent satellite samples.

## Confirmed-background candidate states

Three sources document a state before target installation:

1. Texas A&M–Corpus Christi: official pre-installation survey before 2020 construction;
2. Ahmadu Bello: published pre-burial surveys with no target-related anomalies before installation;
3. IAG/USP: geophysical measurements were collected before target installation, but this predates Sentinel-1 and cannot provide a same-sensor Sentinel-1 background period.

A pre-burial ground survey is not automatically a Sentinel-1 negative record. It becomes a satellite-background candidate only when:

```text
installation_date_is_known
matching_pre_installation_satellite_acquisitions_exist
orbit_and_geometry_are_controlled
season_and_moisture_are_comparable
surface_construction_disturbance_is_separated_from_target_effects
```

## Consequence for the research plan

The public controlled sites remain useful, but their roles separate:

```text
target_level_depth_truth -> GPR_and_ground_method_research
site_level_pre_post_truth -> satellite_exploratory_research
small_target_satellite_depth_calibration -> not_supported_by_current_scale
```

This does not prove that Sentinel-1 can estimate buried depth. It provides a defensible next experiment that can fail honestly.

## Immediate execution plan

1. recover exact construction dates for Texas A&M–Corpus Christi and Ahmadu Bello;
2. identify public Sentinel-1 acquisition coverage before and after construction;
3. freeze same-orbit, same-mode, same-polarization comparisons;
4. match seasons and control rainfall or moisture where possible;
5. define one neutral whole-site window and surrounding background ring per site in private local storage;
6. compare changes in approved raw and contextual features only;
7. keep classifier outputs and target-derived geometry out of the feature vector;
8. add more independent sites before any model fitting;
9. use untouched physical sites for validation and holdout.

## Checklist

- [x] Use official Sentinel-1 spatial resolution rather than pixel spacing alone.
- [x] Screen TU1208 site scale.
- [x] Screen IAG/USP site scale.
- [x] Screen Texas A&M–Corpus Christi site scale.
- [x] Screen Ahmadu Bello site scale.
- [x] Reject target-by-target Sentinel-1 samples from compact mixed sites.
- [x] Preserve site-level pre/post research as an active path.
- [ ] Recover exact installation dates.
- [ ] Verify Sentinel-1 acquisition coverage and observation geometry.
- [ ] Define private site and background windows.
- [ ] Run matched pre/post feature extraction.
- [ ] Add independent sites for train, validation, and holdout.
