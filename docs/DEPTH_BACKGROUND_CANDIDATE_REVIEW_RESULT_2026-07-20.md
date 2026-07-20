# Depth Background Candidate Review Result — 2026-07-20

Status: the first four private background candidates were visually reviewed over satellite imagery and **all four were rejected**.

This review selected no background polygon and made no signal, depth, calibration, training, or app-activation claim.

## Reviewed set

The first private set used:

```text
candidate size = 50 m x 50 m
edge gap from site = 100 m
candidate directions = north, east, south, west
```

The site and all candidate geometry remained outside Git.

## Decision

```text
north = rejected
 east = rejected
south = rejected
 west = rejected
approved_background = none
```

The surrounding land cover and infrastructure visible in the satellite basemap were not sufficiently comparable to the controlled-site window. The candidates included visibly different built, paved, road-adjacent, residential, or industrial context.

The rejection is qualitative visual screening only. It is not a scientific measurement and does not establish absence or presence of any subsurface feature.

## Tool limitation found

The original generator created only four nearby cardinal-direction candidates. That was insufficient for this site because potentially more comparable open-ground areas occur outside the immediate north/east/south/west ring.

The generator has therefore been extended with an optional eight-direction mode:

```text
north
east
south
west
northeast
southeast
southwest
northwest
```

The existing four-direction behavior remains the default.

## Next permitted step

Generate a second private set in a new directory using:

```text
edge gap = 300 m
include diagonals = true
```

Then visually review the eight new candidates over satellite imagery. A candidate may proceed only if it is clearly outside the controlled construction footprint and has reasonably comparable open-ground surface context.

## Checklist

- [x] Load the controlled-site polygon.
- [x] Load the first four candidate polygons.
- [x] Add a satellite basemap.
- [x] Review all first-set candidates.
- [x] Reject all four first-set candidates.
- [x] Preserve the first set as rejected private evidence.
- [x] Extend the generator with optional diagonal candidates.
- [ ] Run the extended generator tests.
- [ ] Generate the second eight-candidate private set.
- [ ] Review the second set.
- [ ] Select one candidate or reject the second set.
