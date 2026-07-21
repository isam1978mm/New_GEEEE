from __future__ import annotations

from app.pipeline.parity.private_cli_classifier import CLASS_IDS as PRIVATE_COMPATIBILITY_CLASS_IDS
from app.pipeline.stages.classifier_core import (
    COMPATIBILITY_ONLY_CLASS_IDS,
    CORE_EMITTABLE_CLASS_IDS,
    ClassId,
    NeutralFeatureVector,
    classify_feature_vector,
)


def _classify_uniform_score(score: float) -> ClassId:
    result = classify_feature_vector(
        NeutralFeatureVector(
            signal_mean=score,
            signal_peak=score,
            signal_spread=score,
        )
    )
    return result.class_id


def test_core_and_compatibility_ids_form_a_complete_disjoint_partition() -> None:
    core = set(CORE_EMITTABLE_CLASS_IDS)
    compatibility = set(COMPATIBILITY_ONLY_CLASS_IDS)

    assert core.isdisjoint(compatibility)
    assert core | compatibility == set(ClassId)
    assert COMPATIBILITY_ONLY_CLASS_IDS == (
        ClassId.Class_K,
        ClassId.Class_L,
        ClassId.Class_M,
        ClassId.Class_N,
    )


def test_every_core_class_id_is_reachable_by_the_normal_selector() -> None:
    representative_scores = (
        0.95,
        0.85,
        0.75,
        0.65,
        0.55,
        0.45,
        0.35,
        0.25,
        0.15,
        0.05,
    )

    emitted = tuple(_classify_uniform_score(score) for score in representative_scores)

    assert emitted == CORE_EMITTABLE_CLASS_IDS


def test_normal_selector_never_emits_compatibility_only_ids() -> None:
    compatibility = set(COMPATIBILITY_ONLY_CLASS_IDS)

    for index in range(1001):
        emitted = _classify_uniform_score(index / 1000.0)
        assert emitted in CORE_EMITTABLE_CLASS_IDS
        assert emitted not in compatibility


def test_private_compatibility_vocabulary_still_preserves_all_a_to_n_ids() -> None:
    assert PRIVATE_COMPATIBILITY_CLASS_IDS == tuple(class_id.value for class_id in ClassId)
