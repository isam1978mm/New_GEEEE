# Depth P1/P2 Reference-Uncertainty Public Closeout — 2026-07-21

Status: `public_uncertainty_search_closed_requires_source_file_or_authority_record`.

No email, form, author contact, or records request was sent.

## Decision

The public record is sufficient to retain TU1208/IFSTTAR and IAG/USP as strong controlled-site ground-method references, but it is not sufficient to assign a numerical independent reference uncertainty for private calibration-pack import.

Do not substitute GPR-estimate error, paper table precision, generic theodolite specifications, or a guessed tolerance for the missing construction/survey uncertainty.

## P1 — TU1208 / IFSTTAR Nantes

Publicly confirmed:

- targets were geolocated during construction using a theodolite;
- several upper-side or upper-corner points were measured per target;
- the finished surface was georeferenced and locally interpolated to calculate depth to the target upper side;
- the public paper describes the resulting reference as independently surveyed construction truth;
- a complete topographic file describing the pit, object positions, and finished surface exists.

Publicly unresolved:

- instrument model and calibration;
- control-network closure;
- point residuals;
- vertical and horizontal survey accuracy;
- target-placement tolerance;
- surface-interpolation uncertainty;
- final bounded uncertainty for each depth-to-top value.

The paper states that the complete topographic file is available on request, while the public Zenodo archive contains the radar supplementary package but does not expose a numerical survey-uncertainty statement.

Later papers about uncertainty at the IFSTTAR site concern uncertainty of GPR-derived depth estimates. That is method-output uncertainty and cannot be used as uncertainty of the independent construction reference.

Classification:

```text
candidate = P1_TU1208_IFSTTAR
physical_depth_provenance = independently_surveyed
reference_definition = surface_to_target_upper_side
public_reference_uncertainty = not_reported
method_research_usable = yes
direct_app_calibration_usable = no_current_scale
private_pack_import_approved = no
remaining_path = obtain_original_topographic_file_and_survey_metadata
```

## P2 — IAG/USP

Publicly confirmed:

- targets were installed at known depths;
- an open-trench topographic survey established positions and depths relative to the ground surface;
- Line 4 actual depth values are published for eight targets;
- the depth definition is ground surface to target top.

Publicly unresolved:

- survey instrument and calibration;
- measurement residuals;
- target-placement tolerance;
- surface-reference uncertainty;
- numerical uncertainty attached to the published actual depths.

The published number of decimal places and the difference between GPR estimates and actual depths are not reference uncertainty. They cannot be converted into an uncertainty value without source support.

Classification:

```text
candidate = P2_IAG_USP
physical_depth_provenance = installed_and_topographically_surveyed
reference_definition = ground_surface_to_target_top
public_reference_uncertainty = not_reported
method_research_usable = yes
direct_app_calibration_usable = no_current_scale_and_missing_uncertainty
private_pack_import_approved = no
remaining_path = obtain_original_construction_sheet_or_topographic_survey_metadata
```

## Blocker effect

P1 and P2 do not currently supply contract-eligible positive records for the private pack. Their physical-depth provenance remains valuable, but their public-only uncertainty paths are exhausted unless the original construction/topographic records become available.

This does not weaken the rule that one compact controlled site is one leakage group and cannot be split into multiple independent Sentinel-1 train, validation, or holdout sites.

## Waiting for

```text
P1_complete_topographic_file
+ P1_instrument_control_residuals_and_surface_interpolation_accuracy
+ P2_original_construction_or_target_spreadsheet
+ P2_topographic_survey_method_and_accuracy
+ source_supported_depth_reference_uncertainty
```

## Next step

Move to candidates whose primary source already reports installation or survey uncertainty explicitly. Do not continue repeating the same public P1/P2 searches and do not invent an uncertainty value.

## Public references

- Dérobert, X.; Pajewski, L. `TU1208 Open Database of Radargrams: The Dataset of the IFSTTAR Geophysical Test Site.` Remote Sensing 2018, 10, 530. https://doi.org/10.3390/rs10040530
- TU1208 supplementary archive. https://doi.org/10.5281/zenodo.1211173
- Xie, F.; Lai, W. W. L.; Dérobert, X. `GPR uncertainty modelling and analysis of object depth based on constrained least squares.` Measurement 2021, 183, 109799. https://doi.org/10.1016/j.measurement.2021.109799
- Porsani, J. L. et al. `O sítio controlado de geofísica rasa do IAG/USP: instalação e resultados GPR 2D-3D.` Revista Brasileira de Geofísica 2006, 24(1), 49–61. https://doi.org/10.1590/S0102-261X2006000100004
- Poluha, B. et al. `Depth Estimates of Buried Utility Systems Using the GPR Method: Studies at the IAG/USP Geophysics Test Site.` International Journal of Geosciences 2017, 8, 726–742. https://doi.org/10.4236/ijg.2017.85040
