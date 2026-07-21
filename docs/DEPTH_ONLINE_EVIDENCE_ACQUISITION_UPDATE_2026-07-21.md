# Depth Online Evidence Acquisition Update — 2026-07-21

Status: evidence search continued after Gmail send/draft actions were unavailable because account approval was declined. No email was sent, no calibration row was approved, and app depth remains disabled.

## Current decision

```text
online_search_status = additional_candidates_found
email_send_status = blocked_user_account_approval_declined
approved_known_depth_positive_records = 0
approved_confirmed_negative_records = 0
relative_depth_baseline_status = not_fitted
app_depth_enabled = false
```

## Candidate P11 — Italian buried-steel-drum test site

Primary source:

- DOI `10.4401/ag-4846`
- article title: `Integrated geophysical measurements on a test site for detection of buried steel drums`

Verified source facts:

- controlled test in clayey-sandy ground;
- twelve empty steel drums were buried;
- reported burial depth is approximately 4–5 m below ground level;
- three methods were used: magnetometry, electrical resistivity tomography, and frequency-domain electromagnetic induction;
- the paper is openly accessible from Annals of Geophysics;
- no machine-readable target table, raw-data archive, exact drum-by-drum depth, depth-reference definition, construction dates, or numerical placement uncertainty was found during this search pass.

Current classification:

```text
physical_depth_provenance = installed_known_approximate_depth
reference_definition = unresolved_top_vs_centre_vs_base
reference_uncertainty_m = not_reported
real_field_data = yes
benign_targets = yes
buried_target_count = 12
reported_depth_range_m = 4_to_5
multi_method_measurements = yes
raw_public_dataset_confirmed = no
machine_readable_target_table = not_found
multiple_physical_sites = no_single_site
source_evidence_usable = promising_pending_exact_reference
method_research_usable = yes
private_pack_import_approved = no
priority = 1_request_data
```

Required next work:

1. request the construction/as-built table for all twelve drums;
2. resolve whether 4–5 m means depth to top, centre, base, or excavation depth;
3. request numerical placement and survey uncertainty;
4. request acquisition dates and raw magnetometry, ERT, and FDEM files;
5. request any pre-burial or independently verified background survey;
6. treat the entire installation as one physical-site group;
7. assess only whole-site or large-section satellite support, not drum-level Sentinel-1 rows.

## Ahmadu Bello University evidence strengthened

Additional public sources reviewed:

- open magnetic study, DOI `10.1016/j.rines.2024.100016`;
- open VLF-EM study, DOI `10.1007/s42452-024-05650-6`;
- related magnetic characterization article describing pre- and post-installation measurements.

Additional verified facts:

- magnetic total-field measurements were collected before and after burial;
- the pre-burial field was intended to identify existing buried materials or faults that could create false anomalies;
- the site contains targets with known material, geometry, orientation, and burial depth;
- the VLF-EM study also compares site response with and without buried targets;
- the multi-method evidence strengthens the value of the site as a ground-method validation case;
- it still does not supply numerical installation uncertainty or an openly downloadable complete raw-data package.

Qualification update:

```text
pre_burial_background_methods = magnetic_and_VLF_EM_confirmed
post_burial_methods = magnetic_VLF_EM_ERT_and_related_methods
independent_confirmed_negative_site = no_same_physical_site
same_site_pre_burial_control = yes
source_evidence_usable = strong_for_ground_method_truth
private_pack_import_approved = no_missing_uncertainty_and_source_package
```

The pre-burial state is valuable as a same-site control. It must not be treated as an independent negative holdout because it belongs to the same physical site and construction context as the post-burial observations.

## TU1208 access route strengthened

The open TU1208 article states that construction photos, videos, and a complete topographical file describing pit geometry, object positions, and finished-surface topography are available on request.

This means the next request should specifically ask for:

```text
complete topographical file
object-position survey points
finished-surface survey points
depth calculation worksheet or export
survey instrument specification
survey and interpolation uncertainty
construction photos and videos
```

The public raw radargrams remain useful, but private-pack import remains blocked until a defensible uncertainty policy and complete record mapping are established.

## Search conclusion

The search now contains at least six independent physical-site leads with installed or surveyed depth information:

```text
TU1208_IFSTTAR
IAG_USP
TAMUCC
Ahmadu_Bello
Sense_City
Teoloyucan
Italian_steel_drum_site
```

These are source leads, not approved calibration records. No single package yet satisfies all of the following:

```text
exact_depth_to_top
numerical_reference_uncertainty
raw_sensor_files
acquisition_dates
complete_target_mapping
confirmed_independent_negative_site
multiple_independent_physical_sites
satellite_scale_support
```

## Next execution order

1. send or manually send the prepared requests once Gmail access is approved;
2. add a targeted request for the Italian steel-drum site;
3. ask TU1208 specifically for its complete topographical file and uncertainty information;
4. continue searching for independently documented negative physical sites rather than same-site controls;
5. import nothing until provenance, uncertainty, scale, and grouping rules pass;
6. keep app depth disabled.
