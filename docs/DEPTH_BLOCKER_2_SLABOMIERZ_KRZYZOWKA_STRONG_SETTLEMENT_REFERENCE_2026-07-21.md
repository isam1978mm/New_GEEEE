# Depth Blocker 2 — Słabomierz–Krzyżówka Strong Settlement Reference — 2026-07-21

Status: `strong_settlement_reference_under_review`.

This candidate clears the practical `something good` threshold. It now has a defensible public chronology linking an official closure design and procurement to reported 2022 closure and actual matched full-surface surveys in March 2023 and March 2024. The published surveys include independent ground checks and centimetre-scale accuracy.

It does **not** yet clear the stricter cap-depth calibration gate because the certified final as-built surface, construction acceptance package, native survey surfaces, common datum, and proof of an untouched test polygon have not been retrieved.

No email, form, author contact, operator contact, or records request was sent.

## Candidate

- Site: Słabomierz–Krzyżówka reclaimed municipal landfill, near Żyrardów, Poland.
- Facility: approximately 14 ha; landfill body approximately 8.7–9 ha.
- Reported closure/reclamation year: 2022.
- Waste remained as a landfill body. The closure design describes shaping and sealing the landfill without disturbing deposited waste except for a localized northwestern reconstruction area.
- Fifteen permanent control points/benchmarks are reported on the landfill.

## Newly strengthened closure and cap evidence

### Official 2016 closure design

The operator's official archive exposes a May 2016 replacement construction design for closure and reclamation.

The design states that:

- the existing crown was approximately elevation 173 m;
- the designed crown was approximately elevation 175 m;
- approximately 2 m of cover/reclamation material was therefore planned over the crown;
- deposited waste was generally to remain undisturbed beneath the closure system;
- the closure system included a mineral clay/bentonite seal, a drainage sand layer, and an outer soil-forming/humus layer;
- the mineral seal was specified as approximately 0.50 m thick, with calcium bentonite at approximately 10 kg/m², over approximately 35,000 m²; and
- the drainage sand layer was specified as approximately 0.15–0.20 m thick.

This is site-specific **design thickness**, not proof of certified as-built thickness.

The same design includes a localized northwestern retaining-wall/slope reconstruction area where waste excavation and rebuilding were planned. That area, plus drainage, roads, wells, repairs, ponding, and other infrastructure, must be excluded from any candidate test polygon.

### Official closure procurement chronology

The operator's official procurement records provide the following sequence:

1. The 2017–2018 archive exposes the closure/reclamation design, technical specification, quantities, and drawings.
2. A separate 2018 stage concerned an access road made from concrete road slabs; it should not be treated as cap construction.
3. On 11 June 2021, PGK Żyrardów published proceeding `ZP.26.GO.16.2021`, titled `Zamknięcie i rekultywacja składowiska odpadów w miejscowości Słabomierz-Krzyżówka`.
4. The public proceeding includes a roughly 40 MB technical-documentation ZIP, specifications, contract draft, quantity workbook, and award decision.
5. The peer-reviewed monitoring paper reports the landfill as closed in 2022.
6. Full-surface monitoring surveys followed in March 2023 and March 2024.

This chronology materially strengthens the interpretation that the two UAV epochs are post-closure monitoring surveys rather than unrelated mapping.

The public procurement attachment itself is exposed, but its large ZIP could not be retrieved through the current browser/cache path. Its existence is verified; its contents were not guessed or represented as reviewed.

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

Reported crown settlement from March 2023 to March 2024 was generally about 0.05–0.15 m, with local values reaching approximately 0.20 m. This is materially larger than the approximately 0.016–0.017 m vertical check-point RMSE and therefore represents a measurable elevation-change signal.

A later study describes annual DSM comparison, fifteen benchmarks, and approximately centimetre-scale agreement with leveling, independently supporting the monitoring framework.

## Remaining limitations

### 1. Stage III timing and footprint are unresolved

The operator states that financing for `Closure and reclamation of the Słabomierz–Krzyżówka landfill — Stage III` was signed on 27 December 2023. The stated Stage III scope covers 3.5 ha of the crown and includes earthworks, a mineral clay seal, a soil-forming layer, and biological reclamation.

The financing date falls between the March 2023 and March 2024 surveys, but it does **not** prove that physical construction occurred before the March 2024 survey. The prior classification overstated construction overlap. Exact construction start, completion, acceptance date, and footprint remain required.

Until those records are retrieved, the full-crown difference surface cannot be treated as settlement-only truth. A construction-free polygon may exist, but it has not yet been proven.

### 2. Surface-process contamination requires masks

The published comparison identifies:

- a local apparent uplift associated with placed repair soil;
- a depression affected by water accumulation;
- erosion/runoff effects;
- vegetation/surface-cover effects; and
- slope movement with horizontal components.

These areas require explicit masks.

### 3. Native survey products are not publicly downloadable

The paper's data-availability statement says the underlying data are available from a co-author on request. The published paper contains matched-survey results, accuracy statistics, figures, and methods, but no public download link for the complete native point clouds or DSMs.

No request was sent because external contact has not been authorized.

### 4. Certified as-built bridge remains missing

The 2016 design now documents site-specific intended cover thickness and layers. The public record reviewed so far still does not expose:

