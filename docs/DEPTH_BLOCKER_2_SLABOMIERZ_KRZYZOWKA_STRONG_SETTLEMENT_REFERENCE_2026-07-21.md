# Depth Blocker 2 — Słabomierz–Krzyżówka Strong Settlement Reference — 2026-07-21

Status: `strong_settlement_reference_under_review`.

This candidate clears the practical `something good` threshold because actual matched full-surface survey evidence exists, with explicit independent ground checks and centimetre-scale accuracy. It does **not** yet clear the stricter cap-depth calibration gate because closure/reclamation construction overlapped the survey interval, the raw point clouds are not publicly downloadable, and the site-specific as-built cap thickness and construction surfaces have not been retrieved.

No email, form, author contact, operator contact, or records request was sent.

## Candidate

- Site: Słabomierz–Krzyżówka reclaimed landfill, near Warsaw, Poland.
- Landfill body: approximately 8.7–9 ha within an approximately 14 ha facility.
- Reported closure/reclamation year: 2022.
- Waste remained as a landfill body; later work concerns closure, sealing, drainage, degassing, shaping, and reclamation rather than clean closure by removal.
- Fifteen permanent control points/benchmarks are reported on the landfill.

## Matched survey evidence

A peer-reviewed 2024 study reports two full-surface UAV photogrammetry campaigns over the same landfill:

| Item | March 2023 survey | March 2024 survey |
|---|---:|---:|
| Images | 1,621 | 1,166 |
| Ground sample distance | 1.84 cm | 2.57 cm |
| Ground control points | 15 | 15 |
| Check points | 14 | 14 |
| Bundle RMSE XY | 0.006 m | 0.008 m |
| Bundle RMSE Z | 0.008 m | 0.006 m |
| Check-point RMSE XY | 0.011 m | 0.009 m |
| Check-point RMSE Z | 0.017 m | 0.016 m |
| Mean point density | approximately 412 points/m² | approximately 229 points/m² |

The study compared the dense point clouds with the M3C2 algorithm and checked UAV-derived elevation changes against classical ground surveying, including trigonometric leveling/GNSS monitoring.

Reported crown settlement from March 2023 to March 2024 was generally about 0.05–0.15 m, with local values reaching approximately 0.20 m. This is materially larger than the approximately 0.016–0.017 m vertical check-point RMSE and therefore is a real measurable settlement signal rather than a change smaller than the stated survey uncertainty.

A 2025/2026 follow-on study reports annual DSM comparison, fifteen benchmarks, and agreement with leveling at approximately centimetre scale, providing an independent later description of the same monitoring framework.

## Why it is not cap-depth calibration-ready

### 1. Reclamation construction overlapped the survey interval

The operator states that financing for `Closure and reclamation of the Słabomierz–Krzyżówka landfill — Stage III` was signed on 27 December 2023. The stated Stage III work covers 3.5 ha of the landfill crown and includes:

- earthworks to shape the landfill body and secure the slope;
- placement of a mineral clay seal;
- placement of a soil-forming reclamation layer; and
- biological reclamation/seeding.

That work falls between the March 2023 and March 2024 survey epochs, or at minimum creates unresolved timing overlap. Therefore a full-crown difference surface cannot be interpreted as settlement alone.

### 2. Local repair and surface-process contamination exist

The 2024 study identifies:

- a local apparent uplift associated with soil placed during repair work;
- a depression affected by water accumulation;
- erosion/runoff effects; and
- vegetation/surface-cover effects.

These areas require explicit masks even if a clean interior polygon can later be isolated.

### 3. Native survey products are not publicly downloadable

The paper's data-availability statement says the underlying data are available from a co-author on request. The published paper contains the matched-survey results, accuracy statistics, figures, and method, but not public download links for the complete native point clouds or DSMs.

No request was sent because external contact has not been authorized.

### 4. Missing cap-depth bridge

The public record reviewed so far does not expose:

