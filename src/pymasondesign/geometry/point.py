from __future__ import annotations

import math
from attrs import field, frozen
from pymasondesign.geometry.tolerances import GEOMETRIC_TOLERANCE


@frozen
class Point2D:
    """Representa um ponto 2D no plano cartesiano (x, y)."""

    x: float = field(converter=float)
    y: float = field(converter=float)

    def distance_to(self, other: Point2D) -> float:
        """Calcula a distância euclidiana até outro ponto."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def is_same(self, other: Point2D, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
        """Verifica se dois pontos são geometricamente equivalentes/mesmo ponto dentro da tolerância."""
        return self.distance_to(other) <= tolerance

    def translated(self, dx: float, dy: float) -> Point2D:
        """Retorna um novo ponto transladado por (dx, dy)."""
        return Point2D(self.x + dx, self.y + dy)
