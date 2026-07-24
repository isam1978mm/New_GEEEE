# Sudbury Numerical Control Evidence Update — 2026-07-25

**Branch:** `main`  
**Status:** numerical construction-control evidence found; calibration geometry and final as-built values still missing  
**Purpose:** record the first source-supported numerical tolerance found for the Sudbury depth route

## Plain-English result

The Sudbury public construction specifications contain real numerical survey-stake and cover-construction tolerances. This is a material improvement over the earlier conclusion that no numerical control bound was public.

It does **not** yet justify treating every part of the cover as one exact measured depth. The published values control construction and survey staking. The final certified as-built thickness surface and its mapped values still need to be extracted.

## Official source package

Washington Department of Ecology, Sudbury Road Landfill, Cleanup Site ID `2485`:

- Construction Plans and Specs — Volume I — Final, document `53360`;
- Construction Plans and Specs — Volume III CQA — Final, document `53362`;
- Construction Quality Assurance Certification Report, document `64264`.

Coordinate-bearing geometry and any extracted survey surface must remain outside Git.

## Numerical survey and construction controls found

### Survey-stake controls

Section 01052 requires conventional survey methods for as-built and payment surveys. It requires:

- equivalent survey-point distributions for comparisons;
- at least a 50-foot (`15.24 m`) grid for the final Area 2 and Area 5 surface surveys used for record drawings;
- established local benchmarks unique to the landfill;
- electronic delivery of survey points, digital terrain-model surfaces, and earthwork calculations;
- independent checks by the owner when desired.

The same section lists vertical stake-setting tolerances including:

- slope stakes: `±0.02 ft` (`±0.006096 m`);
- Area 2/5 subgrade stakes: listed with a `±0.025 ft` (`±0.00762 m`) vertical control component;
- Area 2/5 rough-grade stakes: listed with a `±0.025 ft` (`±0.00762 m`) vertical control component;
- surfacing-grade stakes: `±0.025 ft` (`±0.00762 m`).

These are **stake-setting and construction-control tolerances**, not automatically the uncertainty of every final as-built depth value.

### Cover-thickness acceptance control

The Site Grading and Earthwork quality-assurance table lists the Area 2 and Area 5 soil-cover finish-grade check as:

```text
procedure = field visual verification from hand auger / survey staking
frequency = 100-foot grid
requirement = -0.10 foot to 0 foot
```

The one-sided amount is `0.10 ft` (`0.03048 m`).

The CQA manual separately requires:

- subgrade elevations set about five feet below finished grade;
- grade control to control installed thickness;
- verification of soil-cover thickness;
- final as-built survey of finished grade;
- acceptance only when the cover is at least `4.8 ft` (`1.46304 m`) thick.

The completed construction record previously established that both subgrade and finished grade were professionally surveyed, digital terrain models were compared, and test pits cross-checked the minimum thickness.

## What this evidence can support

The public record now supports all of the following:

```text
actual_constructed_minimum_depth = yes
minimum_depth_m = 1.46304
professional_subgrade_and_finish_surveys = yes
source_supported_stake_tolerance = yes
source_supported_cover_acceptance_tolerance = yes
surface_model_comparison = yes
test_pit_cross_check = yes
```

This means Sudbury is no longer accurately described as having no numerical control evidence.

## What it still cannot support

The following remain unresolved:

- the exact certified as-built depth or thickness value for each mapped footprint;
- whether the `-0.10 ft to 0 ft` table entry applies directly to thickness, finish-grade elevation, or both after the flattened PDF table is interpreted against the original visual table;
- a final uncertainty interval for each satellite-scale polygon;
- an independently confirmed no-target comparison footprint;
- a clean and unchanged Sentinel-1 observation window;
- independent train, validation, and holdout groups.

The `±0.025 ft` stake-setting tolerance must not be presented as the total final depth uncertainty. It does not include all construction, surface-model, interpolation, settlement, and footprint-aggregation effects.

## Current classification

```text
reference_status = measured_minimum_depth_with_control_bound_pending_as_built_surface
positive_depth_evidence = strong
numerical_control_bound_candidate = yes
final_depth_uncertainty_m = not_assigned
exact_private_geometry_extracted = no
confirmed_no_target_geometry = no
eligible_calibration_row = no
```

## Decision

Sudbury is now the strongest public **bounded minimum-depth** lead.

Do not create a calibration row yet. First extract the certified as-built drawing values and map them to Areas 2 and 5. Then determine whether the public construction tolerance can be combined with the as-built surface and an added spatial/interpolation uncertainty term.

## Next bounded action

Continue only with:

1. Construction Quality Assurance Certification Report `64264` and its certified as-built drawings, to recover mapped surface values;
2. the original visual table in document `53360`, to confirm the exact meaning of the `-0.10 ft to 0 ft` requirement;
3. official records that independently establish a no-target comparison area at Sudbury;
4. unchanged post-construction dates suitable for Sentinel-1 matching.

No generic candidate search, outreach, model training, or app-depth enablement is authorized by this evidence update.
