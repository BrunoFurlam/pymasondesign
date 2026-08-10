from __future__ import annotations

from attrs import field, frozen
from pymasondesign.geometry.point import Point2D


@frozen
class BoundingBox:
    """Representa uma caixa delimitadora 2D alinhada aos eixos (x_min, x_max, y_min, y_max)."""

    xmin: float = field(converter=float)
    xmax: float = field(converter=float)
    ymin: float = field(converter=float)
    ymax: float = field(converter=float)

    def __attrs_post_init__(self) -> None:
        if self.xmin > self.xmax:
            raise ValueError(f"xmin ({self.xmin}) não pode ser maior que xmax ({self.xmax}).")
        if self.ymin > self.ymax:
            raise ValueError(f"ymin ({self.ymin}) não pode ser maior que ymax ({self.ymax}).")

    @property
    def width(self) -> float:
        """Largura ao longo do eixo X (xmax - xmin)."""
        return self.xmax - self.xmin

    @property
    def height(self) -> float:
        """Altura ao longo do eixo Y (ymax - ymin)."""
        return self.ymax - self.ymin

    @property
    def center(self) -> Point2D:
        """Centro geométrico do retângulo delimitador."""
        return Point2D((self.xmin + self.xmax) / 2.0, (self.ymin + self.ymax) / 2.0)

    def contains_point(self, point: Point2D) -> bool:
        """Verifica se um ponto está contido nos limites da caixa."""
        return self.xmin <= point.x <= self.xmax and self.ymin <= point.y <= self.ymax

    @classmethod
    def from_points(cls, points: list[Point2D]) -> BoundingBox:
        """Cria uma BoundingBox a partir de uma lista de pontos."""
        if not points:
            raise ValueError("A lista de pontos não pode estar vazia.")
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        return cls(xmin=min(xs), xmax=max(xs), ymin=min(ys), ymax=max(ys))
