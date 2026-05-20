# Live EE Validation

## Purpose

This checklist is for a controlled live Earth Engine validation of the accepted v1 app using service-account-only authentication.

This is an operator checklist. It is not a deployment guide and it does not weaken any redaction, artifact, or parity rule.

## Scope

Use this checklist only after the production-hardening gates before it are complete, especially:

- `H1` production parity contract
- `H2` notebook safety scanner
- `H3` CI
- `H4` reference capture protocol
- `H4.5` IRON_SWIR provenance decision
- `H5` reference-output comparison tests

The live run is a validation of:

- service-account Earth Engine readiness
- canonical ROI execution
- parity against the frozen notebook reference set
- public API safety during and after the run

It is not a claim of real-world detection accuracy.

## Non-Negotiable Rules

- use service-account authentication only
- do not use `ee.Authenticate()`
- do not commit `.env`
- do not commit service-account key files
- do not commit live run artifacts
- do not commit live operator notes containing coordinates or secrets

## Preconditions

Before starting the live validation:

1. Confirm the current full local suite passes:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

2. Confirm notebook safety passes:

```bash
python scripts/check_notebook_safety.py
```

3. Confirm the Earth Engine service-account values are present in `.env`:
   - `EE_SERVICE_ACCOUNT_EMAIL`
   - `EE_SERVICE_ACCOUNT_KEY_PATH`

4. Confirm the canonical ROI reference set exists and is the accepted reference source for parity comparison.

5. Confirm the accepted `IRON_SWIR` rule remains Option A:
   - compare against the corrected analytical/app reference
   - do not compare against a sign-flipped checked-in notebook raster

## Startup

Start the app locally:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Health and Readiness Checks

Liveness:

```bash
curl http://127.0.0.1:8000/healthz
```

Readiness:

```bash
curl http://127.0.0.1:8000/readyz
```

Acceptance criteria:

- `/healthz` succeeds
- `/readyz` succeeds
- readiness failure blocks the live EE validation until the service-account problem is fixed

## Canonical ROI Live Run

Use the accepted canonical ROI and the same input settings used by the frozen notebook reference capture.

Submit the live run:

```bash
curl -X POST http://127.0.0.1:8000/runs \
  -H "Content-Type: application/json" \
  -d "{\"lat\": <canonical-lat>, \"lon\": <canonical-lon>, \"name\": \"canonical-roi-live-validation\"}"
```

Track the run:

```bash
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/<run_id>
```

Acceptance criteria:

- run creation succeeds
- the run progresses through the core stages
- the run reaches a successful terminal state
- no second active run is started during the validation

## Artifact Retrieval for Validation

Retrieve only the artifacts needed for parity checking, and only through the guarded artifact route:

```bash
curl -OJ http://127.0.0.1:8000/runs/<run_id>/artifacts/<artifact_name>
```

Rules:

- do not bypass the guarded artifact endpoint
- do not expose local-sensitive artifacts outside the approved local workflow
- do not move live artifacts into the repo

## Comparison Against Notebook Reference Outputs

Compare the live app outputs against the accepted frozen notebook reference outputs according to:

- [OUTPUT_PARITY_CONTRACT.md](OUTPUT_PARITY_CONTRACT.md)
- [REFERENCE_CAPTURE_PROTOCOL.md](REFERENCE_CAPTURE_PROTOCOL.md)
- [IRON_SWIR_PROVENANCE.md](IRON_SWIR_PROVENANCE.md)

Comparison checklist:

1. Use the same canonical ROI and input settings.
2. Compare the required parity artifacts.
3. Apply the documented tolerance for each artifact.
4. Treat any undocumented difference as a parity failure.
5. Apply the accepted `IRON_SWIR` Option A rule:
   - compare against the corrected analytical/app reference using `(B11 - B12) / (B11 + B12)`
   - do not compare against a sign-flipped checked-in notebook raster

Acceptance criteria:

- all required comparisons pass
- any difference is either zero or already documented as `PARITY_CORRECTS`

## Public API Leakage Checks

During and after the live run, verify that public API responses do not leak forbidden content.

Check:

```bash
curl http://127.0.0.1:8000/runs
curl http://127.0.0.1:8000/runs/<run_id>
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

Verify the public responses contain none of the following:

- latitude
- longitude
- raw coordinates
- geometry
- bounds
- bbox
- CRS transforms
- filesystem paths
- absolute paths
- hashes
- checksums
- fingerprints
- raw errors or tracebacks

Artifact-surface checks:

- experimental outputs are not listed
- `FILESYSTEM_ONLY` outputs are not downloadable
- the API does not expose coordinate-bearing CSV columns in public outputs

## Failure Handling

If the live run fails:

1. stop using the failed result as parity evidence
2. record the failure privately without committing secrets or coordinates
3. determine whether the failure is:
   - service-account readiness
   - Earth Engine runtime
   - parity mismatch
   - public API leakage
4. if the issue is a parity failure, follow the rollback rule from [OUTPUT_PARITY_CONTRACT.md](OUTPUT_PARITY_CONTRACT.md)

If a parity mismatch is found, do not accept production readiness on the basis of partial success.

## Post-Run Cleanup

After the validation:

1. keep live artifacts in approved local storage only
2. do not commit `.env`
3. do not commit key files
4. do not commit live artifacts
5. do not commit private ROI notes or operator notes with coordinates

If a durable record is needed, commit only sanitized documentation or non-sensitive summaries that comply with the redaction contract.

## Completion Record

Record the following privately or in sanitized operator notes:

- date of live validation
- operator identity or role
- app revision or git SHA
- notebook reference revision or manifest identifier
- canonical ROI label
- readiness result
- run ID
- parity result
- whether any `PARITY_CORRECTS` differences were encountered
- whether any leakage checks failed

The live EE validation is complete only when:

- `/readyz` succeeds
- the canonical ROI live run completes successfully
- parity comparison against the frozen reference outputs passes under the accepted rules
- public API leakage checks pass
