"""Módulo de primitivas geométricas e transformações 2D puras."""

from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.bounds import BoundingBox
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.geometry.polygon import Polygon
from pymasondesign.geometry.axis import Axis, AxisRelation, AxisIntersectionResult
from pymasondesign.geometry.tolerances import (
    GEOMETRIC_TOLERANCE,
    JUNCTION_TOLERANCE,
    OVERLAP_TOLERANCE,
    DIVISION_GUARD,
    is_zero,
    is_close,
    is_within_unit,
    is_at_start,
    is_at_end,
    is_at_vertex,
    is_interior,
)

__all__ = [
    "Point2D",
    "Vector2D",
    "BoundingBox",
    "Transform2D",
    "Polygon",
    "Axis",
    "AxisRelation",
    "AxisIntersectionResult",
    "GEOMETRIC_TOLERANCE",
    "JUNCTION_TOLERANCE",
    "OVERLAP_TOLERANCE",
    "DIVISION_GUARD",
    "is_zero",
    "is_close",
    "is_within_unit",
    "is_at_start",
    "is_at_end",
    "is_at_vertex",
    "is_interior",
]

