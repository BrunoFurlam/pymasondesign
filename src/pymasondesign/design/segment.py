from __future__ import annotations

from attrs import field, frozen
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.polygon import Polygon
from pymasondesign.geometry.tolerances import JUNCTION_TOLERANCE
from pymasondesign.design.enums import SegmentRole


@frozen
class ResistantSegment:
    """Representa um segmento estrutural componente da seção resistente (alma ou aba colaborante).

    Attributes:
        segment_id: Identificador único do segmento dentro da seção (ex.: "RS_PG1_X_01_WEB_P1", "RS_PG1_X_01_FLANGE_P2_POS").
        source_panel_id: Identificador do MasonryPanel de origem no modelo estrutural.
        role: Papel do segmento na seção (SegmentRole.WEB ou SegmentRole.FLANGE).
        local_axis: Eixo geométrico 2D do segmento expresso no sistema de coordenadas local da seção.
        global_axis: Eixo geométrico 2D do segmento expresso no sistema de coordenadas global da planta.
        thickness: Espessura da parede do segmento (t > 0).
        effective_length: Comprimento linear efetivo do segmento (L_web para alma, b_f para aba).
        local_polygon: Polígono 2D fechado do segmento no sistema de coordenadas local.
        global_polygon: Polígono 2D fechado do segmento no sistema de coordenadas global.
    """

    segment_id: str = field(converter=str)
    source_panel_id: str = field(converter=str)
    role: SegmentRole = field()
    local_axis: Axis = field()
    global_axis: Axis = field()
    thickness: float = field(converter=float)
    effective_length: float = field(converter=float)
    local_polygon: Polygon = field()
    global_polygon: Polygon = field()

    def __attrs_post_init__(self) -> None:
        if self.thickness <= 0:
            raise ValueError(f"Espessura do segmento deve ser positiva, obtido: {self.thickness}.")
        if self.effective_length <= 0:
            raise ValueError(f"Comprimento efetivo do segmento deve ser positivo, obtido: {self.effective_length}.")

    @property
    def is_web(self) -> bool:
        """Indica se este segmento atua como alma principal."""
        return self.role == SegmentRole.WEB

    @property
    def is_flange(self) -> bool:
        """Indica se este segmento atua como aba colaborante."""
        return self.role == SegmentRole.FLANGE

    @property
    def area(self) -> float:
        """Área da seção transversal deste segmento."""
        return self.effective_length * self.thickness

    def touches(self, other: ResistantSegment, tolerance: float = JUNCTION_TOLERANCE) -> bool:
        """Verifica se este segmento resistente toca outro segmento em alguma extremidade (em coordenadas globais)."""
        return self.global_axis.touches_endpoints(other.global_axis, tolerance=tolerance)
