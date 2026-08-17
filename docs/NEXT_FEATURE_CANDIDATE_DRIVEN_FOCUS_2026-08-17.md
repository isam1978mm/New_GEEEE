# Next Feature — Candidate-Driven Focus Analysis

Date: 2026-08-17  
Status: **PLANNED / NOT IMPLEMENTED**  
Target branch: `main`

## Purpose

Improve the current focus-analysis design without removing the existing user-coordinate focus.

Today, the user-provided coordinate serves two roles:

1. it is the center of the full 6.4 km × 6.4 km analysis grid; and
2. it is also the center of the current 17 m-radius Focus analysis.

This is useful when the user already knows the exact point that should be investigated. It is less useful when the entered coordinate is only a general search center and the strongest anomaly is located elsewhere inside the 6.4 km × 6.4 km scene.

## Planned feature

Keep the existing user-coordinate Focus analysis, and add automatic **candidate-driven focus zones** after whole-scene anomaly/object analysis.

Target flow:

```text
User coordinate
    ↓
6.4 km × 6.4 km full-scene analysis
    ↓
PCA / anomaly analysis
    ↓
Object extraction + candidate ranking
    ↓
┌─────────────────────────┬──────────────────────────┐
│ User Focus              │ Candidate Focus         │
│ original coordinate     │ strongest candidates   │
│ preserve current logic  │ found anywhere in scene│
└─────────────────────────┴──────────────────────────┘
```

## Required behavior

### 1. Preserve User Focus

The coordinate entered by the user must continue to receive its own detailed Focus report.

This keeps the existing use case:

> "I already suspect this exact location; inspect it closely."

### 2. Add Candidate Focus

After the full-area PCA/anomaly/object stages identify candidates, the app should automatically select the highest-priority candidates and run the same or equivalent detailed Focus analysis around those candidate coordinates.

Initial target behavior:

- rank candidates from the existing whole-scene outputs;
- select a small configurable number of top candidates, for example Top 3;
- create one focus zone around each selected candidate;
- preserve candidate ID and coordinates through every focus output;
- do not replace or move the user-selected focus point.

### 3. Final report structure

The final report should clearly separate:

**A. User-selected location**

- original input coordinate;
- detailed focus findings for that point.

**B. Best candidates in the full 6.4 km × 6.4 km scene**

For each selected candidate:

- candidate ID;
- latitude/longitude and/or authoritative projected coordinates;
- ranking/score used for selection;
- detailed focus-layer summaries;
- relevant anomaly/object/classifier context;
- warnings that anomaly/classifier values are screening evidence, not physical confirmation.

## Important implementation constraint

This feature must use the existing classifier outputs as inputs only.

**Do not change classifier formulas, thresholds, labels, or behavior as part of this feature unless a separate explicit approval is given.**

The feature is an orchestration/reporting/focus-selection enhancement, not a classifier redesign.

## 17 m focus-size parity check

Before implementation, resolve the naming/geometry discrepancy between the notebook description and the current app:

- current app Focus implementation uses a **17 m radius**, which gives a **34 m diameter** circle;
- the `new` notebook phase description has referred to `FOCUS_MASK_17M` as approximately **17 m × 17 m**.

Do not silently choose one interpretation. Verify the actual notebook geometry and document the parity decision before changing the app.

## Non-goals

This feature does **not**:

- claim that an anomaly is a confirmed underground object;
- turn Sentinel-1/Sentinel-2/DEM/thermal data into direct physical confirmation;
- add numerical physical depth estimation;
- change the classifier;
- remove the current user-coordinate focus report.

## Acceptance criteria

The feature is complete only when:

1. the original user coordinate still receives a Focus report;
2. the full 6.4 km × 6.4 km scene is still analyzed normally;
3. top candidates can be selected from existing whole-scene results;
4. each selected candidate receives its own detailed focus analysis;
5. user focus and candidate focus outputs are clearly distinguished in artifacts/API/UI;
6. candidate IDs and coordinates remain traceable to the source object/candidate;
7. the 17 m geometry/parity decision is documented and tested;
8. classifier behavior is unchanged unless separately approved;
9. scientific warnings remain explicit: candidate/anomaly scores are not physical confirmation.

## Priority

**Next-feature candidate.**

Recommended implementation order:

1. verify the notebook's actual `FOCUS_MASK_17M` geometry;
2. define candidate-selection/ranking contract using current outputs;
3. make Focus processing accept an explicit center coordinate/candidate ID instead of only the original grid center;
4. run Focus once for the user point and separately for selected candidates;
5. add report/API/UI separation between User Focus and Candidate Focus;
6. add regression tests proving existing classifier behavior is untouched.
