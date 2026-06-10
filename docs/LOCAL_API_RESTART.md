# Local API Restart

Use this when the local web app is down, for example when `http://127.0.0.1:8007/v2` does not load.

## Start the API on port 8007

From PowerShell:

```powershell
cd C:\Dev\New_GEE
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8007
```

Then open:

```text
http://127.0.0.1:8007/v2
```

## Check health

In another PowerShell window:

```powershell
curl http://127.0.0.1:8007/healthz
curl http://127.0.0.1:8007/readyz
```

Expected meaning:

- `/healthz` checks that FastAPI is alive.
- `/readyz` checks readiness, including Earth Engine service-account initialization.

## If port 8007 is stuck

Find the process using the port:

```powershell
netstat -ano | findstr :8007
```

Use the PID from the last column, then stop it:

```powershell
taskkill /PID <PID> /F
```

Start the API again:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8007
```

## Default README port

The README shows the generic local command with port `8000`:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For this local operator workflow, use port `8007` when the UI expects `/v2` at:

```text
http://127.0.0.1:8007/v2
```

(End of LOCAL_API_RESTART.md.)
