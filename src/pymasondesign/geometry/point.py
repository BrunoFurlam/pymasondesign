from __future__ import annotations

import math
from typing import TYPE_CHECKING
from attrs import field, frozen
from pymasondesign.geometry.tolerances import (
    GEOMETRIC_TOLERANCE,
    is_close,
)

if TYPE_CHECKING:
    from pymasondesign.geometry.vector import Vector2D


@frozen
class Point2D:
    """Representa um ponto 2D no plano cartesiano (x, y)."""

    x: float = field(converter=float)
    y: float = field(converter=float)

    @classmethod
    def from_coords(cls, coords: tuple[float, float]) -> Point2D:
        """Cria um ponto a partir de uma tupla de coordenadas (x, y)."""
        x, y = coords
        return cls(x=x, y=y)

    def distance_to(self, other: Point2D) -> float:
        """Calcula a distância euclidiana até outro ponto."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def is_same(self, other: Point2D, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
        """Verifica se dois pontos são geometricamente equivalentes/mesmo ponto dentro da tolerância."""
        return is_close(self.distance_to(other), 0.0, tolerance=tolerance)

    def translated(self, dx: float, dy: float) -> Point2D:
        """Retorna um novo ponto transladado por (dx, dy)."""
        return Point2D(self.x + dx, self.y + dy)

    def vector_to(self, other: Point2D) -> Vector2D:
        """Retorna o vetor orientado a partir deste ponto até o outro ponto (self -> other)."""
        from pymasondesign.geometry.vector import Vector2D

        return Vector2D.from_points(self, other)

    def moved_by(self, vector: Vector2D) -> Point2D:
        """Retorna um novo ponto deslocado pelo vetor 2D informado."""
        return Point2D(self.x + vector.x, self.y + vector.y)

    def __add__(self, other: Vector2D) -> Point2D:
        from pymasondesign.geometry.vector import Vector2D

        if not isinstance(other, Vector2D):
            return NotImplemented
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D | Point2D) -> Point2D | Vector2D:
        from pymasondesign.geometry.vector import Vector2D

        if isinstance(other, Vector2D):
            return Point2D(self.x - other.x, self.y - other.y)
        if isinstance(other, Point2D):
            return other.vector_to(self)
        return NotImplemented


