from __future__ import annotations

from app.services.v6_package_contract import (
    CATEGORY_NAMES,
    SOURCE_LOCK_IDENTITY_FIELDS,
    V6CsvHeaderContract,
    category_for_file,
    summarize_geojson_top_level,
    validate_csv_headers,
    validate_payload_file_names,
)


def _complete_synthetic_names() -> list[str]:
    return [
        "lawful_gee_candidate_scout_top_25_20260101T120000Z.csv",
        "lawful_gee_candidate_scout_top_25_20260101T120000Z.geojson",
        "top25_enhanced_v6.csv",
        "top25_enhanced_v6.geojson",
        "quality_diagnostics_all_cells_v6.csv",
        "stable_candidate_priority_list_v6.csv",
        "request_zones_v6.csv",
        "request_zones_v6.geojson",
        "paid_imagery_quote_template_v6.csv",
        "paid_imagery_quote_comparison_v6.csv",
        "paid_archive_request_summary.txt",
        "visual_inspection_map.html",
        "synthetic_inventory.json",
    ]


def test_category_mapping_covers_known_v6_roles() -> None:
    assert set(CATEGORY_NAMES) == {
        "candidate_tables",
        "request_zones",
        "diagnostics",
        "quote_templates",
        "summary_text",
        "visual_map",
        "unknown",
    }
    assert category_for_file("lawful_gee_candidate_scout_top_25_20260101T120000Z.csv") == (
        "candidate_tables"
    )
    assert category_for_file("request_zones_v6.geojson") == "request_zones"
    assert category_for_file("quality_diagnostics_all_cells_v6.csv") == "diagnostics"
    assert category_for_file("paid_imagery_quote_template_v6.csv") == "quote_templates"
    assert category_for_file("paid_archive_request_summary.txt") == "summary_text"
    assert category_for_file("visual_inspection_map.html") == "visual_map"
    assert category_for_file("extra.csv") == "unknown"


def test_validate_payload_file_names_accepts_complete_synthetic_package() -> None:
    result = validate_payload_file_names(
        _complete_synthetic_names(),
        inventory_filename="synthetic_inventory.json",
    )

    assert result.valid is True
    assert result.issues == ()
    assert result.warnings == ()


def test_validate_payload_file_names_rejects_missing_and_unsafe_members() -> None:
    names = _complete_synthetic_names()
    names.remove("request_zones_v6.csv")
    names.remove("lawful_gee_candidate_scout_top_25_20260101T120000Z.geojson")
    names.append("nested/unsafe.csv")
    names.append("unexpected.csv")

    result = validate_payload_file_names(
        names,
        inventory_filename="synthetic_inventory.json",
    )

    assert result.valid is False
    assert "missing_required_payload:request_zones_v6.csv" in result.issues
    assert (
        "missing_required_payload:lawful_gee_candidate_scout_top_25_<timestamp>.geojson"
        in result.issues
    )
    assert "unsafe_member_name:nested/unsafe.csv" in result.issues
    assert "unknown_payload:unexpected.csv" in result.warnings


def test_validate_csv_headers_checks_headers_only() -> None:
    contract = V6CsvHeaderContract(
        file_name="synthetic.csv",
        required_headers=("sample_id", "score"),
        exact_headers=("sample_id", "score", "review_flag"),
    )

    result = validate_csv_headers(["sample_id", "score", "review_flag"], contract)

    assert result.valid is True
    assert result.issues == ()


def test_validate_csv_headers_reports_missing_duplicate_and_exact_mismatch() -> None:
    contract = V6CsvHeaderContract(
        file_name="synthetic.csv",
        required_headers=("sample_id", "score"),
        exact_headers=("sample_id", "score", "review_flag"),
    )

    result = validate_csv_headers(["sample_id", "sample_id", "other"], contract)

    assert result.valid is False
    assert "duplicate_csv_header:synthetic.csv:sample_id" in result.issues
    assert "missing_csv_header:synthetic.csv:score" in result.issues
    assert "csv_header_set_mismatch:synthetic.csv" in result.issues


def test_summarize_geojson_top_level_ignores_feature_bodies() -> None:
    payload = {
        "type": "FeatureCollection",
        "name": "synthetic_collection",
        "features": [{"private_value": "do_not_surface"}],
    }

    summary = summarize_geojson_top_level(payload)

    assert summary.valid is True
    assert summary.top_level_keys == ("features", "name", "type")
    assert summary.document_type == "FeatureCollection"
    assert summary.features_is_list is True
    assert summary.feature_count == 1
    assert "do_not_surface" not in repr(summary)
    assert "private_value" not in repr(summary)


def test_source_lock_identity_fields_are_metadata_only() -> None:
    assert SOURCE_LOCK_IDENTITY_FIELDS == (
        "contract_version",
        "zip_filename",
        "zip_size_bytes",
        "zip_sha256",
        "inventory_filename",
        "inventory_size_bytes",
        "inventory_sha256",
        "payload_count",
        "zip_entry_count_including_inventory",
        "payload_file_names",
        "payload_file_sizes",
        "payload_file_sha256_values",
        "csv_header_sets",
        "geojson_top_level_roles",
        "category_counts",
    )
