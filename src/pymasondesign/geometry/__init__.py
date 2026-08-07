"""Módulo de primitivas geométricas e transformações 2D puras."""

from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.bounds import BoundingBox
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.geometry.polygon import Polygon

__all__ = [
    "Point2D",
    "Vector2D",
    "BoundingBox",
    "Transform2D",
    "Polygon",
]
