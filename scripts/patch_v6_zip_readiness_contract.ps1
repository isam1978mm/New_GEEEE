param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

Write-Host "=== Patch V6 ZIP readiness contract ==="

$patch = @'
from pathlib import Path

path = Path("app/services/v6_real_package.py")
s = path.read_text(encoding="utf-8")

old_import = "from app.services.v6_real_zones import V6RequestZone, request_zones_to_geojson\n"
new_import = old_import + "from app.services.v6_zip_readiness import build_v6_zip_readiness_report\n"
if new_import not in s:
    if old_import not in s:
        raise SystemExit("Could not find v6_real_zones import")
    s = s.replace(old_import, new_import, 1)

old_validation = '''    validation_report = validate_generated_v6_payload_shape(
        payloads=payloads,
        inventory_filename=inventory_path.name,
    )
'''
new_validation = '''    zip_readiness = build_v6_zip_readiness_report(
        zip_path=zip_path,
        inventory_path=inventory_path,
        payload_records=records,
    )
    validation_report = validate_generated_v6_payload_shape(
        payloads=payloads,
        inventory_filename=inventory_path.name,
    )
'''
if new_validation not in s:
    if old_validation not in s:
        raise SystemExit("Could not find validation_report creation block")
    s = s.replace(old_validation, new_validation, 1)

old_update_tail = '''            "real_output_feed": True,
            "package_provenance": provenance,
        }
    )
'''
new_update_tail = '''            "real_output_feed": True,
            "package_provenance": provenance,
            "zip_ready": bool(zip_readiness["zip_ready"]),
            "zip_readiness": zip_readiness,
        }
    )
    if not zip_readiness["zip_ready"]:
        issues = list(validation_report.get("issues", []))
        issues.extend(f"zip_readiness:{issue}" for issue in zip_readiness["issues"])
        validation_report["issues"] = sorted(set(issues))
        validation_report["validation_status"] = GENERATOR_STATUS_INVALID
'''
if new_update_tail not in s:
    if old_update_tail not in s:
        raise SystemExit("Could not find validation_report update tail")
    s = s.replace(old_update_tail, new_update_tail, 1)

path.write_text(s, encoding="utf-8")
print("PATCHED app/services/v6_real_package.py")
'@

$patch | python -

if ($RunTests) {
    Write-Host "=== Run V6 ZIP readiness tests ==="
    pytest tests/unit/test_v6_zip_readiness.py tests/unit/test_v6_real_package.py tests/unit/test_v6_app_flow.py
}
