# Directory Tree — GEE Screening Web App v0.5

This tree matches PRD v0.5: SQLite for v1, no Docker requirement, FastAPI `BackgroundTasks`, local-only bind by default, and the experimental classifier included in v1 as an env-gated, CLI-only, neutral-terms-only module.

```text
gee_screening_app/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.optional.yml        # optional v2 Postgres/worker stack only; not required for v1
│
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_runs_and_artifacts.py
│
├── scripts/
│   ├── check_forbidden_terms.py       # blocks source-notebook labels outside approved docs
│   ├── check_no_ee_authenticate.py    # blocks ee.Authenticate()
│   ├── check_no_direct_streaming.py   # AST policy: no direct FileResponse/open/sendfile in routes
│   └── check_secret_patterns.py       # blocks service-account keys / .env leaks
│
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI; docs/openapi disabled; binds 127.0.0.1 by default
│   ├── config.py                      # pydantic-settings; reads .env
│   ├── deps.py                        # DB session, EE session, local bind guards
│   ├── errors.py                      # StageError, GridDriftError, ArtifactServeViolation, etc.
│   ├── logging_config.py              # structured JSON logs + redaction formatter
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── runs.py                    # POST /runs, GET /runs, GET /runs/{id}
│   │   ├── artifacts.py               # GET /runs/{id}/artifacts/{name}; delegates to serve_artifact_response()
│   │   ├── health.py                  # GET /healthz, GET /readyz
│   │   └── errors.py                  # custom public-safe FastAPI exception handlers
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── errors.py                  # ErrorPublic
│   │   ├── run.py                     # RunCreate, RunPublic, RunInternal
│   │   ├── artifact.py                # ArtifactPublic, ArtifactInternal, ArtifactClass enum
│   │   ├── grid.py                    # GridManifest internal schema; public view omits CRS origin/transform
│   │   └── status.py                  # run/stage status enums
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py                 # SQLite + aiosqlite; short-lived transaction helpers
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── run.py
│   │       └── artifact.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── artifact_policy.py         # can_serve_artifact()
│   │   ├── artifact_response.py       # only approved file-streaming helper
│   │   ├── ee_session.py              # service-account ONLY; no ee.Authenticate()
│   │   ├── grid.py                    # low-level GRID helpers
│   │   ├── network_guard.py           # bind-address checks, ALLOW_NETWORK_BIND warnings
│   │   ├── redaction.py               # redact() + verify_redacted(); the HTTP boundary
│   │   ├── run_state.py               # queued/running/done/failed/stale_failed transitions
│   │   └── storage.py                 # run dirs, path normalization, artifact writes, hashes
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py            # walks core stages only; never imports stages_experimental
│   │   ├── manifest.py                # RUN/stage manifest read/write
│   │   ├── _base.py                   # Stage protocol, StageResult, ParityCategory
│   │   │
│   │   ├── stages/                    # DEFENSIBLE CORE — always loaded
│   │   │   ├── __init__.py
│   │   │   ├── grid.py                # grid construction stage; calls services/grid.py
│   │   │   ├── dem.py
│   │   │   ├── zero_shift.py
│   │   │   ├── sar_rtc.py
│   │   │   ├── dem_derivatives.py
│   │   │   ├── thermal.py
│   │   │   ├── s2_indices.py          # includes corrected IRON_SWIR denominator
│   │   │   ├── hypercube.py
│   │   │   ├── pca_anomaly.py
│   │   │   ├── object_extract.py
│   │   │   └── alignment_qa.py
│   │   │
│   │   └── stages_experimental/       # INCLUDED IN v1, but isolated and CLI-only
│   │       ├── __init__.py            # raises ImportError unless ENABLE_EXPERIMENTAL=1
│   │       ├── README.md              # local-only, experimental, no validation claim
│   │       ├── run.py                 # CLI: python -m app.pipeline.stages_experimental.run --run-id <id>
│   │       ├── classifier.py          # neutralized reproduction of notebook classifier logic
│   │       ├── classes.py             # Class_A ... Class_N only; no source-notebook labels
│   │       ├── inputs.py              # validates completed RUN + required artifacts
│   │       └── outputs.py             # writes Class IV filesystem-only outputs under experimental/
│   │
│   └── workers/
│       ├── __init__.py
│       └── background.py              # FastAPI BackgroundTasks wrapper; not a separate worker process
│
├── tests/
│   ├── unit/
│   │   ├── test_grid.py
│   │   ├── test_redaction.py
│   │   ├── test_public_errors.py
│   │   ├── test_zero_shift.py
│   │   ├── test_ee_session.py
│   │   ├── test_s2_indices.py         # asserts IRON_SWIR denominator is B11+B12
│   │   ├── test_artifact_policy.py    # can_serve_artifact()
│   │   ├── test_artifact_response.py  # traversal/normalization/guard coverage
│   │   ├── test_logging_redaction.py
│   │   ├── test_run_state_machine.py
│   │   ├── test_experimental_gate.py
│   │   └── test_experimental_neutral_terms.py
│   │
│   ├── integration/
│   │   ├── test_pipeline.py           # full core RUN on fixed reference ROI
│   │   ├── test_api_redaction.py
│   │   ├── test_artifact_classes.py
│   │   ├── test_bind_address.py
│   │   ├── test_stale_run_startup.py
│   │   ├── test_sqlite_session_discipline.py
│   │   └── test_experimental_cli.py   # CLI-only classifier contract on frozen completed RUN fixture
│   │
│   ├── policy/
│   │   ├── test_forbidden_terms.py
│   │   ├── test_no_ee_authenticate.py
│   │   ├── test_no_direct_file_streaming.py
│   │   ├── test_no_experimental_web_refs.py
│   │   ├── test_no_openapi_docs.py
│   │   └── test_secret_patterns.py
│   │
│   ├── notebook_parity/
│   │   ├── README.md                  # core stages only; classifier is not notebook parity
│   │   ├── KNOWN_EXCEPTIONS.md        # e.g., IRON_SWIR correction
│   │   ├── test_dem_parity.py
│   │   ├── test_sar_parity.py
│   │   ├── test_s2_parity.py
│   │   ├── test_dem_derivatives_parity.py
│   │   ├── test_thermal_parity.py
│   │   ├── test_hypercube_parity.py
│   │   ├── test_pca_parity.py
│   │   ├── test_objects_parity.py
│   │   ├── test_alignment_parity.py
│   │   └── fixtures/
│   │       └── reference_run/         # captured notebook outputs at known safe ROI
│   │
│   └── fixtures/
│       ├── sample_grid.json
│       ├── completed_run/             # minimal completed RUN fixture for experimental CLI
│       └── redaction_cases.json
│
├── docs/
│   ├── SAFETY_CONSTANTS.md
│   ├── PIPELINE.md
│   ├── PARITY_PROTOCOL.md
│   ├── PARITY_EXCEPTIONS.md
│   ├── ARTIFACT_TAXONOMY.md
│   ├── REDACTION_CONTRACT.md
│   ├── EXPERIMENTAL_MODULE.md
│   ├── CLASS_MAPPING.md              # PRIVATE; only approved place for source-notebook label mapping
│   ├── NOTEBOOK_MIGRATION_MATRIX.md  # PRIVATE unless scrubbed
│   └── DIRECTORY_SKETCH.md
│
└── frontend/
    ├── index.html
    ├── app.js
    ├── style.css
    ├── config.js                     # external tiles disabled unless ALLOW_EXTERNAL_TILES set
    └── vendor/                       # vendored JS/CSS only; no CDN-loaded scripts/fonts
```

## Notes

- The core orchestrator must never import `app.pipeline.stages_experimental`.
- Experimental classifier outputs are Class IV and never appear in API artifact lists or SPA views.
- The default install path can run the core app without experimental-only dependencies. The experimental CLI may require `pip install .[experimental]`.
- `docs/CLASS_MAPPING.md` and `docs/NOTEBOOK_MIGRATION_MATRIX.md` are project-private unless scrubbed; the publishability target is `app/`, `tests/`, hooks, and generated runtime behavior.
