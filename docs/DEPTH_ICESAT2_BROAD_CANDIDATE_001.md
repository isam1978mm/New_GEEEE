# ICESat-2 broad candidate 001

Status: active targeted verification candidate; not a depth anchor.

## Detection

Campaign:

```text
southwest_us_earthwork_pilot_v1
```

Region:

```text
las_vegas_henderson_pilot
```

Candidate evidence from the completed broad scan:

```text
centroid latitude       = 35.682460403442384
centroid longitude      = -114.97278137207032
RGT                     = 844
spot                    = 3
pre-cycle               = 15
post-cycle              = 16
event window start      = 2022-05-17T08:33:13.245063936+00:00
event window end        = 2022-08-16T04:13:10.692301568+00:00
supporting segments     = 5
median terrain step     = 0.5382080078125 m
cluster step NMAD       = 0.12460572509765624 m
cross-spot support      = false
```

The strict scan accepted this cluster because five neighbouring exact ATL08
terrain segments share one persistent upward event window and have a consistent
step magnitude. This is the first accepted survivor from the broad independent
search.

## What it means

Supported:

```text
persistent spatially supported ATL08 terrain step candidate
```

Not supported yet:

- engineered fill;
- exact placed thickness;
- depth to a buried object;
- radar depth prediction;
- transfer of the laser measurement to surrounding radar pixels.

The measured `0.538 m` terrain rise is an observation, not automatically a
construction thickness. It becomes a candidate anchor only if independent
records confirm what changed, where it changed, when it changed, and the
as-built placed thickness.

## Public-context screen

The coordinate is within the wider Eldorado Valley energy-development corridor
south of Las Vegas and Boulder City. Public sources confirm extensive solar and
energy development in that valley.

However, the currently identified project timelines do not explain this event:

- Copper Mountain Solar 5 was placed in service in 2021;
- Townsite Solar + Storage was completed and operating by January 2022;
- the detected step window is May 17 through August 16, 2022.

Therefore, no project name is assigned to Candidate 001. The event could be
later grading, road or drainage work, maintenance, a separate project, or
another surface change. Parcel-level overlay and dated construction records are
required.

## Immediate verification sequence

1. Extract the exact five segment histories and footprint from the private
   campaign result.
2. Confirm that every supporting segment has the same event window and that the
   step persists in all available post-event epochs.
3. Overlay the segment points on official parcel, leasehold and project maps.
4. Identify the controlling parcel or facility.
5. Search only that parcel/facility for May-August 2022 grading, drainage,
   access-road, maintenance or construction records.
6. Require an as-built or certified thickness tied to a mapped footprint.
7. Reject the candidate if records show only general construction, quantities,
   or design thickness without proof that the measured footprint received it.

## Local dossier extraction

After pulling the depth branch:

```powershell
cd C:\Dev\New_GEE

.\.venv\Scripts\python.exe ..\New_GEE_depth\scripts\extract_icesat2_broad_candidate_dossier.py `
  --candidate-rank 1
```

Outputs:

```text
data/research/icesat2_broad_track_scan/southwest_us_earthwork_pilot_v1/
  candidate_001_dossier.json
  candidate_001_dossier.geojson
```

The JSON preserves the full five-segment timelines and quality checks. The
GeoJSON contains the supporting segment points and cluster centroid.

## Decision gate

Candidate 001 advances only if all of the following are confirmed:

```text
exact project or parcel
matching event dates
mapped footprint overlap
measured or certified placed thickness
sufficiently uniform coverage of the ATL08 footprint
```

Until then:

```text
candidate_is_depth_anchor = false
app_numerical_depth_ready  = false
```

## Protection boundary

This candidate review must not modify:

- the classifier;
- frontend result pages;
- Option 5 surface-change behavior;
- production numerical depth output;
- `main`.
