from __future__ import annotations

from attrs import field, frozen
from pymasondesign.common import to_tuple
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.sections.base import Section
from pymasondesign.sections.properties import SectionProperties
from pymasondesign.design.segment import ResistantSegment


@frozen
class ResistantSection:
    """Representação de uma seção transversal resistente de alvenaria estrutural (almas e abas colaborantes).

    Todas as propriedades geométricas e a seção geométrica são expressas estritamente em COORDENADAS LOCAIS
    (com o eixo X local alinhado à direção de análise da alma principal). A transformação associada mapeia
    do sistema local para o sistema global da planta.

    Attributes:
        section_id: Identificador único da seção resistente (ex.: "RS_PG1_X_01").
        group_id: Identificador do PanelGroup de origem no modelo estrutural.
        direction: Vetor unitário no sistema global correspondente à direção de análise da alma.
        segments: Coleção imutável de segmentos (almas e abas) que compõem a seção resistente.
        height: Altura livre da seção resistente no pavimento (H > 0).
        properties: Propriedades seccionais (A, CG, Ixx, Iyy, Ixy, Wx, Wy, rx, ry) em coordenadas locais.
        geometric_section: Instância geométrica da seção (CompositeSection) em coordenadas locais.
        local_to_global: Transform2D que mapeia pontos e vetores do sistema local para o global da planta.
    """

    section_id: str = field(converter=str)
    group_id: str = field(converter=str)
    direction: Vector2D = field()
    segments: tuple[ResistantSegment, ...] = field(converter=to_tuple)
    height: float = field(converter=float)
    properties: SectionProperties = field()
    geometric_section: Section = field()
    local_to_global: Transform2D = field()

    def __attrs_post_init__(self) -> None:
        if self.height <= 0:
            raise ValueError(f"Altura da seção resistente '{self.section_id}' deve ser positiva, obtido: {self.height}.")
        if not self.segments:
            raise ValueError(f"Seção resistente '{self.section_id}' deve conter ao menos um segmento.")

        # Validação de unicidade de IDs de segmento
        seen_ids = set()
        for seg in self.segments:
            if seg.segment_id in seen_ids:
                raise ValueError(f"ID de segmento duplicado na seção '{self.section_id}': '{seg.segment_id}'.")
            seen_ids.add(seg.segment_id)

    @property
    def webs(self) -> tuple[ResistantSegment, ...]:
        """Coleção dos segmentos que atuam como alma principal (WEB)."""
        return tuple(s for s in self.segments if s.is_web)

    @property
    def flanges(self) -> tuple[ResistantSegment, ...]:
        """Coleção dos segmentos que atuam como abas colaborantes (FLANGE)."""
        return tuple(s for s in self.segments if s.is_flange)

    @property
    def web_panel_ids(self) -> tuple[str, ...]:
        """IDs únicos dos painéis de alvenaria de origem que atuam como alma."""
        seen: list[str] = []
        for s in self.webs:
            if s.source_panel_id not in seen:
                seen.append(s.source_panel_id)
        return tuple(seen)

    @property
    def flange_panel_ids(self) -> tuple[str, ...]:
        """IDs únicos dos painéis de alvenaria de origem que atuam como aba."""
        seen: list[str] = []
        for s in self.flanges:
            if s.source_panel_id not in seen:
                seen.append(s.source_panel_id)
        return tuple(seen)

    @property
    def num_webs(self) -> int:
        """Número de almas presentes na seção resistente."""
        return len(self.webs)

    @property
    def num_flanges(self) -> int:
        """Número de abas colaborantes presentes na seção resistente."""
        return len(self.flanges)

    @property
    def total_area(self) -> float:
        """Área líquida total da seção transversal resistente."""
        return self.properties.area

    @property
    def global_to_local(self) -> Transform2D:
        """Transformação geométrica que mapeia do sistema global da planta para o sistema local da seção."""
        return self.local_to_global.inverse()

    def find_segment(self, segment_id: str) -> ResistantSegment | None:
        """Busca um segmento componente pelo identificador."""
        for s in self.segments:
            if s.segment_id == segment_id:
                return s
        return None
