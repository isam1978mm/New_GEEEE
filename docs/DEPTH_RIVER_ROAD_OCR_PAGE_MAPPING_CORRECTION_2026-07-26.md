# River Road Landfill — OCR Page-Mapping Correction

Date: 2026-07-26

## Decision

**Status:** River Road remains the strongest measured-point candidate, but it still adds zero usable calibration rows.

This addendum corrects the earlier assumption that Appendix A could be isolated as a simple `AR304840–AR304889` page block. The searchable EPA OCR does not prove that window contains the individual pit-depth field reports or Sheet 1. Future work must not treat that range as verified.

## Newly confirmed from EPA document 91025HWW

- `AR304820` begins Part 1, Section 1, Closure Certification.
- `AR304821` states that 129 cover-certification pits were excavated and that Sheet 1 of 3 shows their surveyed locations.
- The same page states that Appendix A field reports contain the final cover thickness for each pit.
- Deficient areas were corrected and re-certified using overlapping pits and/or documented visual inspection.
- `AR304822` contains Table 1, the **Textural Classification Summary**.
- Table 1 maps pit-number groups to soil-composite identifiers `RR1` through `RR15` and reports coarse-fragment, sand, silt, clay, and USDA soil-classification results.
- Table 1 does **not** report cover depth and must never be used as a depth label.
- `AR304830–AR304831` contain the professional facility-design and construction certification.
- The certification identifies the closure as constructed in accordance with the approved application, documents, designs, and plans.
- The closure package records surveying support by Kurtanich Engineers and Associates and QA/QC engineering certification by Todd Giddings and Associates.
- Permit language requires the horizontal grid-control system to be tied to a permanent physical marker on site.
- No numerical horizontal tolerance, vertical tolerance, pit-depth reading precision, or finite uncertainty interval has been recovered.

## Table 1 pit-group mapping

The following is useful only for locating soil-composite records; it is not depth evidence:

```text
pits 1-12     -> RR1
pits 13-24    -> RR2
pits 28-35    -> RR3
pits 36-48    -> RR4
pits 49-53    -> RR5
pits 54-68    -> RR6
pits 78-89    -> RR7
pits 68B-77A and 117-118 -> RR8
pits 110-116  -> RR9
pits 100-109  -> RR10
pits 90-99    -> RR11
pits 119-121  -> RR12
pits 122-124  -> RR13
pits 125-127  -> RR14
pits 128-129  -> RR15
```

The OCR appears imperfect around the `RR8` grouping, so the original page image must be checked before recording that mapping as authoritative.

## What remains missing

1. Individual final accepted cover-thickness values for the 129 pits.
2. Identification of original failures versus final re-certification measurements.
3. Sheet 1 of 3 with pit identifiers and surveyed locations.
4. Coordinate reference system, datum, and numerical survey precision.
5. Numerical pit-depth measurement uncertainty or a documented finite two-sided interval.
6. A point-by-point overlay excluding the southeast knob, channels, berms, roads, leachate and gas infrastructure, monitoring points, and later maintenance areas.
7. Evidence that each retained pit neighborhood was unchanged during the chosen Sentinel-1 observation interval.

## Correct extraction target

Do not use an assumed archive-page window as if it were verified. The next extraction attempt must locate the actual page images by one of these anchors:

- heading `APPENDIX A — FIELD REPORTS`;
- a Todd Giddings and Associates field-report form containing a pit identifier and final cover thickness;
- plan-sheet title `FINAL COVER CERTIFICATION`, Sheet 1 of 3;
- document key `91025HWW`.

Only page images that visibly contain those anchors can be used to extract depth or geometry.

## Readiness impact

```text
usable_calibration_rows_added = 0
numerical_depth_ready = no
strongest_measured_point_candidate = River_Road_Landfill
next_blocker = image_only_pit_forms_map_and_numerical_uncertainty
```

## Public evidence reviewed

- EPA NEPIS document key `91025HWW`, River Road Landfill Record of Decision with embedded 1987 Closure Certification and Post-Closure Plan.
- Closure Certification narrative at archive pages `AR304820–AR304831`.
- Table 1 Textural Classification Summary at `AR304822`.
- Pennsylvania solid-waste permit conditions embedded in the same EPA record.
