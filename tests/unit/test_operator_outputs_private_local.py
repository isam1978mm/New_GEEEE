from __future__ import annotations

from app.services.operator_outputs import (
    is_operator_visible_relative_path,
    is_safe_operator_output_relative_path,
)


def test_private_local_operator_outputs_allow_unlisted_safe_files() -> None:
    assert is_operator_visible_relative_path("unlisted/private_result.kmz") is True
    assert is_operator_visible_relative_path("custom/deep/output/result.npy") is True
    assert is_operator_visible_relative_path("AI_READY_640/Secret_Custom_Result.tif") is True


def test_private_local_operator_outputs_still_block_actual_sensitive_files() -> None:
    blocked = [
        "../outside.txt",
        ".env",
        "PATH_MAP.local.json",
        "run.sqlite",
        "debug.log",
        "credentials.json",
        "service-account-key.json",
        "private_key.pem",
    ]
    for relative_path in blocked:
        assert is_safe_operator_output_relative_path(relative_path) is False
        assert is_operator_visible_relative_path(relative_path) is False
