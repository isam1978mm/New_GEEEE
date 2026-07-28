# Option 1 — Global Depth — Batch 2 cheap screen — 2026-07-28

## Decision

**One candidate advanced to decisive documentary review: Lowry Landfill.**

The other four candidates failed before any radar analysis.

## Locked evidence gate

A candidate may advance only when the public record can plausibly support all of the following:

- full-scale vegetated zones with at least 30–40 m clean interior after exclusions;
- final measured as-built numerical depth, not only a design thickness;
- an exact second measured depth zone or confirmed control area;
- matching radar-facing surface construction;
- coordinate-tied geometry;
- numerical measurement or survey uncertainty;
- a stable Sentinel-1 observation period.

No Earth Engine query was permitted during this screen.

## Candidate 1 — Rocky Flats Original Landfill, Colorado

### Public evidence

DOE states that a new soil cover and drainage features were installed in 2005. DOE later reported recurring downhill slumping and a major stabilization project using hundreds of anchors, buried concrete retention blocks, and new underground drains beginning in 2019.

### Decision

**STOP — unstable and materially reconstructed during the Sentinel-1 era.**

The later stabilization work disturbed the covered hillside and changed subsurface drainage and surface support. The historical 2005 cover therefore does not provide a clean unchanged radar period suitable for calibration.

Official sources:

- https://www.energy.gov/lm/articles/rocky-flats-site-original-landfill-stabilizing-project-underway
- https://www.energy.gov/lm/articles/rocky-flats-site-original-landfill-stabilized

## Candidate 2 — Lowry Landfill, Colorado

### Public evidence

EPA describes a roughly 200-acre main landfill with a soil cover installed when landfilling ended in 1990. EPA reports that the cover is at least 4 feet thick and up to 12 feet thick in some places. EPA also reports that, in 1999, 2 additional feet of soil were placed on the 29-acre north face to provide a minimum cover thickness of 4 feet over the closed landfill. Construction was certified complete in 2006, and the site remains in long-term operations and maintenance.

### Cheap-screen decision

**ADVANCE TO DECISIVE DOCUMENT REVIEW.**

Lowry has adequate area, vegetation, long-term management, and documented broad thickness variation. The decisive question is whether the variation is represented by two exact final measured polygons with numerical uncertainty and matching radar-facing surfaces.

Official sources:

- https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0800186
- https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1016WLK.TXT

## Candidate 3 — Modern Sanitation Landfill, Pennsylvania

### Public evidence

EPA documents a 66-acre landfill with a PADEP-approved low-permeability cap. The ROD describes a 20-acre plateau and 46-acre side-slope area, and EPA reports that the cap and cover system is functioning properly.

### Decision

**STOP — no distinct depth pair.**

The plateau and side slopes are geometric parts of one cap system. The reviewed public record did not establish different final measured cover depths for the two areas. A slope-versus-plateau comparison would also introduce terrain geometry as a radar confounder.

Official sources:

- https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0301322
- https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=91003E3R.TXT

## Candidate 4 — Shpack Landfill, Massachusetts

### Public evidence

EPA states that the selected and completed remedy excavated waste, placed clean fill in excavated areas, graded the site, and restored or replicated wetlands and uplands. CERCLA construction was completed in 2013–2014.

### Decision

**STOP — removal and ecological restoration, not a retained two-depth cover system.**

The final surface is a mixture of restored wetlands and uplands after excavation and backfilling. It does not provide two large retained cover-depth conditions with comparable radar-facing surfaces.

Official source:

- https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0100655

## Candidate 5 — Fernald On-Site Disposal Facility, Ohio

### Public evidence

DOE describes the OSDF as a single large engineered disposal mound completed in 2006, approximately 800 feet wide, 3,700 feet long, and 65 feet high. It has one multilayer cap-and-liner system and is covered with prairie grass.

### Decision

**STOP — one cover system and no second measured condition.**

The site is large and stable, but the reviewed official material describes one OSDF cap profile rather than two exact final measured depth zones or a confirmed no-target control area.

Official source:

- https://www.energy.gov/documents/fernald-preserve-ohio-site-disposal-facilitypdf

## Cheap-screen result

```text
candidate_count = 5
advanced_to_decisive_review = 1
advanced_candidate = Lowry Landfill
Earth Engine query executed = no
calibration row created = no
training started = no
numerical depth ready = no
app depth enabled = no
```

## Next action

Perform a bounded Lowry documentary review for:

1. exact polygons for at least two final measured cover-depth conditions;
2. final as-built depth values rather than minimum or approximate statements;
3. numerical survey or measurement uncertainty;
4. matching topsoil and vegetation assembly;
5. a stable observation window after construction and repairs.
