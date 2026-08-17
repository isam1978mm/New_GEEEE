from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PORT = "8007"
LEGACY_DEFAULT_PORT = "8000"


def test_read_first_docs_lock_canonical_local_port() -> None:
    for relative_path in (
        "AGENTS.md",
        "README.md",
        "AUDIT_READ_FIRST_PRIVATE_LOCAL_APP.md",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8-sig")
        assert CANONICAL_PORT in text, relative_path


def test_primary_startup_docs_do_not_use_uvicorn_default_port() -> None:
    for relative_path in ("AGENTS.md", "README.md"):
        text = (ROOT / relative_path).read_text(encoding="utf-8-sig")
        assert f"--port {CANONICAL_PORT}" in text, relative_path
        assert f"--port {LEGACY_DEFAULT_PORT}" not in text, relative_path
        assert f"127.0.0.1:{LEGACY_DEFAULT_PORT}" not in text, relative_path
