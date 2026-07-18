# Public Controlled-Site Target Depth Extraction — 2026-07-18

Status: public evidence extraction complete for two controlled physical sites. These are source-level depth facts, not approved app calibration records. No model is fitted and app depth output remains unavailable.

## Purpose

This document extracts numerical depth-to-top evidence from openly available controlled-site publications while preserving the distinction between:

```text
installed_or_surveyed_true_depth
geophysical_estimated_depth
app_calibration_approval
```

Only the installed or independently recorded depth is retained as candidate truth. Estimated depths from GPR, ERT, VLF-EM, magnetic, or other geophysical methods are not used as labels.

## Source A — IAG/USP Line 4 controlled targets

Primary source:

- DOI `10.4236/ijg.2017.85040`

Supporting source:

- DOI `10.1590/S0102-261X2006000100004`

The 2017 study reports eight real controlled targets on Line 4 and compares independently known real depths with GPR-derived estimates. A separate site description states that target-top depths at IAG/USP vary from approximately 0.5 m to 2.0 m for the relevant utility targets.

### Extracted real depths

| Public target label | Real depth (m) | Evidence meaning |
|---|---:|---|
| A | 1.97 | independently known controlled-site target depth |
| B | 0.50 | independently known controlled-site target depth |
| C | 0.98 | independently known controlled-site target depth |
| D | 0.50 | independently known controlled-site target depth |
| E | 0.90 | independently known controlled-site target depth |
| F | 0.97 | independently known controlled-site target depth |
| G | 1.00 | independently known controlled-site target depth |
| H | 1.98 | independently known controlled-site target depth |

### Source interpretation

```text
physical_site_group = iag_usp_controlled_site
public_line_group = line_4
reference_status = known_depth_positive_candidate
reference_depth_definition = target_top_or_apex_depth_supported_by_site_description
reference_uncertainty = not_reported
raw_gpr_acquisition = 270_MHz_profile_reported
satellite_feature_compatibility = pending
private_pack_import = not_yet
```

### Missing fields before calibration import

- target-level material and orientation mapping for A through H;
- exact target dimensions for every label;
- documented installation or survey uncertainty;
- acquisition date and raw radar file availability;
- approved satellite-feature support and pixel-mixing assessment;
- a defensible uncertainty policy if the original installation uncertainty cannot be recovered.

All eight labels belong to one physical site and must stay in one split group.

## Source B — Ahmadu Bello University Geophysics Test Site

Primary source:

- DOI `10.1016/j.envc.2024.100910`

Supporting controlled-site sources:

- DOI `10.1007/s11600-023-01096-3`
- DOI `10.1007/s44288-024-00058-6`

The open 2024 depth-comparison paper provides an explicit `Depth to top (m)` column for eight installed target groups. The values below are taken from that true-depth column, not from the ERT or VLF-EM estimate columns.

### Extracted depth-to-top values

| Public target description | Depth to top (m) | Evidence meaning |
|---|---:|---|
| six empty plastic buckets | 0.80 | installed controlled-site depth to top |
| one horizontally buried empty steel drum | 0.80 | installed controlled-site depth to top |
| two horizontally buried empty steel drums | 1.00 | installed controlled-site depth to top |
| one vertically buried empty steel drum | 0.60 | installed controlled-site depth to top |
| six water-filled plastic buckets | 0.80 | installed controlled-site depth to top |
| four-cylinder engine block | 1.20 | installed controlled-site depth to top |
| concrete block | 0.80 | installed controlled-site depth to top |
| two horizontally buried pipes | 0.50 | installed controlled-site depth to top |

### Source interpretation

```text
physical_site_group = ahmadu_bello_controlled_site
reference_status = known_depth_positive_candidate
reference_depth_definition = explicitly_depth_to_top
reference_uncertainty = not_reported
multi_method_field_data = yes
underlying_dataset_access = author_request
satellite_feature_compatibility = pending
private_pack_import = not_yet
```

### Missing fields before calibration import

- target-level dimensions and exact orientation metadata for every grouped row;
- installation uncertainty or a documented uncertainty policy;
- machine-readable field data and acquisition dates;
- neutral mapping between target groups and survey profiles;
- approved satellite-feature support and pixel-mixing assessment.

The eight target groups belong to one physical site and must stay in one split group.

## Evidence count produced by this extraction

```text
independent_physical_site_groups = 2
public_candidate_target_rows = 16
rows_with_explicit_depth_to_top_wording = 8
rows_with_controlled_real_depth_and_supporting_target_top_definition = 8
rows_with_reported_reference_uncertainty = 0
rows_approved_for_private_pack_import = 0
```

The absence of reported uncertainty does not invalidate the sources. It creates an active follow-up task: recover construction tolerances or define and document a conservative source-specific uncertainty policy before import.

## Non-circularity rule

The following values must not replace the extracted true-depth column:

```text
GPR estimated depth
ERT estimated depth
VLF-EM estimated depth
magnetic Euler depth
classifier output
notebook output
app output
```

Those values may later be compared against the true depths as research predictions, but never used as labels.

## Next execution steps

1. map IAG/USP labels A–H to target material, orientation, dimensions, and depth-to-top definition;
2. extract Ahmadu Bello target dimensions and profile mappings from the open papers;
3. obtain construction or survey uncertainty for both sites;
4. request raw or machine-readable field data where not publicly downloadable;
5. screen each whole site for approved satellite-feature availability and pixel mixing;
6. create private calibration rows only after all required contract fields are supportable;
7. keep each physical site entirely within one train, validation, or holdout group.

## Checklist

- [x] Extract IAG/USP real target depths A–H.
- [x] Extract Ahmadu Bello explicit depth-to-top values.
- [x] Exclude geophysical estimates from calibration truth.
- [x] Preserve one physical-site group per controlled site.
- [ ] Recover IAG/USP target material and orientation mapping.
- [ ] Recover target dimensions for both sources.
- [ ] Recover or define reference-depth uncertainty.
- [ ] Obtain acquisition dates and machine-readable field data.
- [ ] Complete satellite-scale compatibility screening.
- [ ] Import only fully supported records into the private pack.
