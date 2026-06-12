# V6-INTAKE-1 Intake Report

## Scope

This report records the local intake status for the frozen V6 reference package documented in
`docs/V6_FROZEN_REFERENCE.md`.

The V6 package is outside the active `notebooks/new.ipynb` parity scope. It remains a separate
external V6 track unless and until a dedicated V6 source-lock, recovery, and app-integration task is
opened.

## Graphify Status

Graphify was queried first for current repo documentation, notebook parity scope, V6 package scope,
notebook safety policy, and reference-bundle practices.

Graphify output was unavailable because `graphify-out/graph.json` was not present in this checkout.
Relevant repository docs and tests were inspected after recording that caveat.

## Package Paths Checked

- ZIP: `C:\Dev\New_GEE_EXTERNAL_V6\V6_FROZEN_REFERENCE_20260612T182318Z.zip`
- Inventory: `C:\Dev\New_GEE_EXTERNAL_V6\V6_FROZEN_REFERENCE_inventory_20260612T182318Z.json`

Expected ZIP SHA256:

`cf3732b48b7500c6fd1112316852fa01c2ce7fbb62257610a9d6e07742139a58`

Expected frozen file count: `12`

## Verification Results

| Check | Result | Notes |
| --- | --- | --- |
| ZIP exists at documented path | verified | The exact ZIP path was present on local disk. |
| ZIP SHA256 matches documented hash | verified | The ZIP hash matched the documented expected SHA256. |
| Inventory JSON exists at documented path | verified | The exact inventory path was present on local disk. |
| Inventory lists 12 frozen files | verified | The inventory declares 12 records. |
| ZIP payload contains 12 frozen files | verified | The ZIP has 13 entries including the inventory JSON, and 12 payload files excluding it. |
| ZIP payload filenames match inventory records | verified | The inventory `file` values match the ZIP payload filenames. |
| ZIP payload sizes and SHA256 values match inventory records | verified | All 12 payload records matched by stream inspection without extraction. |
| Coordinates/geometries inspected or printed | no | Intake was limited to documented filenames, policy, and high-level package structure. |

The external directory, documented frozen ZIP, and documented inventory JSON were available during
this intake. The package was inspected without copying or extracting generated V6 artifacts into the
repository.

## File Categories

The following categories are based on `docs/V6_FROZEN_REFERENCE.md` and were revalidated at
filename/schema level against the ZIP payload and inventory records.

| Category | Role | Git Policy |
| --- | --- | --- |
| ZIP | Frozen external V6 package container | Keep outside Git. |
| CSV | Candidate, ranking, request, quote, and quality tabular outputs | Keep outside Git. |
| GeoJSON | Geometry-bearing candidate/request-zone outputs | Keep outside Git. |
| HTML | Local visual inspection map output | Keep outside Git. |
| TXT | Package summary output | Keep outside Git. |
| Inventory JSON | External audit inventory for the frozen package | Keep outside Git unless a future docs task explicitly decides otherwise. |

## Artifact Policy

The V6 frozen package is generated artifact material and must remain outside the repository.

- Do not copy or commit the V6 ZIP, CSV, GeoJSON, HTML, TXT, generated package folders, or V6 notebook.
- Do not add the V6 notebook to `notebooks/`.
- Do not expose exact coordinates, geometries, candidate details, hashes, or filesystem paths through
  public API or frontend surfaces.
- Treat generated package outputs as filesystem-only material unless a future product/security task
  defines a narrower served-artifact contract.
- Do not use this package to loosen or replace the D1C/D2 `notebooks/new.ipynb` parity baseline.

## Classification Decision

| Classification | Decision |
| --- | --- |
| reference-only material | yes |
| source-lockable package material | yes, at package/inventory level; source-contract work remains a separate V6 task |
| future app-integration candidate | yes, as a separate V6 track with its own source-lock and acceptance criteria |
| generated artifact bundle outside Git | yes |

## Parity Scope Decision

The V6 package is not compatible with the current `notebooks/new.ipynb` parity closure as an in-scope
artifact family.

It remains parked as a separate external V6 package track. Same-source or app parity claims for
`notebooks/new.ipynb` must not depend on V6 package artifacts.

## Blocked And Ready Status

Ready:

- Project role and artifact policy can be documented now.
- The frozen ZIP and inventory are verified at package/inventory level.
- V6 can remain parked without blocking `notebooks/new.ipynb` parity status.

Blocked:

- Real V6 source-lock, recovery, and app-integration planning remain blocked until a dedicated V6
  task defines the source contract, schemas, acceptance criteria, and app writer behavior.
- The verified package must not be treated as `notebooks/new.ipynb` parity evidence.

## Next Recommended Task

Open a separate V6 source-lock task to inspect the V6 source contract and schema without moving the
V6 notebook into `notebooks/` or changing the active D1C/D2 parity tooling.
