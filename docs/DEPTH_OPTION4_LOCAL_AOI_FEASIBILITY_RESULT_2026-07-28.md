# Option 4 — Local AOI calibration feasibility result — 2026-07-28

## Decision

**NOT READY TO RUN**

A bounded Option 4 feasibility check was completed using the strongest existing public candidates. No current candidate supplies the complete local calibration package required inside one AOI:

1. one measured shallow numerical reference;
2. one measured deeper numerical reference;
3. one confirmed control area;
4. coordinate-tied polygons;
5. comparable radar-facing surfaces;
6. enough clean Sentinel-1 support;
7. a stable observation period.

No Earth Engine query was run. No calibration package was created. No training or app change occurred.

## Candidate 1 — Tyrone Dam 3X

### What passes

- Test Plot 5 final measured mean: 26.8 inches, 95% interval 25.8–27.8 inches.
- Test Plot 6 final measured mean: 37.4 inches, 95% interval 33.5–41.3 inches.
- Both plots are large and use the same cover-material and revegetation program.

### What fails

- No official untreated or zero-cover control plot is defined.
- The report's reference to uncovered slopes is only a study objective; every named test plot has a constructed cover.
- Exact GIS/CAD/survey polygons and a plot-specific stable Sentinel-1 period remain unavailable.
- EMNRD request N000019-070026 is still pending for the missing survey and stability records.

Tyrone therefore cannot form an Option 4 package now, even though it has the strongest measured shallow/deep pair.

## Candidate 2 — Sconondoa Phase 3

### What passes

- A measured shallow zone in Cell A has mean excavation depth 3.511 m.
- A measured deeper zone across Cells B/C has mean excavation depth 4.881 m.
- Cells A, B and C received the same documented final surface assembly: woven geotextile, 8 inches compacted run-of-bank gravel and 4 inches crushed stone.
- An official 2022 NYS ortho overlay was created for placement review.

### What fails

- The selected zones have minimum dimensions only about 21.1 m and 23.2 m, below the preferred 30–40 m clean width.
- The georeference remains provisional rather than an authoritative survey transformation.
- The official Final Engineering Report does not designate a control area or an unexcavated area with the same restored surface.
- Areas outside the selected cells cannot be assumed to be controls because Phase 3 also included adjacent off-site work and multiple restored surfaces.

Sconondoa therefore cannot form a defensible Option 4 package from current public records.

## Plain-English conclusion

Option 4 does not mean the user must search alone. The public evidence was tested first. The attempt failed because public records do not currently provide all three local references inside one AOI.

Option 4 can reopen only when one specific AOI supplies:

- measured shallow and deep polygons;
- a confirmed control polygon;
- exact coordinates;
- comparable surfaces;
- sufficient clean pixel support;
- a stable observation window.

## Current status

```text
Option 4 = tested, not ready
local AOI selected = no
complete three-zone package = no
Earth Engine query executed = no
calibration package created = no
training started = no
app depth enabled = no
numerical depth ready = no
```

## Next action

Wait for the Tyrone EMNRD response. If it provides exact plot geometry and stability records, check whether it also identifies a defensible control area. Otherwise Option 4 requires a real operator-provided AOI package and cannot proceed from the current public evidence.
