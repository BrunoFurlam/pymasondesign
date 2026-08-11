from __future__ import annotations

from attrs import field, frozen
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.polygon import Polygon
from pymasondesign.geometry.tolerances import JUNCTION_TOLERANCE
from pymasondesign.structure.enums import SegmentRole


def create_rectangle_polygon(axis: Axis, thickness: float) -> Polygon:
    """Gera um polígono retangular 2D fechado centrado no eixo fornecido."""
    half_t = thickness / 2.0
    n = axis.normal

    v0 = Point2D(axis.start.x - half_t * n.x, axis.start.y - half_t * n.y)
    v1 = Point2D(axis.end.x - half_t * n.x, axis.end.y - half_t * n.y)
    v2 = Point2D(axis.end.x + half_t * n.x, axis.end.y + half_t * n.y)
    v3 = Point2D(axis.start.x + half_t * n.x, axis.start.y + half_t * n.y)

    return Polygon(vertices=(v0, v1, v2, v3))


@frozen
class BracingSegment:
    """Representa um segmento estrutural de uma parede de contraventamento (alma ou aba colaborante).

    Attributes:
        segment_id: Identificador único do segmento dentro da parede (ex.: "BW_PG1_X_01_WEB_P1").
        source_panel_id: Identificador do MasonryPanel de origem no modelo estrutural.
        role: Papel estrutural do segmento (SegmentRole.WEB ou SegmentRole.FLANGE).
        local_axis: Eixo geométrico 2D expresso no sistema de coordenadas local da parede.
        global_axis: Eixo geométrico 2D expresso no sistema de coordenadas global da planta.
        thickness: Espessura da parede do segmento (t > 0).
        height: Altura livre do segmento no pavimento (H > 0).
    """

    segment_id: str = field(converter=str)
    source_panel_id: str = field(converter=str)
    role: SegmentRole = field()
    local_axis: Axis = field()
    global_axis: Axis = field()
    thickness: float = field(converter=float)
    height: float = field(converter=float)

    def __attrs_post_init__(self) -> None:
        if self.thickness <= 0:
            raise ValueError(f"Espessura do segmento deve ser positiva, obtido: {self.thickness}.")
        if self.height <= 0:
            raise ValueError(f"Altura do segmento deve ser positiva, obtido: {self.height}.")

    @property
    def is_web(self) -> bool:
        """Indica se este segmento atua como alma principal."""
        return self.role == SegmentRole.WEB

    @property
    def is_flange(self) -> bool:
        """Indica se este segmento atua como aba colaborante."""
        return self.role == SegmentRole.FLANGE

    @property
    def length(self) -> float:
        """Comprimento linear do segmento (L = axis.length)."""
        return self.local_axis.length

    @property
    def area(self) -> float:
        """Área da seção transversal deste segmento."""
        return self.length * self.thickness

    def local_polygon(self) -> Polygon:
        """Gera o polígono retangular 2D fechado no sistema de coordenadas local."""
        return create_rectangle_polygon(self.local_axis, self.thickness)

    def global_polygon(self) -> Polygon:
        """Gera o polígono retangular 2D fechado no sistema de coordenadas global."""
        return create_rectangle_polygon(self.global_axis, self.thickness)

    def touches(self, other: BracingSegment, tolerance: float = JUNCTION_TOLERANCE) -> bool:
        """Verifica se este segmento toca outro segmento em alguma extremidade (em coordenadas globais)."""
        return self.global_axis.touches_endpoints(other.global_axis, tolerance=tolerance)
