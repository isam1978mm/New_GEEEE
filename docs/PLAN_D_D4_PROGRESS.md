# Plan D D4 Progress

## Scope

Private/local REPORT_640 and thermal-scaling reliability work.

This is not a public-safe redaction track. The goal is to improve local output correctness, reduce contradictory report products, and document formulas clearly.

## Completed

```text
D4.5 partial:
  - Normal private/local REPORT_640_Mass_Report now scales Landsat Collection 2 ST_B10 raw DN to Kelvin before mass calculation.
  - Added scale_st_b10_to_kelvin helper using Kelvin = 0.00341802 * DN + 149.0.
  - Kept explicit notebook mass fetcher behavior separate as legacy notebook provenance.

D4.4 partial:
  - REPORT_640 manifest now records source_family, formula_version, parity_category, and correction_reason for implemented reports.
  - Mass report metadata identifies the corrected private-local formula.
```

## Still open from D4

```text
D4.1 choose one canonical owner for REPORT_640 products.
D4.2 rename fusion-derived outputs if they are kept.
D4.3 rebuild or rename REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy so name and formula match.
D4.6 apply thermal QA masking consistently across all thermal consumers.
D4.7 inspect/fix Zero_Point thermal condition if thermal thresholds exist elsewhere.
D4.8 inspect/fix AIX thermal Norm01 raw-DN scaling.
D4.9 use DEM mosaic for AIX terrain products.
```

## Private-local policy

```text
Do not remove useful REPORT_640 outputs for public-safe reasons.
Prefer corrected local formulas and clear manifest provenance over hiding outputs.
Keep legacy notebook behavior only when explicitly requested or injected as a compatibility path.
```
