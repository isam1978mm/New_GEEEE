# GEDI point precision audit

Status: read-only precision audit; no depth or calibration claim.

## Purpose

The point-pair audit proved that real early and late GEDI footprints exist at
one run. This follow-up checks whether their measured spread is small enough for
a 0.7 m target.

A raw repeat-point difference is not purely temporal change when the two
footprint centres are several metres apart. On sloping ground, one footprint may
simply be uphill or downhill from the other. The audit therefore reports:

- raw late-minus-early GEDI elevation;
- the same value after subtracting the static TanDEM-X elevation difference;
- the same value after subtracting the static SRTM elevation difference;
- separate robust spreads for pairs within 5, 10, 15 and 25 m.

The two DEMs are used only to remove the first-order terrain-offset term. They
are not treated as time epochs and do not create a depth measurement.

## Run

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE
.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\audit_gedi_point_precision.py `
  --run-dir .\data\runs\a4881db6-d92e-4ebc-b628-8a1b089db20b `
  --target-m 0.7
```

## Decision rule

The audit marks the route ready for a point-change prototype only when both the
TanDEM-X- and SRTM-corrected 95% detection floors are at or below the target in
the same 5 m or 10 m band, with at least 30 usable pairs.

Passing that rule would still not prove placed-material thickness. The dates
must bracket a known event and the paired points must fall on the target area.
