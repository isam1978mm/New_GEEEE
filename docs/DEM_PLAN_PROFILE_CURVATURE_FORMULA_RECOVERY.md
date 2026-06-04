# DEM Plan/Profile Curvature Formula Recovery

## 1. Purpose

Phase 4D3 locks the recovery status for two notebook DEM curvature outputs:

```text
curv_plan_640.tif
curv_profile_640.tif
```

The purpose is to determine what evidence is still required before a later implementation slice can safely reproduce these notebook outputs. Faithful notebook-to-Python-app conversion remains the objective, but this phase is investigation and contract only.

## 2. Scope

Phase 4D3 covers:

- source inspection;
- formula evidence classification;
- required reference artifacts;
- required metadata expectations;
- numeric verification requirements;
- a machine-readable checklist/report helper.

Files inspected:

```text
notebook_gaps_coverage.md
gaps.md
docs/DEM_CURVATURE_PARITY_RECONSTRUCTION.md
docs/DEM_CURV_LAPLACIAN_PARITY_VERIFICATION_CONTRACT.md
app/pipeline/parity/dem_curvature_reconstruction.py
app/pipeline/stages/dem_derivatives.py
app/pipeline/stages/feature_stacks.py
notebooks/new.ipynb
```

`Notebook cells.md` was not present at repository root. The source notebook reference available in the repo is `notebooks/new.ipynb`.

## 3. Non-Goals

Phase 4D3 does not:

- implement plan curvature;
- implement profile curvature;
- change DEM formulas;
- change raster math;
- generate rasters;
- create aliases;
- call Earth Engine;
- integrate with the live pipeline;
- change API, frontend, database, migrations, classifier logic, or artifact serving;
- decide public/shared exposure.

No formulas were implemented in Phase 4D3.

## 4. Current Status From Phase 4D

Phase 4D recorded:

| Output | Current app status | Formula status in Phase 4D | Runtime verified | Notebook-value parity verified |
| --- | --- | --- | --- | --- |
| `curv_plan_640.tif` | No separate app writer found. | `no_formula_found` from inspected summary docs/source at that time. | false | false |
| `curv_profile_640.tif` | No separate app writer found. | `no_formula_found` from inspected summary docs/source at that time. | false | false |

Phase 4D3 additionally inspected `notebooks/new.ipynb` directly and found notebook-source formula text for both plan and profile curvature. That changes the formula recovery status to:

```text
authoritative_formula_found
```

It does not change runtime or notebook-value parity status.

## 5. Evidence Needed Before Implementation

The following evidence is still required before implementation can be attempted safely:

- frozen notebook reference output `DEM_GEO8_TIFS/curv_plan_640.tif`;
- frozen notebook reference output `DEM_GEO8_TIFS/curv_profile_640.tif`;
- locked reference metadata for both outputs;
- numeric tolerance contract for comparison;
- confirmation of `save_tif` filename suffix behavior in the target reference bundle;
- confirmation of nodata handling and NaN conversion;
- confirmation of sign convention and scaling/normalization from reference outputs.

File existence is not parity proof. Formula text alone is not notebook-value parity proof.

## 6. Candidate Non-Authoritative GIS Formulas

No generic GIS convention formula is adopted in Phase 4D3.

The formulas below are not from memory and are not an implementation. They are copied as notebook-source evidence from `notebooks/new.ipynb` around the DEM curvature export cells:

```text
p, q = dz_dx, dz_dy
r, s, t = d2z_dxx, d2z_dxy, d2z_dyy
den = (p*p + q*q + 1.0)
den_sqrt = np.sqrt(den)
den_3_2 = den * den_sqrt

curv_profile = - (r*p*p + 2*s*p*q + t*q*q) / (den_3_2 + 1e-12)
curv_plan = (r*q*q - 2*s*p*q + t*p*p) / ((p*p + q*q + 1e-12) * (den_sqrt + 1e-12))
```

Because these equations were found in the source notebook, they are treated as authoritative notebook formula evidence. They are still not enough to implement parity until frozen output references and metadata expectations are locked.

## 7. Required Frozen Notebook Artifacts

Required reference files:

```text
DEM_GEO8_TIFS/curv_plan_640.tif
DEM_GEO8_TIFS/curv_profile_640.tif
```

The reference bundle must preserve original notebook names. If the local notebook saved intermediate names before suffixing, the final reference filenames must still resolve to the notebook parity filenames above.

## 8. Required Notebook Source Lines/Cells

Notebook source evidence found:

```text
notebooks/new.ipynb around lines 25376-25405
notebooks/new.ipynb around lines 26044-26072
```

The two regions contain the same plan/profile formula family and save calls:

```text
save_tif("curv_profile", curv_profile)
save_tif("curv_plan", curv_plan)
```

A later implementation slice should cite these notebook regions and the frozen reference output bundle together. Source lines without reference output comparison are not enough to mark notebook-value parity true.

## 9. Required Metadata Expectations

Each frozen reference output must lock:

- CRS;
- transform;
- pixel size;
- units;
- nodata;
- dtype;
- sign convention;
- scaling/normalization.

The notebook source references the master grid and a `PIX` cell size. The later implementation must verify the final reference outputs rather than assuming metadata from source code alone.

## 10. Required Numeric Verification Plan

A later verifier or implementation test must compare:

- width;
- height;
- CRS;
- transform;
- dtype;
- nodata;
- band count;
- max absolute difference;
- mean absolute difference;
- compared pixel count;
- nodata or NaN pixel count;
- within-tolerance status.

`notebook_value_parity_verified=true` is allowed only after frozen reference comparison passes.

## 11. Why App `curvature.tif` Cannot Be Reused

The current app `curvature.tif` is a Laplacian-style curvature candidate:

```text
d2z_dxx + d2z_dyy
```

Plan and profile curvature are distinct directional curvature formulas using first derivatives, mixed second derivatives, denominator terms, and sign convention. The app's single `curvature.tif` cannot be reused for:

```text
curv_plan_640.tif
curv_profile_640.tif
```

Reusing it would fabricate notebook outputs and would erase the distinction the notebook preserves.

## 12. Recommended Implementation Gate

A later implementation phase may begin only after:

1. source formula evidence is cited from `notebooks/new.ipynb`;
2. frozen reference outputs for `curv_plan_640.tif` and `curv_profile_640.tif` are available;
3. metadata expectations are locked;
4. numeric tolerance expectations are locked;
5. tests are written against small deterministic arrays and frozen reference fixtures or a reference-comparison harness;
6. implementation remains confined to notebook parity mode until public/shared exposure is separately decided.

Current machine-readable status:

| Output | Formula status | Authoritative formula found | Implementation status |
| --- | --- | --- | --- |
| `curv_plan_640.tif` | `authoritative_formula_found` | true | `blocked_missing_reference_output` |
| `curv_profile_640.tif` | `authoritative_formula_found` | true | `blocked_missing_reference_output` |

## 13. Confirmation No Formulas Were Implemented

Phase 4D3 added only a recovery contract, checklist/report helper, and tests. It did not implement plan curvature, profile curvature, raster generation, aliases, Earth Engine calls, or pipeline integration.
