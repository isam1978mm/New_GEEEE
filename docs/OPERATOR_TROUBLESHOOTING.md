# Operator Troubleshooting

This document covers local UI/runtime checks only. It must not be used as a reason to change science, GRID, SAR, notebook parity, tolerances, reference-manifest behavior, or public-safety redaction rules.

## Known-good local context

- Local repo path used during the UI smoke work: `C:\Dev\New_GEE`
- Local UI/API port used during the successful run: `8007`
- Representative successful run ID: `669456b0-58a7-4b41-9961-4663b919a990`
- Expected public-safe run artifacts for that run:
  - `objects_index.csv`
  - `clusters_summary.csv`
  - `alignment_qa.json`
  - `alignment_audit.json`
  - `alignment_mask_selection.json`

## Restart rule after code or `.env` changes

A browser hard reload is not enough after backend code, frontend assets served by FastAPI, or `.env` changes. Restart the FastAPI server first, then hard reload the browser.

PowerShell:

```powershell
cd C:\Dev\New_GEE

# Optional: identify the process currently listening on the local app port.
Get-NetTCPConnection -LocalPort 8007 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess

# Stop only the uvicorn/python process that you intentionally started for this app.
# Replace <PID> with the OwningProcess value after verifying it is the app server.
Stop-Process -Id <PID>

# Start the app on the same local port used for the successful UI run.
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8007
```

Then hard reload the browser tab:

```text
Ctrl + F5
```

## Readiness check before starting or inspecting runs

Before queuing a new run or judging a failed one, confirm the app is ready on the actual port in use.

PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8007/readyz | ConvertTo-Json -Depth 8
```

Do not start a fresh run when readiness reports `ee_not_ready`. Fix the Earth Engine runtime configuration first, restart the server, then check `/readyz` again.

## Earth Engine service-account troubleshooting

A DEM stage that fails immediately, especially with `/readyz` reporting `ee_not_ready`, usually means the local Earth Engine service-account configuration is not usable by the running server process.

Check the `.env` entry and the target file path:

```powershell
cd C:\Dev\New_GEE

Select-String -Path .env -Pattern '^EE_SERVICE_ACCOUNT_KEY_PATH=|^NOTEBOOK_REFERENCE_BUNDLE_DIR='

$keyLine = (Select-String -Path .env -Pattern '^EE_SERVICE_ACCOUNT_KEY_PATH=').Line
$keyPath = $keyLine.Split('=', 2)[1].Trim().Trim('"')
Test-Path $keyPath
```

The key path should resolve to an existing JSON key file. Watch for accidental concatenation in `.env`, for example a single line like:

```text
EE_SERVICE_ACCOUNT_KEY_PATH=...jsonNOTEBOOK_REFERENCE_BUNDLE_DIR=...
```

That must be split into two separate lines:

```text
EE_SERVICE_ACCOUNT_KEY_PATH=...
NOTEBOOK_REFERENCE_BUNDLE_DIR=...
```

After fixing `.env`, restart the FastAPI server and re-check `/readyz`. Browser hard reload alone will not reload backend environment variables.

## Verify the successful run outputs in the UI

Use the already successful run when possible:

```text
669456b0-58a7-4b41-9961-4663b919a990
```

Expected UI behavior:

- State shows `Done`.
- Current stage shows `Completed`.
- Stage checklist shows completed stages.
- Status history includes the run lifecycle through completion.
- Run outputs shows 5 public-safe artifacts.
- Artifact names include extensions.

## Verify `objects_index.csv` download filename

The UI download link for `objects_index.csv` should use the filename-ending route:

```text
http://127.0.0.1:8007/runs/669456b0-58a7-4b41-9961-4663b919a990/artifacts/objects_index/download/objects_index.csv
```

Browser verification:

1. Open the app on `http://127.0.0.1:8007`.
2. Load or select run `669456b0-58a7-4b41-9961-4663b919a990`.
3. In `Run outputs`, click `objects_index.csv`.
4. Confirm the saved filename is exactly `objects_index.csv`.

PowerShell HTTP sanity check:

```powershell
$runId = '669456b0-58a7-4b41-9961-4663b919a990'
$base = 'http://127.0.0.1:8007'
$url = "$base/runs/$runId/artifacts/objects_index/download/objects_index.csv"

$response = Invoke-WebRequest -Uri $url -Method Get
$response.Headers['Content-Disposition']
$response.Content.Substring(0, [Math]::Min(200, $response.Content.Length))
```

A healthy response should expose a CSV artifact and should advertise `objects_index.csv` through either the URL filename segment, `Content-Disposition`, or both. If the browser still saves without `.csv`, inspect the actual link target in DevTools or by copying the link address. It should end with:

```text
/runs/<run_id>/artifacts/objects_index/download/objects_index.csv
```

## Dirty working tree guardrails

Do not commit these unless intentionally reviewed and adopted:

- `.env`
- `PATH_MAP.local.json`
- reference bundle binaries
- `data/runs/`
- `data/reports/`
- `gee_screening_app.egg-info/`
- `uv.lock`
- unrelated `pyproject.toml` changes

For a quick local check:

```powershell
git status --short
git log --oneline -5
```

If `pyproject.toml`, `uv.lock`, or `gee_screening_app.egg-info/` are still dirty, review them intentionally before deciding whether to clean, ignore, or adopt them. Do not include them in a UI/runtime docs-only commit by accident.