- the certified pre-cap or final-subgrade terrain surface;
- the certified final as-built cap surface;
- the executed 2021 construction acceptance/completion package;
- surveyed actual layer thickness across the candidate polygon;
- Stage I/II/III native construction surfaces and exact boundaries;
- a construction-completion map proving which areas were untouched between March 2023 and March 2024; or
- a certified common datum/coordinate-system statement linking construction and monitoring surfaces.

## Classification

```text
candidate_id = SLABOMIERZ-KRZYZOWKA-2022
candidate_state = strong_settlement_reference_under_review
something_good_threshold = pass
actual_matched_surface_evidence = pass_published
closure_design = pass_official_2016
final_closure_procurement = pass_official_2021
closure_year = 2022_reported_peer_reviewed
waste_left_in_place = pass_except_local_northwest_reconstruction_exclusion
survey_epoch_1 = march_2023
survey_epoch_2 = march_2024
full_surface_point_clouds = pass
independent_ground_check = pass
control_points = 15
check_points = 14
vertical_checkpoint_rmse_2023 = 0.017_m
vertical_checkpoint_rmse_2024 = 0.016_m
observed_crown_settlement = generally_0.05_to_0.15_m_local_max_approximately_0.20_m
design_total_cover_thickness = approximately_2_m
design_mineral_clay_bentonite_seal = approximately_0.50_m
design_drainage_sand = approximately_0.15_to_0.20_m
design_outer_soil_humus_layer = pass_thickness_requires_drawing_or_quantity_confirmation
certified_as_built_thickness = unresolved
certified_pre_cap_surface = unresolved
certified_final_as_built_surface = unresolved
raw_public_surface_download = fail_request_only
stage_III_financing_date = 2023_12_27
stage_III_physical_overlap = unresolved_not_proven
stage_III_scope = 3.5_ha_crown_earthworks_clay_seal_soil_layer_and_seeding
northwest_waste_rebuild_area = exclude
repair_mask = required
ponding_erosion_vegetation_mask = required
infrastructure_mask = required
clean_interior_polygon = promising_but_unproven
settlement_method_benchmark = ready_published_results_only
raw_data_settlement_calibration = not_ready
cap_depth_calibration = not_ready
external_contact_authorized = false
```

## Decision

Retain Słabomierz–Krzyżówka as the strongest post-closure matched full-surface settlement reference found in this screening pass.

It now has:

1. an official site-specific closure design with documented intended cover thickness and layers;
2. an official 2021 final closure/reclamation procurement and technical package;
3. reported closure in 2022;
4. actual March 2023 and March 2024 full-surface surveys; and
5. independent centimetre-level accuracy checks.

Do not call it cap-depth calibration-ready. The certified as-built surface, actual constructed thickness, native survey data, common datum, Stage III timing and footprint, and a proven construction-free polygon remain missing.

## Waiting for

```text
2021_public_technical_documentation_ZIP_contents
+ executed_2021_contract_and_completion_acceptance
+ certified_final_as_built_drawings_or_surface
+ certified_pre_cap_or_final_subgrade_surface
+ surveyed_actual_cover_layer_thickness
+ Stage_I_II_III_completion_dates_and_boundaries
+ proof_of_clean_polygon_untouched_between_march_2023_and_march_2024
+ raw_march_2023_point_cloud_or_DSM
+ raw_march_2024_point_cloud_or_DSM
+ common_horizontal_and_vertical_datum
+ construction_survey_accuracy_statement
+ masks_for_northwest_rebuild_repair_soil_ponding_erosion_vegetation_and_infrastructure
```

## Next step

Continue public-only retrieval of the 2021 technical-documentation ZIP, executed contract, completion acceptance, as-built drawings/surfaces, and Stage III start/completion records. Then test whether a clean interior polygon can be proven outside the northwestern reconstruction, Stage III works, repairs, drainage, roads, wells, ponding, erosion, and vegetation-change areas.

Do not contact the authors, operator, contracting authority, or any agency unless the user explicitly authorizes it.

## Public references

- PGK Żyrardów official 2017–2018 procurement archive, closure/reclamation documentation and drawings: `https://www.pgk.zyrardow.pl/434%2Cprzetargi-i-zamowienia-archiwum-lata-2017-2018`
- PGK Żyrardów, May 2016 replacement construction design: `https://www.pgk.zyrardow.pl/plik%2C2611%2Cprojekt-budowlany-pdf.pdf`
- PGK Żyrardów official 2021 procurement proceeding `ZP.26.GO.16.2021`: `https://platformazakupowa.pl/transakcja/469789`
- PGK Żyrardów Stage III financing notice: `https://www.pgk.zyrardow.pl/242%2Caktualnosci?tresc=2859`
- Pasternak, G.; Pasternak, K.; Koda, E.; Ogrodnik, P. `Unmanned Aerial Vehicle Photogrammetry for Monitoring the Geometric Changes of Reclaimed Landfills.` Sensors 2024, 24, 7247. `https://doi.org/10.3390/s24227247`
- Open full text: `https://pmc.ncbi.nlm.nih.gov/articles/PMC11598493/`
- Pasternak, G. et al. `UAV-Based Remote Sensing Methods in the Structural Assessment of Remediated Landfills.` Remote Sensing 2026, 18, 57. `https://doi.org/10.3390/rs18010057`
