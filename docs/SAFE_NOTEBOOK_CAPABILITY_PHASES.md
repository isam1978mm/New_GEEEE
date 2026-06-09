# Safe Notebook Capability Phases

This document records the seven-phase plan for converting useful notebook-only capabilities into safe app features.

The rule is simple:

```text
Local PC = private research mode
VPS = safe deployment mode
```

The notebook can remain powerful for private local work, but the deployable app must keep exact locations, raw labels, unvalidated classifier claims, and sensitive artifacts away from the public API, frontend, logs, and downloadable artifact surface.

## Global rules

- Do not copy the notebook directly into the app.
- Do not expose exact coordinates, WKT, GeoJSON, KMZ, CRS transforms, bounds, hashes, or local paths in public API/frontend responses.
- Do not expose raw treasure/Tesla/hard-classifier labels in the deployable app.
- Keep local-private research code out of the deployable app path.
- Use `FILESYSTEM_ONLY` for sensitive exact-location, classifier, KMZ, GeoJSON, field, and local-private outputs.
- Do not add CNN/YOLO/Swin/Unet inference as a real detection feature without labeled data, validation, and a separate approval decision.
- Every app feature must have tests, artifact-class decisions, and redaction/serving checks.

## Recommended order

1. Safe Run File Inspector
2. Safe Map Point Picker
3. Local-only KMZ / GeoJSON / field package
4. Local-private raw classifier plus VPS-safe separation
5. Offline AI research module only
6. Stable formula contracts for deferred feature stacks
7. Run Diagnostics CLI

---

## Phase 1 — Safe Run File Inspector

### What it does

Adds an app feature that inspects files created by one run only:

```text
./data/runs/<run_id>/
```

It can report:

- files found;
- missing expected files;
- GeoTIFF shape, CRS, transform, nodata, and basic stats;
- NPY shape and dtype;
- disk size;
- artifact registry status;
- alignment status.

### Why we need it

The notebook lets the operator manually inspect many folders and outputs. The app needs the same practical checking power, but in a clean and repeatable way.

This helps answer simple operator questions:

- Did the run finish correctly?
- Which files are missing?
- Which output is broken?
- Are the rasters on the same grid?
- How much disk space did this run use?

### Why not copy the notebook way

The notebook scans Google Drive, `/content`, manual upload folders, and arbitrary paths. That is useful in Colab, but risky in the app.

The app version must inspect only the controlled run directory. It must not scan random folders, Drive folders, secret folders, or user-supplied absolute paths.

### Safety boundary

- Read only from `./data/runs/<run_id>/`.
- No arbitrary filesystem scanning.
- No exact coordinate output in public API responses.
- Sensitive file details stay internal or local-only.

### Acceptance checks

- Unit test: rejects paths outside the run directory.
- Unit test: reports missing expected artifacts.
- Unit test: identifies CRS/transform/shape mismatches.
- Integration test: works on a completed sample run.

---

## Phase 2 — Safe Map Point Picker

### What it does

Adds a controlled app map picker:

- click on a map to select a point;
- optional search box;
- external tiles controlled by settings;
- selected point stored internally;
- no raw coordinate printing in the normal UI.

### Why we need it

The notebook has a friendly map picker. The app should also let the operator choose a point without manually typing coordinates.

This improves usability and reduces input mistakes.

### Why not copy the notebook way

The notebook prints exact latitude/longitude, WKT, GeoJSON, and geometry directly. That is acceptable for a private notebook, but not for a deployable web app.

The app must keep exact coordinates internal and avoid exposing them through public responses.

### Safety boundary

- Map selection is allowed.
- Exact coordinates are stored internally only.
- UI can show a safe confirmation like `Point selected`.
- External tiles remain configurable and can be disabled.
- No public API response should include exact coordinates, geometry, CRS transform, or bounds.

### Acceptance checks

- Frontend test: user can select a point.
- API test: public run response does not expose raw lat/lon.
- Redaction test: coordinate-like fields are blocked from public DTOs.
- Settings test: external tiles can be disabled.

---

## Phase 3 — Local-only KMZ / GeoJSON / field package

### What it does

Creates exact-location files for private local use only, such as:

