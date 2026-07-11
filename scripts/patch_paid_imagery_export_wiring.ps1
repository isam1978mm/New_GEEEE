param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

Write-Host "=== Patch paid imagery export wiring ==="

$pythonPatch = @'
from pathlib import Path

path = Path("app/services/v6_app_flow.py")
s = path.read_text(encoding="utf-8")

old_generate = '''    input_path = _private_input_path(settings, run_id)
    if not input_path.is_file():
        return _observe_and_return(
            action="generate",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=_not_available(run_id=run_id, request_id=access_context.request_id),
        )
'''

new_generate = '''    input_path = _private_input_path(settings, run_id)
    if not input_path.is_file():
        from app.services.v6_local_package_input import ensure_local_v6_package_input

        ensure_local_v6_package_input(settings=settings, run_id=run_id)
    if not input_path.is_file():
        return _observe_and_return(
            action="generate",
            settings=settings,
            run_id=run_id,
            access_context=access_context,
            result=_not_available(run_id=run_id, request_id=access_context.request_id),
        )
'''

if old_generate not in s:
    raise SystemExit("Could not find generate_private_v6_package missing-input block")
s = s.replace(old_generate, new_generate, 1)

old_loader = '''    candidates = tuple(_candidate_from_mapping(row) for row in candidates_raw)
    zones = tuple(_zone_from_mapping(row) for row in zones_raw)
    return V6RealPackageInputs(
        run_id=_required_str(payload.get("run_id"), "run_id"),
        timestamp=_required_str(payload.get("timestamp"), "timestamp"),
        scored_candidates=candidates,
        request_zones=zones,
    )
'''

new_loader = '''    candidates = tuple(_candidate_from_mapping(row) for row in candidates_raw)
    zones = tuple(_zone_from_mapping(row) for row in zones_raw)
    optional_kwargs: dict[str, Any] = {}
    for key in (
        "source_mode",
        "score_basis",
        "geometry_basis",
        "package_provenance",
        "placeholder_map_label",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            optional_kwargs[key] = value.strip()
    for key in (
        "fallback_score_used",
        "fallback_geometry_used",
        "frozen_notebook_parity_claimed",
    ):
        value = payload.get(key)
        if isinstance(value, bool):
            optional_kwargs[key] = value
    return V6RealPackageInputs(
        run_id=_required_str(payload.get("run_id"), "run_id"),
        timestamp=_required_str(payload.get("timestamp"), "timestamp"),
        scored_candidates=candidates,
        request_zones=zones,
        **optional_kwargs,
    )
'''

if old_loader not in s:
    raise SystemExit("Could not find load_v6_real_package_inputs return block")
s = s.replace(old_loader, new_loader, 1)

path.write_text(s, encoding="utf-8")
print("PATCHED app/services/v6_app_flow.py")
'@

$pythonPatch | python -
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($RunTests) {
    Write-Host "=== Run paid imagery export wiring tests ==="
    pytest tests/unit/test_v6_paid_imagery_export_wiring.py tests/unit/test_v6_app_flow.py tests/unit/test_v6_local_package_input.py
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
