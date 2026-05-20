# VPS deployment goals

This file defines deployment-planning goals `D0` through `D7` for the accepted v1 application.

Deployment goals do not start until production-hardening has reached at least:

- `H1` — Production parity contract
- `H2` — Notebook safety scanner
- `H3` — GitHub Actions CI

The deployment target remains constrained by the v1 safety model:

- no Docker
- no PostgreSQL
- no `ee.Authenticate()`
- no public network exposure
- `ALLOW_NETWORK_BIND=false`
- FastAPI remains bound to `127.0.0.1`
- Earth Engine remains service-account only

The purpose of this plan is deployment preparation, not feature expansion.

---

# Goal D0 — Deployment prerequisites and acceptance boundary

Requirements:

- Confirm v1 is accepted and production-hardening has reached at least `H1`, `H2`, and `H3`.
- Confirm the current full local suite passes before any VPS deployment work proceeds.
- Confirm deployment remains local-surface only:
  - `ALLOW_NETWORK_BIND=false`
  - no reverse proxy that exposes the app publicly
  - no direct `0.0.0.0` bind
- Confirm the operator understands that VPS deployment is still for operator-local access only, typically through SSH tunneling.

Validation:

```bash
git status
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal D1 — VPS host baseline and hardening checklist

Requirements:

- Define supported VPS OS baseline, package prerequisites, Python version, filesystem layout, and service account secret placement.
- Define a dedicated non-root service user for the app, but keep the plan template-safe:
  - no hardcoded username
  - no hardcoded absolute app path
- Define firewall posture:
  - SSH allowed
  - app port not publicly exposed
  - localhost-only application bind
- Define SQLite/data directory placement and file-permission expectations.
- Define journald/log rotation expectations.

Validation:

```bash
python --version
id <service-user>
ss -ltnp
```

---

# Goal D2 — Application install and environment bootstrap

Requirements:

- Define deployment steps for:
  - cloning or copying the repo
  - creating a virtual environment
  - installing the project with dev dependencies if parity/test execution is required on-host
  - creating `.env`
  - storing the Earth Engine service-account key outside the repo
- Keep the environment template-safe:
  - no hardcoded local workstation path
  - no hardcoded VPS user
  - no committed secrets
- Require `ALLOW_NETWORK_BIND=false`.
- Require service-account-only Earth Engine configuration.

Validation:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -c "from app.config import Settings; print(Settings().bind_host)"
```

---

# Goal D3 — On-host parity and safety preflight

Requirements:

- Before enabling any long-running service, run the local suite on the VPS host environment.
- Confirm parity-related tests are included, not only unit or integration tests.
- Confirm the deployment environment does not introduce path, permission, or temp-directory regressions.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal D4 — Systemd service definition

Requirements:

- Define a template-safe `systemd` unit for the app.
- The unit must not hardcode a specific local username or local absolute path.
- The unit must:
  - run under a dedicated service user/group placeholder
  - point to a configurable working directory placeholder
  - point to a configurable virtualenv placeholder
  - load environment from a configurable `.env` path
  - restart on failure
  - keep bind host at `127.0.0.1`
  - keep `ALLOW_NETWORK_BIND=false`
- Do not introduce Docker, gunicorn worker farms, Celery, Redis, PostgreSQL, or public ingress.

Validation:

```bash
systemctl daemon-reload
systemctl enable <app-service>
systemctl status <app-service>
journalctl -u <app-service> --no-pager -n 100
```

---

# Goal D5 — Operator access path and tunnel workflow

Requirements:

- Define SSH-tunnel-only operator access to the VPS-hosted app.
- Clarify that `tunnel.sh` is run from the operator machine, not from the VPS.
- Document the expected tunnel behavior:
  - remote app remains bound to `127.0.0.1`
  - operator machine forwards a local port to the VPS localhost port
- Do not define any public URL, TLS listener, reverse proxy exposure, or open ingress for the app itself.

Validation:

```bash
ssh -L <local-port>:127.0.0.1:<remote-port> <user>@<host>
curl http://127.0.0.1:<remote-port>/healthz
curl http://127.0.0.1:<local-port>/healthz
```

---

# Goal D6 — Data handling, backups, and recovery

Requirements:

- Define backup expectations for:
  - SQLite database
  - `data/runs/`
  - service manifests
  - local-only experimental outputs if explicitly retained
- Define restore expectations and stale-run recovery steps.
- Preserve artifact-class and redaction constraints during backup/restore handling.
- Do not export or publish sensitive artifacts.

Validation:

```bash
sqlite3 <db-path> ".tables"
python -m app.main --help
```

---

# Goal D7 — Deployment acceptance gate

Requirements:

- Confirm VPS deployment is still local-surface only and not publicly exposed.
- Confirm the current full suite passes in the deployment-ready environment.
- Run the safety scanners/checks required for deployment acceptance:
  - `python scripts/check_no_ee_authenticate.py`
  - `python scripts/check_no_direct_streaming.py`
  - `python scripts/check_notebook_safety.py` if present
- Confirm Earth Engine remains service-account only.
- Confirm `ALLOW_NETWORK_BIND=false`.
- Confirm no Docker, no PostgreSQL, and no public network exposure were introduced.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
python scripts/check_no_ee_authenticate.py
python scripts/check_no_direct_streaming.py
python scripts/check_notebook_safety.py
systemctl status <app-service>
curl http://127.0.0.1:<remote-port>/healthz
curl http://127.0.0.1:<remote-port>/readyz
ss -ltnp
```

If `scripts/check_notebook_safety.py` is not present yet, skip that one check explicitly and record the reason.
