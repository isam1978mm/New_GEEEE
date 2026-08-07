# ICESat-2 Campaign 011 — Pennsylvania AML Reclamation-Complete Polygons

Date: 2026-08-07

## Approval

The user explicitly approved Campaign 011 with `go` after Campaign 010 closed with zero surviving candidates.

Tyrone Route A remains independent and pending a newly submitted EMNRD public-records request. Campaign 011 does not wait for that response and does not contact any agency.

## Campaign 010 result carried forward

Campaign 010 completed with no failed tiles and no surviving candidate:

```text
polygon-intersecting / completed tiles = 5
failed tiles                            = 0
quality segments retained              = 10,050
exact segment series                   = 7,097
raw step-up segment series             = 1
spatial clusters                       = 0
surviving candidates                   = 0
usable calibration rows                = 0
numerical depth                        = still blocked
```

The isolated Campaign 010 step must not be promoted by weakening the existing spatial-support gate.

## Campaign 011 controlling decision

Campaign 011 leaves Florida and uses a different official agency, geography, and reclamation inventory.

The discovery geometry is the Pennsylvania Department of Environmental Protection (PA DEP) `AML Polygon Feature` layer in the public eMapPA Feature Service:

```text
https://gis.dep.pa.gov/depgisprd/rest/services/emappa/eMapPA_External/FeatureServer/74
```

The layer is official PA DEP polygon data and contains an explicit sub-facility status field:

```text
SF_STATUS = Abandoned
SF_STATUS = Reclamation Complete
```

Campaign 011 retains only:

```text
SF_STATUS = Reclamation Complete
```

The layer does not expose a reliable reclamation-completion date field. Therefore `Reclamation Complete` is used only as an official spatial/status screening gate. It must not be interpreted as an event date, measured fill thickness, or depth anchor.

PA DEP separately publishes annual program-accomplishment pages identifying highlighted AML projects completed during the ICESat-2 era, including 2019, 2020, 2021, 2022, 2023, and 2024. That establishes that the program continued to complete reclamation work after ICESat-2 began, but Campaign 011 will not assign any polygon a completion year unless an exact downstream record proves it.

## Why this is genuinely different from Campaigns 007–010

Campaigns 007–010 were all Florida phosphate-mine/reclamation discovery campaigns using FDEP geometry or annual FDEP attributes.

Campaign 011 changes all three discovery dimensions:

```text
agency       = Pennsylvania DEP
geography    = Pennsylvania coal fields
work class   = abandoned-mine-land reclamation
```

It does not reuse:

- FDEP active-mine boundaries;
- FDEP released phosphate units;
- FDEP 2021 WP/WC status selection; or
- FDEP 2018–2021 TOTALACRECL transitions.

## Campaign identity

```text
campaign_id = northeast_us_earthwork_pilot_v11_pa_aml_reclamation_complete
region_id   = pa_dep_reclamation_complete_aml_polygons
```

Scanner:

```text
scripts/scan_icesat2_pa_aml_reclamation_complete_campaign.py
```

Tests:

```text
tests/unit/test_scan_icesat2_pa_aml_reclamation_complete_campaign.py
```

## Official source fields used

The PA DEP layer exposes polygon geometry and fields including:

```text
OBJECTID
SF_ID
OTHER_ID
SF_NAME
SF_TYPE_CD
SF_TYPE
SF_STATUS_CD
SF_STATUS
SF_PRIORITY_CD
SF_PRIORITY
SF_PROBLEM_CODE
SF_PROBLEM_CODE_DESCRIPTION
HEIGHT_FT
VOLUME_CY
FLOW_GPM
KEYWORDS
PRIORITY
QUANTITY
UOM
STATUS
Shape__Area
Shape__Length
```

`HEIGHT_FT`, `VOLUME_CY`, `QUANTITY`, and similar inventory fields are not automatically treated as placed-cover thickness. They remain contextual metadata only.

## Spatial selection

