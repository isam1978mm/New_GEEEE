# F171 — Plant Kraft AP-1 elevation-only re-score

Date: 2026-08-20

## Route context

This is part of the site-independent direct-elevation validation route opened at F165. It does not change Tyrone Step 4 status.

## What was verified

Georgia Power's public Plant Kraft AP-1 records include a Certification of CCR Removal and related VRP appendices.

The public record establishes:

- Plant Kraft was retired in 2015.
- The AP-1 ash pond was closed by removal and off-site disposal before the Georgia CCR-rule effective date in November 2016.
- The June 2018 / February 2019 VRP Compliance Status Reports state the former ash pond was excavated to **visually clean plus six additional inches** within the permitted pond boundary.
- The same reports indicate the ash pond excavation was complete by August 2016; September 2016 groundwater sampling is described as occurring one month after completion of excavation.
- The Certification/VRP drawing package contains **Figure 2 — Plant Kraft AP-1 Post Excavation Topographic Map**.
- Figure 2 is tied to 2016 CAD path `G:\2016\160269.000\dwg\160269_TOPO.dwg`, timestamped 2016-08-23 in the indexed drawing text.
- The map identifies Georgia East Zone / NAD83 horizontal control.
- A later **Figure 4 — Plant Kraft AP-1 Topographic Map — Top of Structural Fill** is separately identified, supporting the interpretation that Figure 2 represents the exposed post-excavation surface before later structural-fill grading.

## Scientific assessment

### Post-excavation side

**PASS in principle.** Kraft preserves a clearly named post-excavation topographic surface corresponding to the required clean-removal stage, before the later structural-fill surface.

### Pre-excavation side

**BLOCKED.** No equivalently trustworthy immediate pre-excavation survey or elevation surface was recovered from the public Kraft records searched in F171.

A 2011 Chatham County / Coastal Georgia lidar surface exists historically, but it is too early to substitute automatically for the 2015–2016 pre-excavation pond surface. EPA's historical description states AP-1 operated as rotating ash dewatering cells in which ash was sluiced, dried, and excavated during plant operations. Therefore an older lidar surface cannot be assumed unchanged up to closure excavation.

No 2014–2016 public lidar or site survey was recovered that can be tied to the immediate pre-excavation AP-1 surface with the frozen accuracy requirement.

## Important access limitation

The Georgia Power PDFs are readable as indexed text, but PDF screenshot rendering repeatedly failed with cache errors in the current web environment. Therefore no visual contour digitization was attempted and no elevations were fabricated from corrupted text extraction.

## Decision

Plant Kraft AP-1 = **POST-SURFACE PASS / PRE-SURFACE BLOCKED**.

Kraft is not currently a complete executable direct-elevation validation site.

Bremo West Ash Pond remains the stronger candidate because it has both a dated pre-excavation field survey and licensed post-excavation surveys; Bremo's remaining blocker is source-file extraction rather than missing scientific chronology.

## Reopen condition

Kraft becomes executable only if a trustworthy immediate pre-excavation surface is recovered, such as:

- 2015/early-2016 survey points/contours/DTM of AP-1 before closure excavation;
- a contemporaneous survey-grade lidar acquisition covering AP-1;
- native project CAD containing both pre- and post-excavation surfaces with documented control.

Do not use the 2011 lidar as a substitute without evidence the AP-1 surface remained unchanged.

## Guardrails

- no classifier changes;
- no UI changes;
- no NB-formula changes;
- no fitting to Tyrone known depth answers;
- do not call Kraft validated until both surfaces are recovered and independently checked.