```text
./data/runs/<run_id>/kmz/
./data/runs/<run_id>/full_job/location/
./data/runs/<run_id>/full_job/field_ops/
```

Possible outputs:

- KMZ for Google Earth;
- GeoJSON for local GIS review;
- field brief text;
- private navigation package;
- local-only exact site/focus geometry.

### Why we need it

Exact-location outputs are useful for the operator's own local workflow. They help with private review, Google Earth visualization, and field preparation.

### Why not expose it in the app

Exact KMZ, GeoJSON, WKT, and coordinate files reveal the real location. They must not become downloadable through the web app or visible in a public API response.

### Safety boundary

- Artifact class must be `FILESYSTEM_ONLY`.
- `http_servable=False`.
- Not listed in public artifact lists.
- Not previewed or tiled unless a safe, non-georeferenced preview is explicitly generated.
- Local filesystem access only.

### Acceptance checks

- Unit test: exact-location artifacts are `FILESYSTEM_ONLY`.
- Integration test: artifact endpoint refuses these files.
- Integration test: frontend does not list these files.
- Redaction test: exact coordinates do not appear in public responses.

---

## Phase 4 — Local-private raw classifier plus VPS-safe separation

### What it does

Keeps the raw notebook-style treasure/Tesla/hard-classifier logic available on the operator's own PC, while separating it from the deployable VPS-safe app.

The agreed rule:

```text
Local PC: raw/private research logic may run as-is.
VPS: raw/private logic must not be deployed or exposed.
```

### Local PC private mode

Allowed locally on the operator's own machine:

- original notebook classifier labels;
- raw treasure/Tesla/hard-classifier naming;
- exact local outputs;
- private KMZ/GeoJSON;
- manual inspection;
- private experiments.

Recommended environment flag:

```text
LOCAL_PRIVATE_MODE=1
```

Recommended local-only folders:

```text
local_private/
private_outputs/
raw_notebook_exports/
```

These folders should be gitignored.

### VPS safe mode

Required for deployment:

- neutral classes only, such as `Class_A`, `Class_B`, `Class_C`;
- no archaeology-specific labels in app code, tests, logs, filenames, API responses, or frontend;
- no frontend button for the raw classifier;
- no HTTP route to the raw classifier;
- no BackgroundTasks or orchestrator path invoking raw logic;
- no exact-coordinate public output;
- classifier outputs are `FILESYSTEM_ONLY`;
- no claim of real-world detection accuracy.

Recommended deployment flag:

```text
DEPLOYMENT_MODE=vps_safe
```

### Why we need it

The operator needs freedom to continue private research locally, but the project also needs a safe deployment path.

This split gives both:

- private local power;
- clean VPS-safe app behavior.

### Why not deploy the raw version as-is

On a VPS, mistakes are easier and more serious:

- a route can expose output;
- a frontend button can reveal labels;
- logs can contain sensitive names;
- exact coordinates can leak;
- raw classifier claims can create false confidence;
- GitHub can accidentally contain private terms or files.

### Required structure

Use hard separation, not memory or comments only.

Recommended structure:

```text
project/
├── app/
│   └── pipeline/
│       └── stages_experimental/
│           ├── classifier.py        # neutral VPS-safe version
│           ├── classes.py           # Class_A, Class_B...
│           └── run.py               # CLI-only
│
├── local_private/                   # operator PC only, gitignored
│   └── raw_notebook_classifier/
│       └── original_logic.py        # raw labels allowed here only
│
├── private_outputs/                 # operator PC only, gitignored
└── docs/
    └── CLASS_MAPPING.md             # private mapping only
```

### Safety boundary

- Raw classifier code must not be imported by app routes, frontend, BackgroundTasks, or the core orchestrator.
- VPS-safe classifier remains neutralized and CLI-only.
- Raw local folders are gitignored.
- Forbidden-term scanners protect deployable paths.

### Acceptance checks

- Unit test: raw local folders are gitignored.
- Unit test: forbidden terms fail in deployable paths.
- Unit test: experimental package requires explicit enable flag.
- Integration test: no API route exposes classifier outputs.
- Integration test: frontend does not list classifier outputs.
- Policy test: VPS mode refuses raw/private imports.

---

## Phase 5 — Offline AI research module only

### What it does

