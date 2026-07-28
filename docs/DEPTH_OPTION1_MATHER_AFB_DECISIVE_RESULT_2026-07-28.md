# Option 1 — Mather Air Force Base decisive result — 2026-07-28

## Decision

**NOT GOOD TO GO for numerical depth.**

Mather Air Force Base is a strong documentary near-miss, but the reviewed public record does not provide the exact final measured depth evidence required for calibration.

## What the official record establishes

- The Landfill Operable Unit included several landfill sites.
- Site 3 received an engineered cap.
- Site 4 received an engineered cap plus flood-control measures such as an embankment.
- Refuse from Site 2 was excavated and consolidated into Site 4 before Site 4 was capped.
- Additional waste or contaminated material from other sites was also placed at Site 4.
- The 1998 Basewide ROD references a `Final Closure Certification Report for Landfill Sites` prepared in 1997.
- EPA's current site profile states that two landfills received low-permeability caps and are monitored.

## Why it fails the calibration gate

### 1. No two final measured depth polygons

The publicly reviewed documents describe selected cap types and completed remedies, but do not publish two coordinate-tied final measured cap-depth polygons.

### 2. No numerical depth or survey uncertainty

No pointwise final cover-thickness table, bounded depth interval, or numerical survey uncertainty was recovered from the indexed public record.

### 3. Site 4 is not a clean control or simple second condition

Site 4 is a consolidation landfill. It received refuse from Site 2 and other material before capping. It also includes flood-control infrastructure. This makes it unsuitable as a simple negative/control comparison.

### 4. Surface construction is not proven equivalent

Site 3 is described as receiving an engineered cap. Site 4 received an engineered cap plus an embankment and consolidation work. The reviewed record does not prove identical radar-facing surface construction across two clean interior zones.

### 5. The referenced closure certification is not enough without its measurements

The 1998 ROD proves that a Final Closure Certification Report existed, but the indexed record reviewed here does not expose the report's final measured thickness data, coordinate-tied polygons, or numerical uncertainty.

## Reopen rule

Reopen Mather only if the 1997 Final Closure Certification Report or equivalent as-built package is recovered and it contains all of the following:

```text
separate Site 3 and Site 4 final measured depth polygons = yes
coordinate-tied geometry = yes
numerical depth or survey uncertainty = yes
matching radar-facing surface construction = yes
30-40 m clean interiors after infrastructure exclusions = yes
stable Sentinel-1 period = yes
```

## Sources

- EPA Mather site profile: https://cumulis.epa.gov/supercpad/SiteProfiles/index.cfm?fuseaction=second.cleanup&id=0902793
- 1995 Landfill OU ROD: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=91002T35.TXT
- 1998 Basewide OU ROD: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=9100NPUB.TXT

## Current app status

```text
mather_documentary_gate = failed
calibration_record_created = false
earth_engine_query_executed = false
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
training_started = false
numerical_depth_ready = false
app_depth_enabled = false
```
