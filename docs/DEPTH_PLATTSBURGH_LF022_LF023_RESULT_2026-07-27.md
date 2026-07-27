# Plattsburgh LF-022/LF-023 depth-pair result - 2026-07-27

## Decision

**NOT GOOD TO GO**

The Plattsburgh pair passes the basic size and long-term-stability screens. It fails the approved numerical-depth evidence gate because the public record does not provide coordinate-tied final measured cover thicknesses, and it does not prove that the radar-facing soil construction is equivalent between the two landfills.

## Why the pair looked promising

### LF-022

The recovered official five-year review describes:

- an irregular landfill approximately 500 feet wide by 1,200 feet long;
- approximately 11.3 acres;
- a completed remedy consisting of 12 inches of soil cover and grass;
- completion in spring 1995;
- final inspection on July 20, 1995.

### LF-023

The same report describes:

- an irregular landfill approximately 500 feet wide by 1,400 feet long;
- approximately 12 acres;
- a synthetic barrier layer;
- a soil barrier-protection layer;
- six inches of topsoil;
- grass and shallow-rooted plants;
- completion in spring 1994;
- final inspection on September 19, 1994.

Both areas are large enough in principle to retain a 30-40 m clean interior after reasonable boundary and infrastructure exclusions.

## Stability result

The five-year-review record reports acceptable cap inspections after construction. The current EPA site profile states that the former-base landfill caps continue to be inspected annually and that previous cleanup actions have been found protective.

This supports a potentially stable Sentinel-1-era observation period. Stability is not the fatal problem for this candidate.

## Fatal blocker 1: no public coordinate-tied measured depths

The recovered public package includes the design Records of Decision and the 2009 five-year review. It confirms that the covers were built and inspected.

It does not publish:

- a final as-built cover-thickness grid;
- survey-point coordinates linked to measured thicknesses;
- a point-by-point comparison between subgrade and final grade;
- numerical horizontal or vertical survey uncertainty;
- execution-ready interior depth polygons.

The five-year review cites separate Remedial Action Construction Completion Reports for LF-022 and LF-023, but those reports were not present in the public NYSDEC package recovered during this screen.

Therefore, the available 12-inch and multi-layer-cover descriptions are completed design descriptions, not coordinate-tied final measured calibration values.

## Fatal blocker 2: matching near-surface construction is not proven

The two visible surfaces are both vegetated, but their construction records are not equivalent:

- LF-022 is described only as 12 inches of soil cover with grass.
- LF-023 has six inches of topsoil over a separate soil barrier-protection layer and a synthetic barrier.

The public record does not demonstrate that the two areas used the same:

- topsoil source or blend;
- soil gradation;
- compaction;
- drainage behavior;
- moisture-retention behavior;
- surface preparation.

A Sentinel-1 difference could therefore reflect different upper-soil construction or moisture behavior rather than cover depth alone.

## Calibration decision

```text
full-scale vegetated areas = yes
30-40 m clean interior possible in principle = yes
stable Sentinel-1 period supported in principle = yes
second cover condition exists by design = yes
coordinate-tied final measured depths = no
pointwise as-built thickness grid = no
numerical survey uncertainty = no
matching near-surface construction proven = no
usable calibration row created = no
Earth Engine query executed = no
training started = no
app depth enabled = no
plan changed = no
```

Final decision:

```text
NOT_GOOD_TO_GO_PUBLIC_ASBUILT_AND_MATCHING_SURFACE_FAILED
```

## Sources reviewed

- Plattsburgh AFB Third Five-Year Review Report, 2009.
- LF-022 Record of Decision, 1992.
- LF-023 Source Control Record of Decision, 1992.
- EPA current Plattsburgh Air Force Base site profile.
- NYSDEC public document listing for site 510003.
- Temporary GitHub recovery PR #16 artifact.

## Next step

Continue the approved search unchanged. Advance only a full-scale vegetated pair with public coordinate-tied final measured depths, numerical uncertainty, matching upper-soil construction, at least 30-40 m clean interior, and a stable Sentinel-1 observation period.
