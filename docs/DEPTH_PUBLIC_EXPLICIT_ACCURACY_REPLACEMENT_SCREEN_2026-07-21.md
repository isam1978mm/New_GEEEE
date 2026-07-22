# Depth Public Explicit-Accuracy Replacement Screen — 2026-07-21

Status: `replacement_candidates_method_benchmarks_not_contract_ready`.

No email, form, author contact, operator contact, or records request was sent.

## Purpose

After P1–P7 public closeout, a targeted search was run for controlled buried-target studies that explicitly report survey or positioning accuracy. The goal was to find source-backed uncertainty for independent depth-to-top truth, not merely GPR prediction error.

## Candidate R1 — Japanese buried-pipe and cavity test yard

Primary source:

- Sada et al. (2025), DOI `10.2208/jscejj.24-22018`.

Verified from the journal record:

- measurements were taken at a test yard where buried-pipe and cavity locations were known;
- the GPR system was linked to VRS GNSS and a distance-measuring instrument;
- VRS positioning is described as having an error of several centimetres;
- reported horizontal position-detection accuracy was within approximately 0.2 m;
- reported vertical position-detection accuracy was approximately 0.05–0.20 m and worsened with depth.

Qualification distinction:

```text
known_test_yard_positions = yes
GNSS_positioning_accuracy = several_centimetres_reported
GPR_detection_error_horizontal = within_approximately_0.2_m
GPR_detection_error_vertical = approximately_0.05_to_0.20_m
independent_burial_depth_reference_uncertainty = not_extracted
construction_or_placement_tolerance = not_extracted
```

The GNSS specification and the reported GPR detection error must not be substituted for uncertainty in the independently known burial-depth label. Without the construction/survey method used to establish the pipe/cavity reference depths and its tolerance, this is not a contract-ready `known_depth_positive` source.

Decision:

```text
candidate_id = R1_JAPAN_2025_TEST_YARD
method_accuracy_benchmark = strong
reference_uncertainty_policy_source = no
private_pack_import = not_approved
```

## Candidate R2 — Malaysian pipe/soil controlled comparison

Primary source:

- Hassan et al., `Accuracy Assessment of GPR Data for Buried Objects with Different Pipes and Soil-Based Conditions`, DOI `10.52939/ijg.v19i5.2651`.

Verified from the article record:

- six controlled points compare PVC and iron pipes in three soil types;
- actual depths were obtained using a conventional levelling method;
- reported GPR-versus-reference RMSE values range from approximately 0.025 m to 0.093 m depending on pipe and soil type.

Qualification distinction:

```text
actual_depth_reference = conventional_levelling
GPR_vs_reference_RMSE = reported
levelling_instrument_accuracy = not_reported_in_public_record_reviewed
placement_tolerance = not_reported
final_depth_label_uncertainty = not_reported
```

The GPR-versus-reference RMSE is model/method performance, not the uncertainty of the actual-depth labels. It cannot populate `depth_reference_uncertainty_m` without source-backed levelling and placement tolerances.

Decision:

```text
candidate_id = R2_MALAYSIA_CONTROLLED_PIPE_SOIL
method_accuracy_benchmark = useful
reference_uncertainty_policy_source = no
private_pack_import = not_approved
```

## Replacement-screen decision

The targeted explicit-accuracy search found useful ground-method performance benchmarks but did not find a public source that provides all of:

```text
independent_depth_to_top_truth
+ explicit_reference_measurement_accuracy
+ placement_or_construction_tolerance
+ final_bounded_label_uncertainty
+ contract_complete_source_metadata
```

Therefore:

```text
public_reference_uncertainty_blocker = remains_blocked
TAMUCC_exact_shared_image_match = owner_run_gate
model_fitting = prohibited
app_depth_enabled = false
```

## Public references

- Japanese test-yard journal record: `https://www.jstage.jst.go.jp/article/jscejj/81/22/81_24-22018/_article/-char/en`
- Malaysian controlled pipe/soil article: `https://ijg.e-geoinfo.com/index.php/journal/article/view/2651`
