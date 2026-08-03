# ICESat-2 cycle-pair independence audit

Status: read-only validation gate; no depth, calibration, or app-unblock claim.

## Why this gate exists

The ATL08 repeat audit found 128 colocated 100 m segments with a measured NMAD
of about 0.054 m.  That is promising, but the preview shows adjacent segments
from the same early and late satellite passes.  Adjacent segments are spatial
samples; they are not independent acquisitions and can share a pass-level
vertical offset.

This audit rebuilds the comparison separately for every actual combination of:

- reference ground track;
- detector spot;
- early ICESat-2 cycle;
- late ICESat-2 cycle.

A single precise cycle pair is reported as such.  It is not promoted to
multi-epoch repeatability.

## Run

```powershell
cd C:\Dev\New_GEE_depth
git pull

cd C:\Dev\New_GEE
.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\audit_icesat2_cycle_independence.py `
  --run-dir .\data\runs\a4881db6-d92e-4ebc-b628-8a1b089db20b `
  --target-m 0.7
```

The script prints JSON and writes nothing to the run.

## Decision rule

Each cycle-pair cohort must independently contain at least 30 colocated segments
within 5 m or 10 m and have a measured 95% detection floor at or below the
requested target.

`multi_epoch_repeatability_supported` becomes true only when passing cohorts
include at least:

- two different early cycles; and
- two different late cycles.

This prevents one long laser track from being misreported as hundreds of
independent validations.

## What a pass would mean

A pass means ICESat-2 has repeatable relative elevation precision at this AOI
across more than one pair of acquisitions.

It still does not establish:

- that an ICESat-2 track crosses the actual feature whose thickness is needed;
- that the early and late observations bracket material placement;
- that a 100 m ATL08 segment is fully covered by the changed feature;
- placed-material thickness;
- depth to a buried object;
- Sentinel-1 depth prediction.

Target intersection and event timing remain separate required gates.
