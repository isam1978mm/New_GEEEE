param(
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

Write-Host "=== Mark PRD v0.5 as historical context ==="

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$prdPath = Join-Path $repoRoot "docs\PRD_v0.5.md"
if (-not (Test-Path $prdPath)) {
    throw "Missing docs\PRD_v0.5.md"
}

$text = Get-Content -Raw -Encoding UTF8 $prdPath
$notice = @'

> **Supersession notice — 2026-07-15:** This PRD v0.5 is historical context only. It is not the active source of truth for current audits regarding classifier placement, classifier API/frontend visibility, public-SaaS severity assumptions, or the local-private core-classifier execution model. Future audits must read `docs/LOCAL_PRIVATE_CORE_CLASSIFIER_EXECUTION_PLAN_2026-07-15.md` and `AUDIT_DO_NOT_BREAK_CONTRACTS.md` before using this PRD.
'@

if ($text -like "*Supersession notice — 2026-07-15*") {
    Write-Host "PRD already contains supersession notice."
} else {
    $marker = "**Storage backend:** SQLite (PostgreSQL/Supabase deferred to v2)`r`n"
    if (-not $text.Contains($marker)) {
        $marker = "**Storage backend:** SQLite (PostgreSQL/Supabase deferred to v2)`n"
    }
    if (-not $text.Contains($marker)) {
        throw "Could not find PRD metadata insertion point."
    }
    $text = $text.Replace($marker, $marker + $notice, 1)
    Set-Content -Encoding UTF8 -NoNewline -Path $prdPath -Value $text
    Write-Host "Inserted supersession notice into docs\PRD_v0.5.md"
}

if ($RunTests) {
    Write-Host "=== Verify docs marker ==="
    git grep -n "Supersession notice" docs
}
