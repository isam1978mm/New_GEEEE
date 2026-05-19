from __future__ import annotations

from dataclasses import dataclass

from app.pipeline.stages_experimental.classes import CLASS_BY_ID, ClassId


@dataclass(frozen=True, slots=True)
class NeutralFeatureVector:
    signal_mean: float
    signal_peak: float
    signal_spread: float


@dataclass(frozen=True, slots=True)
class NeutralClassification:
    class_id: ClassId
    class_score: float
    class_family: str
    classifier_version: str


def classify_feature_vector(feature_vector: NeutralFeatureVector) -> NeutralClassification:
    score = _normalized_score(feature_vector)
    class_id = _select_class_id(score)
    class_definition = CLASS_BY_ID[class_id]
    return NeutralClassification(
        class_id=class_id,
        class_score=score,
        class_family=class_definition.class_family,
        classifier_version=class_definition.classifier_version,
    )


def _normalized_score(feature_vector: NeutralFeatureVector) -> float:
    raw_score = (
        feature_vector.signal_mean * 0.45
        + feature_vector.signal_peak * 0.4
        + feature_vector.signal_spread * 0.15
    )
    return max(0.0, min(1.0, round(raw_score, 6)))


def _select_class_id(score: float) -> ClassId:
    if score >= 0.9:
        return ClassId.Class_A
    if score >= 0.8:
        return ClassId.Class_B
    if score >= 0.7:
        return ClassId.Class_C
    if score >= 0.6:
        return ClassId.Class_D
    if score >= 0.5:
        return ClassId.Class_E
    if score >= 0.4:
        return ClassId.Class_F
    if score >= 0.3:
        return ClassId.Class_G
    if score >= 0.2:
        return ClassId.Class_H
    if score >= 0.1:
        return ClassId.Class_I
    return ClassId.Class_J