Campaign 011 queries the official layer over its Pennsylvania AML polygon extent in WGS84 and uses ArcGIS pagination rather than assuming the first 1,000 records are complete.

A feature is retained only when:

1. it is a Polygon or MultiPolygon;
2. `SF_STATUS` normalizes exactly to `RECLAMATION COMPLETE`; and
3. its WGS84 envelope has at least 40 m of approximate span in both east-west and north-south directions.

The 40 m envelope screen does not prove a 40 m clean calibration area. It only removes polygons that cannot geometrically contain the already-required roughly 30–40 m clean footprint. Any survivor still needs an exact manual usable-area assessment excluding roads, drains, structures, highwalls, edges, and other disturbances.

## Cluster identity gate

Every segment supporting a surviving spatial cluster must share exactly one official PA DEP AML polygon identity.

Preferred identity:

```text
SF_ID
```

Fallback identity when necessary:

```text
OBJECTID
```

A cluster split across different reclamation-complete polygons or with ambiguous overlap is rejected rather than guessed.

## Campaign method

Campaign 011 will:

1. query the PA DEP AML Polygon Feature layer with `SF_STATUS = 'Reclamation Complete'`;
2. paginate the official ArcGIS response until all returned pages are exhausted;
3. request WGS84 GeoJSON geometry;
4. reject non-polygon, wrong-status, duplicate, and too-small-envelope features;
5. build the normal resumable 25 km tile grid;
6. reject every tile that does not intersect a retained PA DEP polygon;
7. query ATL08 only for retained tiles;
8. deduplicate ATL08 observations;
9. reject every observation outside the retained official polygons;
10. apply all existing repeat-series, step, neighbour, cluster, and cross-spot gates unchanged;
11. reject any spatial cluster whose supporting segments do not all share exactly one retained PA DEP polygon;
12. attach PA DEP polygon metadata to any survivor; and
13. keep records research disabled until the existing mandatory finalizer also passes.

## Unchanged scientific gates

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

The mandatory finalizer remains unchanged:

```text
maximum net fraction             = 0.50
minimum recovery fraction        = 0.60
minimum retention fraction       = 0.50
minimum reversal fraction        = 0.60
minimum follow-up fraction       = 0.60
maximum context step             = 5.0 m
minimum context segment count    = 4
maximum context event window     = 730 days
```

## Evidence boundary

Even a surviving/finalized terrain step does not establish reclamation construction or finite cover thickness.

For a survivor, later official-record research must independently prove:

1. exact project/activity date or defensible event window;
2. that the terrain change is engineered reclamation rather than unrelated earth movement;
3. measured finite placed-material depth/thickness with units and uncertainty;
4. exact usable geometry tied to a known CRS;
5. a clean area roughly 30–40 m wide after exclusions;
6. stable post-event Sentinel-1 observation period; and
7. radar surface comparability to a second independent measured-depth anchor.

## Protection boundary

Campaign 011 must not modify:

- classifier behavior;
- frontend result pages;
- Option 5;
- Tyrone evidence or the pending EMNRD request;
- production numerical-depth output;
- `main`; or
- any prior campaign result.

Always keep:

```text
records_research_ready = false
numerical_depth_unlocked = false
candidate_is_depth_anchor = false
```

until all downstream evidence gates are independently satisfied.

## Decision after live scan

### Any failed tile

Campaign 011 is incomplete. Fix or retry only the failed work; do not interpret a partial scan as closure.

### Zero spatial candidates and zero failed tiles

Close Campaign 011 with zero usable rows. Do not start Campaign 012 automatically.

### Spatial clusters rejected by the single-polygon gate

Close spatially if no cluster remains. Report the rejection counts and do not begin records research.

### Survivor after single-polygon gate

It is only a terrain-step candidate. Run the existing mandatory finalizer before any records research.

### Finalized survivor

Only then may exact PA DEP project/construction/as-built records be researched. It still is not a calibration row until measured finite thickness, clean geometry, stability, and radar comparability all pass.
