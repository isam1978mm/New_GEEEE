# River Road Landfill — NEPIS OCR Access Addendum

Date: 2026-07-25

## Decision

**Status:** River Road remains the strongest measured-point candidate, but no calibration row can be added.

A targeted search found that EPA's searchable Record of Decision package contains the full 1987 Closure Certification and Post-Closure Plan as Appendix C. This is stronger than relying on a later summary because the original engineering narrative, professional certification, test-pit grouping, and archive-page sequence are publicly traceable in one EPA document.

The decisive pit-by-pit forms and surveyed Sheet 1 still could not be extracted. The text interface exposes the typed narrative and laboratory summaries, but the intervening field-report and drawing block is not text-searchable enough to recover the handwritten or image-based values.

## Exact public document key

```text
EPA NEPIS document key = 91025HWW
Document title = Superfund Record of Decision: River Road Landfill / Waste Management, Inc., Pennsylvania
Embedded evidence = Appendix C, 1987 Closure Certification and Post-Closure Plan
```

## What this pass confirmed directly from the original package

- The closure certification begins at archive page marker approximately `AR304809`.
- The main closure narrative and professional certification are readable around archive markers `AR304820` through `AR304831`.
- The narrative states that:
  - a minimum three-foot final cover was emplaced;
  - 129 cover-certification pits were excavated;
  - Sheet 1 of 3 shows their surveyed locations;
  - Appendix A field reports record the final cover thickness for each pit;
  - deficient areas were corrected and re-certified using overlapping pits and/or documented visual inspection;
  - the extreme southeast knob of less than one acre was not investigated.
- The pit groups used for soil composites are visible in the typed tables and cover the numbered sequence through pit 129, including revised or lettered identifiers in corrected areas.
- A registered professional engineer certified on September 30, 1987 that the facility was constructed and prepared in accordance with the approved documents and plans.
- The package identifies Kurtanich Engineers and Associates as providing surveying support and Todd Giddings and Associates as providing construction management, engineering inspection, QA/QC, and certification.
- Later OCR-readable permit records begin around the upper `AR3048xx` pages, while the field-report and drawing contents between the typed sections remain inaccessible as usable text.

## Why this still does not create a calibration row

1. The actual final accepted thickness for each pit remains unreadable.
2. The surveyed Sheet 1 point geometry remains unreadable.
3. Corrected pits cannot be separated reliably from their initial failed measurements.
4. The field forms' measurement endpoint and units cannot be verified point by point.
5. No numerical measurement uncertainty or survey tolerance has been recovered.
6. A certified minimum of three feet is not a substitute for a point-specific measured depth.
7. No unseen drawing geometry or handwritten value may be inferred from the OCR gaps.

## Required extraction target

A future successful extraction should retrieve only:

```text
Appendix A field-report pages
Final Cover Certification — Sheet 1 of 3
Survey notes and legend
```

For each pit, the private evidence pack must capture the final accepted reading, pit identifier, survey location, measurement date, re-certification status, measurement endpoint, and numerical uncertainty.

## Readiness impact

```text
usable_calibration_rows_added = 0
numerical_depth_ready = no
river_road_status = strongest_candidate_blocked_by_image_only_pit_forms_and_map
```
