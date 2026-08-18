# Candidate-Driven Focus — 17 m Geometry Decision

Date: 2026-08-17  
Status: **DECIDED FOR THIS IMPLEMENTATION**

## Why this decision was required

`docs/next/NEXT_FEATURE_CANDIDATE_DRIVEN_FOCUS_2026-08-17.md` identified a geometry discrepancy that had to be resolved before Candidate Focus was implemented:

- the current app uses a circular Focus mask with a **17 m radius** (34 m diameter);
- the available `new` notebook phase description describes `FOCUS_MASK_17M` as approximately **17 m × 17 m**.

The feature plan explicitly prohibited silently choosing one interpretation.

## Evidence reviewed

### Current app implementation

`app/pipeline/stages/focus_mask.py` defines:

- `FOCUS_RADIUS_M = 17.0`;
- a circular Euclidean-distance mask;
- `focus_diameter_m = 34.0`;
- the contract `circular_mask_radius_m_centered_on_authoritative_grid`.

`tests/unit/test_focus_mask.py` already locks this behavior. On the authoritative 10 m grid, the centered 17 m-radius mask contains 9 pixels.

### Available notebook material

The project-provided notebook phase inventory describes:

- cell 119 as ROI-constrained analysis inside a `17m FOCUS`, described there as approximately `17 m × 17 m`;
- cell 141 as a `17M MASK REBUILDER`;
- cell 196 as defining `Focus_ROI_17m` from the selected point.

However, the exact Tesla-v7.2 source cell that constructs `FOCUS_MASK_17M` is not present in the repository material available to this implementation. The separate uploaded candidate-scout notebook does not contain `FOCUS_MASK_17M` and therefore cannot resolve the Tesla-v7.2 geometry.

## Decision

For Candidate Focus, **do not change the existing User Focus geometry**.

The operational contract for this feature is:

- **User Focus:** keep the current circular **17 m radius** mask unchanged;
- **Candidate Focus:** use the same circular **17 m radius** mask, centered on each selected candidate;
- **diameter:** 34 m;
- **candidate geometry contract:** `circular_mask_radius_m_centered_on_ranked_candidate`.

This is a deliberate backward-compatible implementation decision. It is **not** a claim that the unavailable Tesla-v7.2 source cell has been proven to use a 17 m radius.

If the exact notebook cell is later supplied and proves a different geometry such as a 17 m × 17 m square, changing the existing app geometry must be handled as a separate explicit parity migration with its own approval and regression tests.

## Why this is the safest choice now

1. It preserves the current user-coordinate Focus behavior exactly as required by the feature plan.
2. It avoids silently changing an already-tested production contract.
3. Candidate Focus uses the same detailed Focus footprint as User Focus, so the two result families remain directly comparable.
4. The unresolved notebook-source limitation is documented rather than hidden.

## Tests that enforce the decision

Candidate Focus tests must assert:

- `FOCUS_RADIUS_M == 17.0`;
- a centered 17 m-radius mask on the 10 m grid keeps the existing 9-pixel contract;
- Candidate Focus summaries report `focus_radius_m = 17.0` and `focus_diameter_m = 34.0`;
- User Focus remains untouched;
- classifier behavior remains untouched.
