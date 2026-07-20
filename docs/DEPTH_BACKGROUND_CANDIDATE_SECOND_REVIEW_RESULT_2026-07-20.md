# Depth Background Candidate Second Review Result — 2026-07-20

Status: the second eight-candidate private set was visually reviewed over satellite imagery. The **south** candidate was selected as the best provisional comparison window for exact acquisition matching.

This selection is a qualitative screening decision only. It does not create a confirmed no-target record, establish a signal difference, estimate depth, train a model, import a calibration row, or enable app depth output.

## Reviewed set

```text
candidate size = 50 m x 50 m
edge gap from site = 300 m
candidate directions = north, east, south, west, northeast, southeast, southwest, northwest
```

All geometry remained outside Git.

## Visual decision

```text
north = rejected
northeast = rejected
east = rejected
southeast = rejected
south = provisionally selected
southwest = secondary but not selected
west = rejected
northwest = rejected
```

The south candidate most closely resembled the controlled-site window in visible open grass/soil context and did not visibly contain a building, water body, industrial facility, or dense wooded cover inside the candidate box.

The southwest candidate also covered open ground but showed less comparable surrounding context and was not selected.

The other candidates were rejected because they visibly intersected or closely bordered residential, paved, industrial, wooded, marsh, highway, or parking-area context.

## Scientific boundary

The selected south polygon remains only a **comparison window**. A single satellite basemap view cannot prove historical stability or absence of subsurface material.

The next exact-acquisition match is allowed only to verify that the site and selected background share the same Sentinel-1 images in both clean periods. It is not a depth or buried-feature validation run.

## Next permitted step

```text
copy the private south candidate to the canonical private background file
→ run the no-network site-background matcher dry run
→ if the dry run passes, execute exact acquisition matching with the reviewed-background flag
→ freeze the matched image manifest privately
```

## Checklist

- [x] Generate the second eight-candidate private set.
- [x] Load the site, all eight candidates, and satellite basemap.
- [x] Review all eight candidates.
- [x] Select south as the provisional comparison window.
- [x] Keep all coordinates and geometry outside Git.
- [ ] Create the canonical private background file from the south candidate.
- [ ] Run the no-network matcher dry run.
- [ ] Execute exact acquisition matching only after the dry run passes.
- [ ] Keep app depth output unavailable.
