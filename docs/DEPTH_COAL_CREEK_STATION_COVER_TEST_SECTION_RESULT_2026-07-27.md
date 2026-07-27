# Coal Creek Station cover test-section result - 2026-07-27

## Decision

**NOT GOOD TO GO**

Coal Creek was a strong lead because its field demonstration included two conventional vegetated soil covers with a real nominal thickness contrast:

- municipal-waste cover: 3 ft total;
- special-waste cover: 5 ft total;
- nominal difference: 2 ft, or 0.6096 m;
- both finished with 6 in of topsoil and adapted grasses.

The project also included a 3-ft evapotranspiration cover, but that design removes the compacted clay-rich layer and therefore is not a depth-only comparison with the conventional covers.

## Recovered cover profiles

The official LRC-50-F application gives these designs:

| Cover | Topsoil | Subsoil | Compacted clay-rich layer | Total |
|---|---:|---:|---:|---:|
| Municipal-waste cover | 6 in | 12 in | 18 in | 36 in / 3 ft |
| Special-waste cover | 6 in | 30 in | 24 in | 60 in / 5 ft |
| Evapotranspiration cover | 6 in | 30 in | 0 in | 36 in / 3 ft |

The best possible depth pair is therefore the 3-ft municipal-waste cover versus the 5-ft special-waste cover. Both are conventional soil covers and share the same stated grassed topsoil surface, although their internal layer proportions are not identical.

A published case history confirms that the field lysimeters were constructed in May 2004.

## Fatal problem - physical pixel support

The site-specific project description states that the test plots are 10 m by 20 m. Its test-plot drawing shows:

- outer test-section dimensions: 20 m by 30 m;
- central monitored lysimeter: 10 m by 20 m;
- diversion berms, side boundaries, collection piping, and monitoring infrastructure around the lysimeter.

The depth project requires a clean 20 m footprint that remains within one condition after applying inward margins for boundaries, berms, survey uncertainty, geolocation error, and mixed pixels.

Coal Creek cannot satisfy that requirement:

- the authoritative monitored plot is only 10 m wide;
- the full outer section is exactly 20 m wide;
- any nonzero inward margin reduces the usable width below 20 m.

This is a physical geometry failure. Better georeferencing or different code cannot create additional interior width.

## Other unresolved gates

The recovered public package also does not provide:

- final as-built thickness measurements for each completed section;
- exact WGS84 polygons for the three sections;
- numerical boundary or survey uncertainty;
- proof that the original test sections remained undisturbed through a usable Sentinel-1 observation period.

These issues are secondary because the width failure already closes the candidate.

## Extraction correction

The first automated extraction selected a neighboring project because the NDIC page grouped several project links inside one broad HTML container. That artifact was rejected.

The corrected extractor used the exact official LRC-50-F URL, validated the URL identity, recovered all 85 pages, and rendered every page for visual review. No conclusions were taken from the incorrect neighboring-project artifact.

## Calibration decision

```text
constructed field sections = yes
same stated grassed surface = yes for all three profiles
best nominal depth contrast = 2 ft / 0.6096 m
outer section = 20 m x 30 m
monitored lysimeter = 10 m x 20 m
clean 20 m interior after margins = no
final as-built depth grid = not recovered
exact WGS84 polygons = not recovered
numerical uncertainty = not recovered
Sentinel-1-era survival = not confirmed
calibration row created = no
Earth Engine query executed = no
app depth enabled = no
```

Final decision:

```text
NOT_GOOD_TO_GO_PIXEL_SUPPORT_FAILED
```

## Sources reviewed

- North Dakota Industrial Commission, LRC-50-F, *Grant Application for an Alternative Cover Demonstration Project at Coal Creek Station*.
- Stockdill, Jorgenson, and Obermeyer (2006), *Case History and Regulatory Aspects of a Final Cover Performance Evaluation Involving Conventional and Evapotranspirative Cover Designs*.
- EPA CLU-IN evapotranspiration-cover demonstration summary.

Temporary draft PR #13 was used only for document recovery and rendering. It should be closed without merging.

## Next step

Do not continue with field trials whose monitored sections are 10 m wide or whose outer decks are only 20 m wide.

The next candidate must use substantially larger full-scale cover zones, preferably at least 30 to 40 m wide after excluding berms and infrastructure, with final as-built thickness measurements and one uniform vegetated surface assembly.