- the certified pre-closure or pre-cap terrain surface;
- the final as-built cap surface;
- the Stage I/II/III native construction surfaces;
- site-specific final-cover thickness across the candidate polygon;
- a construction-completion boundary showing which crown areas were untouched between March 2023 and March 2024; or
- a certified common datum/coordinate-system statement for all construction and monitoring surfaces.

The general Polish closure rules do not substitute for site-specific as-built thickness.

## Classification

```text
candidate_id = SLABOMIERZ-KRZYZOWKA-2022
candidate_state = strong_settlement_reference_under_review
something_good_threshold = pass
actual_matched_surface_evidence = pass_published
closure_year = 2022_reported
waste_left_in_place = likely_pass_pending_closure_decision
survey_epoch_1 = march_2023
survey_epoch_2 = march_2024
full_surface_point_clouds = pass
independent_ground_check = pass
control_points = 15
check_points = 14
vertical_checkpoint_rmse_2023 = 0.017_m
vertical_checkpoint_rmse_2024 = 0.016_m
observed_crown_settlement = generally_0.05_to_0.15_m_local_max_approximately_0.20_m
raw_public_surface_download = fail_request_only
one_event_final_cap = fail_or_unresolved_due_stage_III_overlap
stage_III_overlap = 3.5_ha_crown_earthworks_clay_seal_soil_layer_and_seeding
repair_mask = required
ponding_erosion_mask = required
pre_cap_surface = unresolved
certified_final_as_built_surface = unresolved
site_specific_cap_thickness = unresolved
construction_surface_datum = unresolved
clean_interior_polygon = possible_but_unproven
settlement_method_benchmark = ready_published_results_only
raw_data_settlement_calibration = not_ready
cap_depth_calibration = not_ready
external_contact_authorized = false
```

## Decision

Retain Słabomierz–Krzyżówka as the strongest newly found **settlement-method and survey-accuracy reference**.

It is the first candidate in this screening pass with both:

1. actual matched full-surface surveys over consecutive years; and
2. explicit independent centimetre-level survey validation.

Do not use the whole published difference surface as landfill-settlement truth without separating Stage III construction, repairs, ponding, erosion, and other surface changes. Do not use it as cap-thickness ground truth until the pre-cap/as-built bridge and site-specific cover thickness are retrieved.

## Waiting for

```text
specific_official_closure_decision
+ Stage_I_II_III_completion_dates_and_boundaries
+ certified_stage_III_as_built_drawings_or_surface
+ proof_of_clean_polygon_untouched_between_march_2023_and_march_2024
+ site_specific_final_cover_layer_thickness
+ certified_pre_cap_or_subgrade_surface
+ certified_final_as_built_surface
+ raw_march_2023_point_cloud_or_DSM
+ raw_march_2024_point_cloud_or_DSM
+ common_horizontal_and_vertical_datum
+ construction_survey_accuracy_statement
+ masks_for_repair_soil_placement_ponding_erosion_and_infrastructure
```

## Next step

Continue public-only archive research for the specific Polish closure decision, Stage III tender/completion package, construction boundary, layer thickness, and any openly indexed native survey products. Do not contact the authors or operator unless the user explicitly authorizes it.

## Public references

- Pasternak, G.; Pasternak, K.; Koda, E.; Ogrodnik, P. `Unmanned Aerial Vehicle Photogrammetry for Monitoring the Geometric Changes of Reclaimed Landfills.` Sensors 2024, 24, 7247. https://doi.org/10.3390/s24227247
- Open full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC11598493/
- PGK Żyrardów operator notice, `Zamknięcie i rekultywacja składowiska Słabomierz-Krzyżówka`: https://www.pgk.zyrardow.pl/242%2Caktualnosci?tresc=2859
- Pasternak, G. et al. `UAV-Based Remote Sensing Methods in the Structural Assessment of Remediated Landfills.` Remote Sensing 2026, 18, 57. https://doi.org/10.3390/rs18010057
