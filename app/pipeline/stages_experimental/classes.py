from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClassId(str, Enum):
    Class_A = "Class_A"
    Class_B = "Class_B"
    Class_C = "Class_C"
    Class_D = "Class_D"
    Class_E = "Class_E"
    Class_F = "Class_F"
    Class_G = "Class_G"
    Class_H = "Class_H"
    Class_I = "Class_I"
    Class_J = "Class_J"
    Class_K = "Class_K"
    Class_L = "Class_L"
    Class_M = "Class_M"
    Class_N = "Class_N"


@dataclass(frozen=True, slots=True)
class ClassDefinition:
    class_id: ClassId
    class_family: str
    classifier_version: str = "experimental_v1"


CLASS_DEFINITIONS: tuple[ClassDefinition, ...] = tuple(
    ClassDefinition(class_id=class_id, class_family=f"family_{index:02d}")
    for index, class_id in enumerate(ClassId, start=1)
)

CLASS_BY_ID: dict[ClassId, ClassDefinition] = {
    item.class_id: item for item in CLASS_DEFINITIONS
}