Keeps CNN/Swin/YOLO/Unet training and inference work as offline research until there is real labeled data and validation.

Possible future module:

```text
research_ai/
```

Allowed only after separate approval:

- labeled dataset definition;
- train/validation split;
- model card or validation report;
- reproducible training command;
- output artifact-class rules;
- no public detection claim without validation.

### Why we need it

Deep learning may become useful later, but only if trained and tested properly.

### Why not now

The notebook contains model attempts and inference experiments, not a validated production model. Without real labels and testing, model output can be misleading.

### Safety boundary

- Not part of v1 production app.
- No frontend/API exposure.
- No real detection claims.
- Outputs are local/private until validated.
- Requires separate plan before implementation.

### Acceptance checks

For now:

- No CNN/YOLO/Swin/Unet production route.
- No frontend control for AI model inference.
- No model output served as public result.

Future acceptance requires a separate validation document.

---

## Phase 6 — Stable formula contracts for deferred feature stacks

### What it does

Converts useful notebook feature-stack families into stable, testable app stages one family at a time.

Candidate families:

```text
NANO_STACK
GPHYS_MASTER_640
RAD_MASTER_CUBE_640
ULTIMATE_GPHYS_SCAN_640
```

Before coding any family, create a formula contract defining:

- purpose;
- input bands;
- output bands;
- exact formulas;
- nodata rules;
- grid rules;
- normalization rules;
- artifact classes;
- QA checks;
- parity expectations;
- known notebook duplicates or rejected variants.

### Why we need it

This is where useful notebook science can become clean app output.

The app should not lose good feature-engineering ideas, but each idea must become stable and testable.

### Why not copy all feature stacks now

Many notebook stacks are duplicates, renamed variants, or unstable experiments. Copying all of them would make the app messy, hard to test, and hard to trust.

### Recommended first candidate

Start with:

```text
GPHYS_MASTER_640
```

Reason: it is likely useful, but needs a fixed neutral formula contract before implementation.

### Safety boundary

- No archaeology-specific output names in deployable paths.
- No exact coordinates in public responses.
- Artifact classes assigned at write time.
- Any local-sensitive raster/tensor output remains protected by artifact policy.

### Acceptance checks

- Formula contract doc exists before code.
- Unit tests cover formulas and nodata handling.
- Parity/contract tests verify output shape, dtype, grid, transform, and expected stats.
- Artifact-class tests verify serving behavior.

---

## Phase 7 — Run Diagnostics CLI

### What it does

Adds a command-line diagnostic tool for completed or failed runs.

Example command:

```bash
python -m app.tools.inspect_run --run-id <id>
```

It can check:

- missing files;
- wrong CRS;
- wrong transform;
- wrong shape;
- bad nodata;
- TIF/NPY mismatch;
- artifact registry mismatch;
- stage manifest mismatch;
- suspicious file size;
- incomplete stage outputs.

### Why we need it

When a run fails, the operator needs a simple way to know what is wrong.

The notebook has many debug cells. The app needs a safer, repeatable version of that debug power.

### Why not copy notebook debug cells

Notebook debug cells inspect random paths, Drive folders, uploaded files, and manual test files. That is not safe or repeatable inside the app.

The CLI should inspect only a known run directory and should produce predictable diagnostics.

### Safety boundary

- CLI reads only known run directories.
- No arbitrary absolute path scanning by default.
- Any exact coordinate details stay local-only.
- Diagnostic output for public/API use must be redacted.

### Acceptance checks

- Unit test: refuses non-run paths.
- Unit test: catches raster shape/transform mismatch.
- Unit test: catches missing sidecars or manifests.
- Integration test: CLI reports healthy sample run as healthy.
- Integration test: CLI reports broken fixture as broken.

---

## Final implementation note

This document is a planning contract only. Each phase should be implemented by a separate Codex goal or pull request.

Do not start Phase 4 raw-local support, Phase 5 AI research, or Phase 6 feature-stack implementation before their safety boundaries and tests are in place.

Best first implementation goal:

```text
Run Diagnostics CLI + Safe Local File Inspector
```

Plain English: this gives the app the notebook's useful checking power without unsafe Drive scanning, coordinate leaking, or unstable classifier exposure.
