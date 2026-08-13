from __future__ import annotations

from attrs import field, frozen
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.bounds import BoundingBox
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.geometry.tolerances import (
    DIVISION_GUARD,
    is_zero,
    is_positive,
)


@frozen
class Polygon:
    """Representa uma forma geométrica poligonal 2D pura e imutável delimitada por vértices.

    Attributes:
        vertices: Tupla imutável e ordenada de vértices 2D (Point2D).
    """

    vertices: tuple[Point2D, ...] = field(converter=tuple)

    def __attrs_post_init__(self) -> None:
        if len(self.vertices) < 3:
            raise ValueError(f"Um polígono deve ter no mínimo 3 vértices, recebido {len(self.vertices)}.")

    @classmethod
    def from_coords(cls, coords: list[tuple[float, float]] | tuple[tuple[float, float], ...]) -> Polygon:
        """Cria um polígono a partir de uma sequência de pares de coordenadas (x, y)."""
        return cls(vertices=tuple(Point2D(x, y) for x, y in coords))

    @property
    def num_vertices(self) -> int:
        """Número de vértices do polígono."""
        return len(self.vertices)

    @property
    def perimeter(self) -> float:
        """Perímetro total do contorno do polígono."""
        pts = self.vertices
        n = len(pts)
        return sum(pts[i].distance_to(pts[(i + 1) % n]) for i in range(n))

    @property
    def bounds(self) -> BoundingBox:
        """Caixa delimitadora (BoundingBox) do polígono."""
        xs = [p.x for p in self.vertices]
        ys = [p.y for p in self.vertices]
        return BoundingBox(xmin=min(xs), xmax=max(xs), ymin=min(ys), ymax=max(ys))

    @property
    def signed_area(self) -> float:
        """Área com sinal (Shoelace). Positiva para anti-horário, negativa para horário."""
        pts = self.vertices
        n = len(pts)
        area_sum = 0.0
        for i in range(n):
            j = (i + 1) % n
            area_sum += pts[i].x * pts[j].y - pts[j].x * pts[i].y
        return area_sum / 2.0

    @property
    def area(self) -> float:
        """Área geométrica positiva do polígono."""
        a = abs(self.signed_area)
        if is_zero(a):
            raise ValueError("A área do polígono é nula (vértices colineares ou coincidentes).")
        return a

    @property
    def centroid(self) -> Point2D:
        """Centro de gravidade / baricentro geométrico do polígono (Point2D)."""
        pts = self.vertices
        n = len(pts)
        qx_sum = 0.0
        qy_sum = 0.0
        area_sum = 0.0

        for i in range(n):
            j = (i + 1) % n
            xi, yi = pts[i].x, pts[i].y
            xj, yj = pts[j].x, pts[j].y
            cross = xi * yj - xj * yi
            area_sum += cross
            qx_sum += (yi + yj) * cross
            qy_sum += (xi + xj) * cross

        signed_area = area_sum / 2.0
        if is_zero(signed_area):
            raise ValueError("A área do polígono é nula (vértices colineares ou coincidentes).")

        area = abs(signed_area)
        sign = 1.0 if is_positive(signed_area) else -1.0
        return Point2D(sign * qy_sum / (6.0 * area), sign * qx_sum / (6.0 * area))

    def contains_point(self, point: Point2D) -> bool:
        """Verifica se um ponto está dentro do polígono via algoritmo de Ray-Casting."""
        pts = self.vertices
        n = len(pts)
        inside = False
        x, y = point.x, point.y

        for i in range(n):
            j = (i + 1) % n
            xi, yi = pts[i].x, pts[i].y
            xj, yj = pts[j].x, pts[j].y

            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + DIVISION_GUARD) + xi)
            if intersect:
                inside = not inside

        return inside

    def transformed(self, transform: Transform2D) -> Polygon:
        """Aplica uma transformação 2D (translação, rotação ou espelhamento) a todos os vértices."""
        return Polygon(vertices=tuple(transform.apply_point(p) for p in self.vertices))

    def translated(self, dx: float, dy: float) -> Polygon:
        """Translação do polígono por (dx, dy)."""
        return Polygon(vertices=tuple(p.translated(dx, dy) for p in self.vertices))
