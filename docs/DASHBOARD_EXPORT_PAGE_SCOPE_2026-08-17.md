# Dashboard and Export Page Scope — 2026-08-17

## Status

Approved product/UI direction.

This document records the required separation between the **Dashboard** and the **Export page**.

## Controlling rule

**Do not remove technical output files.**

The technical/internal output files remain available in the application, but they should be moved out of the main Dashboard download area and presented on the **Export page**.

The Dashboard should be focused on the operator's decision-making workflow rather than displaying every generated artifact.

## Dashboard — required focus

The Dashboard should concentrate on the information the operator needs to understand the run:

1. **Final result / report**
   - overall run result;
   - strongest findings/candidates;
   - clear status and warnings;
   - run quality / usability information.

2. **Classifier results**
   - preferred classifier summary;
   - ranked findings/candidates;
   - candidate score/label information;
   - access to the detailed classifier table when needed.

3. **Candidate/location context**
   - where the important finding is located;
   - enough map/location information to understand what should be reviewed next.

4. **Next action**
   - make it clear whether the operator should review the result, inspect candidate details, export files, or continue to paid imagery.

The Dashboard should not be dominated by raw `.npy`, intermediate rasters, hypercube files, notebook compatibility artifacts, duplicate/deprecated aliases, or other implementation-level outputs.

## Export page — required scope

The Export page should become the place where the operator can obtain **all generated files**, including technical outputs.

Nothing should be deleted merely because it is not a primary Dashboard result.

The Export page should include clear groups such as:

### A. Result and classifier exports
- final/result report files;
- `classifier/summary.json`;
- `classifier/classifications.csv`;
- other preferred classifier outputs.

### B. Location and field exports
- GeoJSON;
- KMZ/KML where available;
- CSV coordinate/location exports;
- field-operation packages.

### C. Paid-imagery handoff exports
Files needed to continue from an app finding to an external paid imagery provider should be grouped clearly.

The intended flow is:

**Result -> classifier finding -> candidate coordinates/AOI -> paid-imagery export package -> imagery provider**

The paid-imagery package should ultimately identify the selected/top candidate rather than forcing the operator to reconstruct the target from internal files.

Where the current implementation only exports the originally entered coordinate/focus area, that limitation must remain explicit until candidate-driven paid-imagery export is implemented.

### D. Technical / advanced outputs
Keep the existing technical files and make them available here, including as applicable:
- `.npy` arrays;
- hypercube artifacts;
- PCA/anomaly outputs;
- intermediate raster products;
- science/feature stacks;
- notebook-parity outputs;
- support layers;
- manifests and QA files;
- deprecated/compatibility aliases that are still intentionally retained.

These should be labeled as **Technical / Advanced Outputs** so they do not distract from the operator's primary result.

## Duplicate / deprecated files

Do not delete compatibility or deprecated copies solely to simplify the Dashboard.

Preferred/current files should be shown first and clearly labeled. Deprecated or compatibility copies can remain accessible on the Export page under an advanced/compatibility grouping.

For classifier results, prefer the files under `classifier/` as the primary outputs. Any `experimental/` copies retained for backward compatibility should not be presented as the main classifier result.

## Paid imagery requirement

The product direction is not merely to preserve a generic imagery-export package. The useful final workflow is candidate-driven:

1. run the analysis;
2. review classifier findings;
3. select the strongest or chosen candidate;
4. obtain that candidate's exact coordinates/AOI;
5. export a paid-imagery handoff package for that candidate;
6. send the package to the imagery provider.

The package should include, as appropriate:
- selected candidate ID;
- selected candidate coordinates;
- AOI geometry in GeoJSON/KMZ or equivalent;
- classifier label/score or summary needed for operator context;
- run ID;
- run manifest/provenance reference;
- clear statement of what imagery area is being requested.

This is separate from numerical depth estimation and must not be described as a depth product.

## Non-goals / protections

- **Do not remove technical outputs.**
- **Do not change or redesign the classifier as part of this UI cleanup.**
- Do not reinterpret notebook-derived proxy layers as physical confirmation.
- Do not hide files required for reproducibility or troubleshooting.
- Do not make the Dashboard a raw artifact browser.

## Acceptance criteria

The UI change is correct when:

1. the Dashboard is visibly focused on result/report, classifier findings, quality, location context, and next action;
2. the existing technical output files have not been deleted;
3. those technical files are reachable from the Export page;
4. preferred classifier outputs are distinguished from deprecated/compatibility copies;
5. paid-imagery exports are easy to find on the Export page;
6. the limitation between original-coordinate export and candidate-driven export is not hidden;
7. no classifier behavior is changed by this work.

## Current requested direction

**Keep the files. Move the technical downloads to the Export page. Make the Dashboard more focused.**
