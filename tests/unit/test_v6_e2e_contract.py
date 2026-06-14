from pathlib import Path


DOC = Path("docs/V6_E2E_1.md")
PACKAGE_JSON = Path("frontend-v2/package.json")
PLAYWRIGHT_CONFIG = Path("frontend-v2/playwright.config.ts")
SPEC = Path("frontend-v2/e2e/v6-package-flow.spec.ts")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v6_e2e_files_are_present_and_scripted() -> None:
    assert DOC.is_file()
    assert PLAYWRIGHT_CONFIG.is_file()
    assert SPEC.is_file()

    package_json = _read(PACKAGE_JSON)
    assert '"e2e:v6"' in package_json
    assert "playwright test -c playwright.config.ts e2e/v6-package-flow.spec.ts" in package_json


def test_v6_e2e_spec_mocks_backend_flow_and_retrieves_zip() -> None:
    content = _read(SPEC)

    assert "mockFrozenV6PackageFlow" in content
    assert "/operator/v6/package/review" in content
    assert "/operator/v6/package/generate" in content
    assert "/operator/v6/package/download" in content
    assert "waitForEvent(\"download\")" in content
    assert "V6_REAL_GENERATED.zip" in content


def test_v6_e2e_spec_verifies_operator_token_handoff() -> None:
    content = _read(SPEC)

    assert "local-e2e-operator-token" in content
    assert "requireBearer" in content
    assert "authorization" in content
    assert "Bearer ${OPERATOR_TOKEN}" in content


def test_v6_e2e_doc_preserves_post_freeze_and_safety_boundaries() -> None:
    content = _read(DOC)

    assert "versioned post-freeze follow-up" in content
    assert "does not change frozen V6 generation" in content
    assert "safe metadata only" in content
    assert "no private rows or spatial payload bodies are visible" in content
    assert "Do not alter frozen V6 generation logic unless the issue is proven to be there" in content
