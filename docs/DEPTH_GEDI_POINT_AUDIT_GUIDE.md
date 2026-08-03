# GEDI point audit — controlling guide

Status: read-only audit implemented; no depth or calibration claim.

## Why this exists

`scripts/check_laser_altimetry_coverage.py` uses the monthly raster product. Its
fractional sums are useful only for ranking AOIs and estimating how sparse GEDI
coverage is. They are not counts of individual shots and cannot prove that an
early footprint and a late footprint measured the same place.

The point audit uses the official vector-table index:

`LARSE/GEDI/GEDI02_A_002_INDEX`

It loads only the L2A vector tables intersecting one run AOI.

## Run it

```powershell
cd C:\Dev\New_GEE
.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\audit_gedi_point_pairs.py `
  --run-dir .\data\runs\a4881db6-d92e-4ebc-b628-8a1b089db20b
```

The script reads Earth Engine and prints JSON. It does not write to the run,
create zones, invoke the depth engine, or change the frontend.

## Quality filters

Only shots satisfying all of these are retained:

- `quality_flag == 1`
- `degrade_flag == 0`
- `elevation_bias_flag == 0`
- `surface_flag == 1`
- `0 <= sensitivity <= 1`
- non-null `delta_time`, `elev_lowestmode`, and `shot_number`

## Pairing rule

The early/late boundary defaults to `2022-01-01`.

A pair is accepted only when:

1. the late shot is the nearest late neighbour of the early shot;
2. the early shot is also the nearest early neighbour of that late shot;
3. their separation is within the requested maximum, default 25 m.

This reciprocal rule prevents one footprint from being reused in several
apparent pairs.

## Output

The JSON reports:

- integer early and late shot counts;
- exact earliest and latest observation timestamps;
- unique dates, orbits, and beams;
- reciprocal pair counts within 5, 10, 15, and 25 m;
- the number of occupied 100 m midpoint bins;
- raw late-minus-early elevation-change statistics;
- a preview containing exact shot IDs, dates, coordinates, elevations, beams,
  orbits, source table IDs, separation, and elevation difference.

## Interpretation

`possible_point_change_test` means only that at least one quality-filtered,
reciprocal early/late pair exists within 25 m.

It does **not** prove:

- placed-material thickness;
- depth to a buried object;
- sub-metre accuracy;
- that observations bracket a construction event;
- that GEDI sampling is dense enough over a particular target;
- that radar predicts depth.

The monthly-raster screen already indicates that these AOIs have very sparse
coverage over their full area. The point audit is the decisive check of whether
any real repeated footprints exist at all and where they are.
