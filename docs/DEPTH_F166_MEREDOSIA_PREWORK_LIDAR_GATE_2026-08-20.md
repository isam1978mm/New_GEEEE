# Depth validation — F166 Meredosia pre-work lidar gate — 2026-08-20

## Decision

**F166 PASS.**

Meredosia advances as the first site-independent direct-elevation validation candidate.

This is not a Tyrone Step-4 success. Tyrone remains separately blocked on the missing 2004 immediate post-grading/pre-cover 3X surface.

## Pre-work elevation source

Dataset: **2017 USGS Lidar: West Central Illinois**.

Key metadata:

- counties include **Morgan County**, Illinois;
- geographic bounds approximately `-90.91` to `-89.21` longitude and `39.52` to `40.44` latitude;
- collection dates: **2017-12-03 through 2017-12-13**;
- nominal pulse spacing: **0.5 m**;
- specification: **USGS 3DEP Quality Level 2+**;
- original delivery: classified LAS 1.4 plus tiled bare-earth DEMs;
- original horizontal reference: NAD83(2011), Illinois West State Plane, US survey feet;
- original vertical reference: NAVD88 (GEOID12B), US survey feet;
- NOAA/USGS EPT distribution is also available online;
- independent non-vegetated accuracy testing used 91 checkpoints;
- reported `RMSEz = 0.06253 m`;
- required NVA was 19.6 cm at 95% confidence and the dataset passed;
- metadata reports no void or missing-data areas, with one specifically identified water-only/no-LAS tile in **Mason County** rather than Morgan County.

The Bottom Ash Pond location is approximately `39.82, -90.57`, which lies inside the dataset bounds.

## Timing gate

The lidar was acquired in December 2017.

Official Meredosia closure records state that Bottom Ash Pond clean closure began on **2018-03-12** and was completed on **2018-05-23**.

Therefore the lidar is clearly **pre-excavation**.

## Water / terrain usability gate

The Meredosia Closure Plan states that the plant ceased generating in February 2012 and that the Bottom Ash Pond reportedly had **no standing water within two months of plant closure**.

This materially strengthens the use of the December-2017 lidar as a terrain/ash-surface source rather than a water-surface observation.

The USGS metadata also states that classified point-cloud coverage is complete except for one explicitly identified water-only tile in Mason County.

Together, these facts are sufficient to pass the pre-work source gate and proceed to the post-work/as-built comparison stage.

Operational extraction of the exact Bottom Ash Pond lidar tile / point subset remains a required implementation step before any numerical depth is calculated.

## Clean-closure mask guard

Do not difference the entire ash-pond complex indiscriminately.

Official closure records state that the **pond itself was clean closed**, but the Bottom Ash Pond berm was excluded and some CCR associated with infrastructure/roadway/pipeline areas was treated separately / capped.

The validation footprint must therefore be the spatially verified clean-excavation area only.

## Frozen scientific gate

Do not relax the existing vertical-accuracy requirement after seeing results.

The pre-work lidar's reported `RMSEz = 0.06253 m` is below the frozen `0.15 m` historical-surface RMSE requirement, so the source is not rejected at this stage.

This does not yet prove the final difference surface will meet the complete validation gate; post-work surface accuracy, datum reconciliation, spatial registration and independent checks remain outstanding.

## Status after F166

- Meredosia elevation route: **ADVANCE**.
- Pre-work elevation timing: **PASS**.
- Pre-work dataset coverage at Meredosia: **PASS**.
- Pre-work source published vertical RMSE gate: **PASS**.
- Exact clean-excavation mask: **still to recover/verify**.
- Post-work/as-built surface: **identified as existing, not yet recovered/verified for numerical use**.
- Numerical excavation depth: **NOT YET COMPUTED**.
- Numerical-depth validation: **NOT YET CLAIMED**.
- Tyrone Step 4: **still blocked separately**.

## Exact next action — F167

Recover and verify the Meredosia 2018/2019 post-work/as-built surface.

Priority sources already identified:

1. Geotechnology / CDG Engineers **Ash Pond Closure, As-Built Plans, Meredosia Power Station (2019)**;
2. January 18, 2019 **Construction Quality Assurance Report**;
3. David Mason + Associates construction/final **UAS point cloud and DTM** products.

For the first available source, verify:

- acquisition/survey date;
- whether it represents the clean-excavated Bottom Ash Pond floor;
- spatial coverage and clean-closure boundary;
- vertical and horizontal datum;
- survey/control/accuracy metadata;
- whether later fill/cap/grading occurred before that surface was captured.

Do not calculate depth until the post-work surface and mask pass these checks.