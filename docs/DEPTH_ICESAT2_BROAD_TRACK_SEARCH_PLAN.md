# ICESat-2 broad track-first candidate search

Status: approved next route; independent candidate discovery; not an app depth feature.

## Decision

The following routes are closed for the current data:

- the nine completed app runs;
- the seven unique run geographies;
- the 10 km expansion around those geographies;
- the diagnostic recheck of isolated steps out to 1 km.

None produced a spatially supported persistent upward terrain-step cluster.
The next route must therefore stop expanding around the same locations and
search new areas directly along repeated ICESat-2 ATL08 terrain tracks.

## Objective

Find previously unknown locations where the measured ATL08 terrain history is:

```text
flat -> one upward jump -> flat
```

A location survives only when neighbouring exact ATL08 terrain segments show
the same event window and a consistent step magnitude. Records are researched
only after a cluster survives.

## What is free before records

The search uses ATL08 terrain height (`h_te_*`), not canopy height. It uses the
multi-epoch shape to reject:

- gradual ramps;
- stable ground;
- reversible or irregular changes;
- isolated spikes;
- spatially unsupported single segments.

This substantially reduces vegetation and random-noise confounding before any
record search, but it does not prove engineered fill. Construction, grading,
buildings and other surface works can also create a step.

## First campaign

Campaign ID:

```text
southwest_us_earthwork_pilot_v1
```

Initial independent search box:

```text
west  = -115.75
south =   35.55
east  = -114.65
north =   36.45
```

The box is intentionally outside the old app AOIs. It is a first operational
pilot, not a claim that an anchor exists there. The campaign file is editable,
so later boxes can be added without changing the scanner.

## Scientific gates

The broad scan retains the existing strict defaults:

```text
minimum distinct epochs          = 4
minimum observations per side    = 2
minimum upward step              = 0.30 m
maximum plateau NMAD             = 0.25 m
minimum dominant-jump fraction   = 0.60
neighbour connection distance    = 250 m
minimum neighbouring segments    = 3
maximum cluster step NMAD        = 0.25 m
cross-spot diagnostic distance   = 500 m
```

The campaign must not lower these values merely to create candidates.

## Operational design

The scanner:

1. loads explicit bounding boxes from a versioned JSON campaign file;
2. assigns a local UTM projection to each moderate-sized region;
3. divides each region into projected tiles;
4. queries ATL08 terrain observations tile by tile;
5. stores a private normalized cache for every successful tile;
6. resumes from cached tiles after interruption;
7. deduplicates observations at tile boundaries;
8. classifies exact segment histories through time;
9. requires spatially supported upward-step clusters;
10. ranks only surviving clusters for later record lookup.

A failed remote tile is reported and does not erase successful tile caches.
The scan never creates app artifacts, depth anchors, public downloads or UI
output.

## Files

```text
config/icesat2_broad_track_campaign_v1.json
scripts/scan_icesat2_broad_track_campaign.py
tests/unit/test_icesat2_broad_track_campaign.py
```

Default private output:

```text
data/research/icesat2_broad_track_scan/
```

## Required interpretation

A surviving cluster means only:

```text
persistent spatially supported ATL08 terrain step candidate
```

It does not mean:

- engineered fill confirmed;
- placed thickness confirmed;
- depth to a buried object;
- radar depth prediction;
- transfer of the laser measurement to surrounding radar pixels.

## Decision after the campaign

- `surviving_candidate_count > 0`: inspect the ranked timelines and research
  records only for those locations.
- `surviving_candidate_count = 0` with no failed tiles: close the pilot box and
  add a new independent campaign box.
- failed tiles: rerun; successful tiles are reused from cache.

## Protection boundary

This route must not modify:

- the classifier;
- frontend result pages;
- Option 5 surface-change behavior;
- production numerical depth output;
- `main`.
