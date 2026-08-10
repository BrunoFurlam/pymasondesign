from __future__ import annotations

from attrs import field, frozen
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.polygon import Polygon
from pymasondesign.sections.base import Section
from pymasondesign.sections.properties import SectionProperties


@frozen
class PolygonSection(Section):
    """Representa uma seção transversal estrutural poligonal.

    Attributes:
        polygon: Objeto geométrico Polygon que define o contorno da seção.
    """

    polygon: Polygon = field()

    @classmethod
    def from_vertices(cls, vertices: list[Point2D] | tuple[Point2D, ...]) -> PolygonSection:
        """Cria uma PolygonSection diretamente a partir de uma lista ou tupla de vértices."""
        return cls(polygon=Polygon(vertices=tuple(vertices)))

    @classmethod
    def from_coords(cls, coords: list[tuple[float, float]] | tuple[tuple[float, float], ...]) -> PolygonSection:
        """Cria uma PolygonSection a partir de pares de coordenadas (x, y)."""
        return cls(polygon=Polygon.from_coords(coords))

    def compute_properties(self) -> SectionProperties:
        """Calcula as propriedades geométricas e mecânicas da seção poligonal via integrais de Green / Shoelace."""
        pts = self.polygon.vertices
        n = len(pts)

        area_sum = 0.0
        qx_sum = 0.0
        qy_sum = 0.0
        ixx0_sum = 0.0
        iyy0_sum = 0.0
        ixy0_sum = 0.0

        for i in range(n):
            j = (i + 1) % n
            xi, yi = pts[i].x, pts[i].y
            xj, yj = pts[j].x, pts[j].y

            cross = xi * yj - xj * yi
            area_sum += cross
            qx_sum += (yi + yj) * cross
            qy_sum += (xi + xj) * cross
            ixx0_sum += (yi**2 + yi * yj + yj**2) * cross
            iyy0_sum += (xi**2 + xi * xj + xj**2) * cross
            ixy0_sum += (xi * yj + 2.0 * xi * yi + 2.0 * xj * yj + xj * yi) * cross

        signed_area = area_sum / 2.0
        if abs(signed_area) == 0.0:
            raise ValueError("A área da seção poligonal é nula (vértices colineares ou coincidentes).")

        area = abs(signed_area)
        sign = 1.0 if signed_area > 0 else -1.0

        cg_x = sign * qy_sum / (6.0 * area)
        cg_y = sign * qx_sum / (6.0 * area)

        # Momentos de inércia na origem global (0, 0)
        ixx_0 = sign * ixx0_sum / 12.0
        iyy_0 = sign * iyy0_sum / 12.0
        ixy_0 = sign * ixy0_sum / 24.0

        # Teorema dos Eixos Paralelos (Steiner) para eixos baricêntricos
        ixx = ixx_0 - area * (cg_y**2)
        iyy = iyy_0 - area * (cg_x**2)
        ixy = ixy_0 - area * cg_x * cg_y

        return SectionProperties(
            area=area,
            ixx=max(ixx, 0.0),
            iyy=max(iyy, 0.0),
            ixy=ixy,
            cg=Point2D(cg_x, cg_y),
            bounds=self.polygon.bounds,
        )
