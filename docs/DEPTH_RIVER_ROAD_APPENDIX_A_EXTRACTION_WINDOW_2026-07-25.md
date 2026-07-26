# River Road Landfill — Appendix A Extraction Window

Date: 2026-07-25

## Decision

**Status:** highest-priority measured-depth candidate; no usable calibration row yet.

The public EPA OCR record confirms that the full 1987 Closure Certification and Post-Closure Plan is embedded in document key `91025HWW`. The text layer proves that 129 final-cover certification pits were excavated, their locations were surveyed, and Appendix A contains pit-by-pit final cover thickness field reports. It also proves that deficient areas were corrected and re-certified.

The remaining evidence is image-only. The readable narrative reaches approximately archive page `AR304839`, while later permit records resume near `AR304890`. Appendix A field forms and the final-cover plan sheets are therefore expected inside this roughly fifty-page scanned block. Individual pit values and mapped locations have not been read and must not be guessed.

## New facts confirmed in this pass

- EPA document key: `91025HWW`.
- Closure package begins near archive page `AR304809`.
- Closure narrative identifies:
  - 129 certification pits;
  - approximately two pits per acre;
  - final cover minimum of three feet;
  - surveyed pit locations on Final Cover Certification, Sheet 1 of 3;
  - pit-specific thickness values in Appendix A;
  - re-certification of deficient areas.
- The text layer contains the pit grouping used for soil composites:
  - pits 1–12;
  - 13–24;
  - 28–35;
  - 36–48;
  - 49–53;
  - 54–68;
  - 68B–77A;
  - 78–89;
  - 90–99;
  - 100–109;
  - 110–116;
  - 117–118;
  - 119–121;
  - 122–124;
  - 125–127;
  - 128–129.
- Appendix A and the plan-sheet block appear to lie after the professionally signed construction certification around `AR304839` and before permit material around `AR304890`.
- Repeated searches for individual archive markers inside that block returned no separately indexed pages.
- A secondary PDF renderer was tested but required user login and could not be used.

## Why no row can be created

1. Individual final accepted pit depths remain unreadable.
2. Sheet 1 of 3 remains unreadable.
3. Point coordinates and coordinate reference system remain unknown.
4. Failed initial pits cannot be distinguished from final re-certification pits.
5. Measurement uncertainty and survey tolerance remain undocumented.
6. The three-foot requirement is only a minimum and cannot substitute for actual values.

## Exact next extraction target

Use the original EPA PDF for document key `91025HWW` and render only the scanned archive block approximately spanning `AR304840` through `AR304889`.

Priority order:

1. Appendix A field-report pages containing pit identifier and accepted final thickness.
2. Final Cover Certification, Sheet 1 of 3, containing surveyed pit locations and survey notes.
3. Any legend, datum, benchmark, scale, northing/easting, or accuracy statement.
4. Re-certification notes showing which initial failures were corrected.

## Current readiness impact

```text
usable_calibration_rows_added = 0
numerical_depth_ready = no
strongest_candidate = River_Road_Landfill
remaining_blocker = image_only_appendix_and_survey_sheet
```

## Public evidence reviewed

- EPA NEPIS text record for document key `91025HWW`.
- Embedded 1987 Closure Certification and Post-Closure Plan.
- Closure narrative, professional engineer certification, table of contents, soil-composite table, and archive page markers.
