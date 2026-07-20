from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_depth_s1_matched_features_batched as batched


class _FakePercentileReducer:
    def __init__(self) -> None:
        self.combine_kwargs: dict[str, Any] | None = None

    def combine(self, **kwargs: Any) -> object:
        self.combine_kwargs = kwargs
        return self


class _FakeReducerApi:
    percentile_reducer = _FakePercentileReducer()
    count_reducer = object()

    @classmethod
    def percentile(cls, percentiles: list[int], output_names: list[str]) -> _FakePercentileReducer:
        assert percentiles == [25, 50, 75]
        assert output_names == ["p25", "median", "p75"]
        cls.percentile_reducer = _FakePercentileReducer()
        return cls.percentile_reducer

    @classmethod
    def count(cls) -> object:
        return cls.count_reducer


class _FakeEe:
    Reducer = _FakeReducerApi


def test_reducer_combine_uses_string_prefix_and_shared_inputs_keyword() -> None:
    returned = batched.build_percentile_count_reducer(_FakeEe)
    reducer = _FakeReducerApi.percentile_reducer

    assert returned is reducer
    assert reducer.combine_kwargs == {
        "reducer2": _FakeReducerApi.count_reducer,
        "outputPrefix": "",
        "sharedInputs": True,
    }
    assert isinstance(reducer.combine_kwargs["outputPrefix"], str)
    assert reducer.combine_kwargs["sharedInputs"] is True


def test_batched_query_defaults_to_corrected_single_batch_query(monkeypatch) -> None:
    called_batches: list[list[str]] = []

    def corrected_query(**kwargs: Any) -> list[dict[str, Any]]:
        rows = kwargs["manifest_rows"]
        called_batches.append([str(row["image_id"]) for row in rows])
        return [
            {
                "image_id": row["image_id"],
                "timestamp": row["timestamp"],
                "site": {},
                "background": {},
            }
            for row in rows
        ]

    monkeypatch.setattr(
        batched,
        "query_exact_s1_feature_summaries_fixed",
        corrected_query,
    )
    rows = [
        {"image_id": "S1A_PRE_001", "timestamp": "2019-01-01T00:00:00+00:00"},
        {"image_id": "S1A_POST_001", "timestamp": "2021-01-01T00:00:00+00:00"},
    ]

    returned = batched.query_exact_s1_feature_summaries_batched(
        manifest_rows=rows,
        site_geometry_payload={"type": "Polygon", "coordinates": []},
        background_geometry_payload={"type": "Polygon", "coordinates": []},
        resolution_meters=10,
        batch_size=1,
    )

    assert called_batches == [["S1A_PRE_001"], ["S1A_POST_001"]]
    assert [row["image_id"] for row in returned] == ["S1A_PRE_001", "S1A_POST_001"]
