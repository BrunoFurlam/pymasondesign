from __future__ import annotations

from attrs import define, field
from pymasondesign.geometry.base import Section
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.bounds import BoundingBox
from pymasondesign.geometry.properties import SectionProperties


@define(frozen=True, slots=True)
class RectangularSection(Section):
    """Representa uma seção transversal retangular maciça.

    Args:
        width: Largura ao longo do eixo X (b).
        height: Altura ao longo do eixo Y (h).
        origin: Vértice inferior esquerdo (x0, y0), por padrão (0, 0).
    """

    width: float = field(converter=float)
    height: float = field(converter=float)
    origin: Point2D = field(default=Point2D(0.0, 0.0))

    def __attrs_post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError(f"Largura (width) deve ser positiva, recebido {self.width}.")
        if self.height <= 0:
            raise ValueError(f"Altura (height) deve ser positiva, recebido {self.height}.")

    def compute_properties(self) -> SectionProperties:
        b = self.width
        h = self.height
        area = b * h
        cg = Point2D(self.origin.x + b / 2.0, self.origin.y + h / 2.0)
        ixx = (b * (h**3)) / 12.0
        iyy = (h * (b**3)) / 12.0
        ixy = 0.0
        bounds = BoundingBox(
            xmin=self.origin.x,
            xmax=self.origin.x + b,
            ymin=self.origin.y,
            ymax=self.origin.y + h,
        )
        return SectionProperties(
            area=area,
            ixx=ixx,
            iyy=iyy,
            ixy=ixy,
            cg=cg,
            bounds=bounds,
        )
