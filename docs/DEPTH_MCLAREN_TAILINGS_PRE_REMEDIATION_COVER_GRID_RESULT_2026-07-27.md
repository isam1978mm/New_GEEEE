# McLaren Tailings pre-remediation cover-grid result - 2026-07-27

## Decision

**NOT GOOD TO GO**

McLaren initially appeared promising because the old tailings cover was measured on a 100-foot grid using 35 boring locations. Cover thickness was recorded to the nearest inch.

Those measurements cannot support the app's numerical-depth calibration because they describe the site before the final reclamation project.

## Fatal blocker

The reclamation project removed the tailings impoundment from the Soda Butte Creek floodplain, placed the waste in a lined repository, and reconstructed the creek and floodplain.

The project was completed in 2014. The disturbed site was covered with amended soil and seeded.

Therefore, the old measured shallow/deep cover zones did not survive into a stable Sentinel-1 observation period. Their geometry and physical meaning were destroyed by excavation, regrading, repository construction, creek reconstruction and reseeding.

This cannot be fixed by georeferencing the old boring grid.

## Calibration decision

```text
full-scale pre-remediation measured grid = yes
100-ft grid with 35 boring locations = yes
old cover thickness measurements = yes
old measured zones survived remediation = no
stable Sentinel-1-era depth zones = no
usable calibration row created = no
Earth Engine query executed = no
training started = no
app depth enabled = no
plan changed = no
```

Final decision:

```text
NOT_GOOD_TO_GO_MEASURED_ZONES_REMOVED_DURING_REMEDIATION
```

## Sources reviewed

- Final Reclamation Design Report for the McLaren Tailings Abandoned Mine Site.
- National Park Service, *Crystal Clear: McLaren Tailings Restoration*.
- National Park Service, *Mine tailings reclamation project improves water quality in Yellowstone's Soda Butte Creek*.
- National Park Service, *Reclamation work at McLaren Mill and Tailings*.

## Next step

Continue the approved search unchanged. Do not advance a historical measured-depth map unless its measured zones remained physically intact and stable during the Sentinel-1 period.
