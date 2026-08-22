# F195 — Tangerine bounded lidar execution

Date: 2026-08-21

## Decision

Re-open **Tangerine Landfill only** for one bounded execution. This does not reopen the generic public-lidar site search.

F193 dropped Tangerine because the exact 2021 same-footprint coverage was not proven within the three-fingerprint site budget. That unresolved gate is now answered **YES**.

## Coverage result

The public OpenTopography/USGS 3DEP spatial boundary for `AZ_PimaCo_2_2021` contains the Tangerine Landfill location/footprint area.

Boundary source:

- `OpenTopography/Data_Catalog_Spatial_Boundaries`
- `USGS_3DEP/AZ_PimaCo_2_2021.geojson`

Tangerine location/boundary provenance remains tied to the official Pima County record-of-survey entry `RS-33-039`, "Pima County Survey / Results of Survey for Tangerine Landfill on Tangerine Rd., Located in Portions of Sections 1 & 2, T12S, R11E". The official record page identifies scanned file `RS-33-039_001.TIF`.

For automated execution only, the runner may use OpenStreetMap way `714462943` (`landuse=landfill`) as a provisional mask. That geometry is **not final claim geometry** and must be checked against `RS-33-039` before any final scientific claim.

## Frozen timing bracket

The F193 timing findings remain unchanged:

- waste acceptance ended: **2013**;
- pre surface: PAG / USGS Eastern Pima lidar, **March 2015**;
- final closure / three-foot soil cover completed: **December 2016**;
- post surface: `AZ_PimaCo_2_2021`, acquired in **2021**.

Thus the required order is now supported:

`final waste placement -> 2015 pre-lidar -> 2016 cover -> 2021 post-lidar`

## F194 error-budget repair

Frozen screening formula:

`RMSE_diff = sqrt(RMSE_pre^2 + RMSE_post^2)`

and require:

`nominal_target_thickness >= 5 * RMSE_diff`

Inputs:

- 2015 published RMSEz: **0.0976 m**;
- 2021 published non-vegetated vertical accuracy at 95% confidence: **0.107 m**;
- using the same `95% / 1.96` screening conversion already used in F193 gives 2021 screening RMSEz ~= **0.05459 m**;
- combined `RMSE_diff` ~= **0.11183 m**;
- `5 * RMSE_diff` ~= **0.55915 m**;
- nominal three-foot cover = **0.9144 m**.

Result:

**PASS** because `0.9144 m > 0.55915 m` (about 1.64x the frozen minimum).

This is a screening pass only. It is not a measured-depth validation result.

## Exact public elevation projects

Pre:

`USGS_LPC_AZ_Eastern_PimaCO_2015_LAS_2017`

Post:

`AZ_PimaCo_2_2021`

Both are addressed through the USGS public 3DEP Entwine Point Tile convention:

`https://s3-us-west-2.amazonaws.com/usgs-lidar-public/<project>/ept.json`

The execution runner is:

`scripts/tangerine_lidar_execution.py`

It does not modify the app, classifier, NB formula, UI, or production pipeline.

## Execution contract

The runner:

1. creates the same analysis bounds and 1 m grid for both epochs;
2. reads USGS EPT ground-class points only (`Classification = 2`);
3. builds 2015 and 2021 1 m ground DTMs in EPSG:32612;
4. excludes the landfill plus a buffer from stable-ground fitting;
5. searches a bounded sub-pixel XY shift;
6. robustly fits/removes a stable-ground vertical offset and plane;
7. applies the already-frozen residual gates;
8. only if those gates pass, reports the target elevation change descriptively against the nominal 0.9144 m cover.

Frozen residual gates:

- stable-ground RMSE <= **0.15 m**;
- absolute median stable-ground residual <= **0.05 m**;
- 95th percentile absolute stable-ground residual <= **0.30 m**;
- fitted residual-plane drift across the target <= **0.10 m**.

## Interpretation limits

The three-foot value is a **nominal regulatory/design cover thickness**, not an independent measured mean.

The 2021 post surface is roughly five years after December 2016 closure. Settlement may reduce the apparent elevation increase relative to placed cover thickness.

Therefore even a clean execution may initially establish only:

> public before/after lidar can recover an elevation increase reasonably consistent with the nominal cover after controlled co-registration.

It must not be described as agreement with an independently measured mean unless separate as-built thickness measurements are recovered.

## Stop rule

- If the actual stable-ground residual gates fail: **close the free-public-lidar route**; do not launch another site search.
- If the residual gates pass but target change is not interpretable: close Tangerine and the route unless a concrete geometry/settlement correction is already available.
- If the residual gates pass and target change is interpretable: document Tangerine as a public-lidar executable demonstration, with the nominal-vs-measured limitation explicit.

No new candidate search is authorized by F195.
