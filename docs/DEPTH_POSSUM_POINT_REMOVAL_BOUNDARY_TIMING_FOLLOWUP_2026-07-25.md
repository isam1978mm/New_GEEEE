# Possum Point Removal Boundary and Timing Follow-up — 2026-07-25

**Branch:** `main`  
**Status:** complete CCR removal confirmed; exact public geometry and clean observation timing fail  
**Calibration rows created:** 0

## Plain-English result

Possum Point Ponds A, B, C, and E are strongly documented closure-by-removal areas. Official Dominion records establish that:

- all CCR was removed from Ponds ABC and E;
- at least six inches of underlying soil was additionally excavated;
- Virginia DEQ verified the removal work in 2019;
- the closure plan uses NAVD 88 elevations;
- Ponds ABC covered about 15.7 acres;
- Pond E covered about 39.2 acres.

This is strong physical evidence that the former pond areas no longer contained CCR.

It is still not enough for a calibration row.

## Exact-boundary problem

The official Dominion index publicly lists:

- Ponds ABC Location Restrictions;
- Ponds ABC History of Construction;
- Ponds ABC Closure Plan;
- Pond E Location Restrictions;
- Pond E History of Construction;
- Pond E Closure Plan.

The one-page location-restriction certification and searchable closure-plan text were recovered. The coordinate-bearing drawing sheets were not recoverable through either the Dominion CDN reader or the Virginia DEQ document viewer during this bounded search.

The published acreage values and unit names do not by themselves define a survey-grade calibration polygon. No private geometry was created.

## Timing and surface-use problem

The post-removal surfaces are not clean, untouched comparison areas:

- Pond E currently functions as a stormwater-management pond;
- water entering Pond E is pumped to active Pond D;
- the Pond E embankment was breached and the unit remains managed because of groundwater impacts;
- Ponds ABC remain subject to periodic structural and engineering inspection;
- a 2023 assessment recorded erosion on part of the Ponds ABC embankment;
- the station and its CCR-management work remain active.

Therefore the radar signal cannot safely be interpreted as a stable empty-ground control without substantial surface-use confounding.

## Current classification

```text
physical_CCR_removal_confirmed = yes
minimum_over_excavation_m = 0.1524
regulator_verification = yes
exact_public_geometry = no
post_removal_surface_untouched = no
clean_sentinel1_window_verified = no
eligible_negative_calibration_row = no
```

## Decision

Close Possum Point as a numerical-depth calibration route. Do not digitize acreage or approximate pond outlines as exact geometry, and do not treat an active stormwater pond or managed embankment as an unchanged empty comparison area.

## Next bounded action

Search only for a completed closure-by-removal site that has all three of the following publicly available together:

1. a final survey or coordinate-bearing as-built boundary;
2. regulator-confirmed removal or clean native-soil verification;
3. a later stable surface period without active pond, drainage, construction, or redevelopment use.
