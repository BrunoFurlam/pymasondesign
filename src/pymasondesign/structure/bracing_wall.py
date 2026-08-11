from __future__ import annotations

from attrs import field, frozen
from pymasondesign.common import to_tuple
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.structure.bracing_segment import BracingSegment


@frozen
class BracingWall:
    """Representação de uma parede de contraventamento estrutural de alvenaria (almas e abas colaborantes).

    Representa o elemento estrutural vertical resistente a ações horizontais em uma dada direção
    e verticais associadas. O sistema de coordenadas local tem origem no centróide geométrico dos
    segmentos e o eixo X local alinhado à direção de análise da alma principal.

    Attributes:
        wall_id: Identificador único da parede de contraventamento (ex.: "BW_PG1_X_01").
        group_id: Identificador do PanelGroup de origem no modelo estrutural.
        direction: Vetor unitário no sistema global correspondente à direção de análise da alma.
        segments: Coleção imutável de segmentos (almas e abas) que compõem a parede de contraventamento.
        height: Altura livre da parede no pavimento (H > 0).
        local_to_global: Transform2D que mapeia pontos e vetores do sistema local para o global da planta.
    """

    wall_id: str = field(converter=str)
    group_id: str = field(converter=str)
    direction: Vector2D = field()
    segments: tuple[BracingSegment, ...] = field(converter=to_tuple)
    height: float = field(converter=float)
    local_to_global: Transform2D = field()

    def __attrs_post_init__(self) -> None:
        if self.height <= 0:
            raise ValueError(f"Altura da parede de contraventamento '{self.wall_id}' deve ser positiva, obtido: {self.height}.")
        if not self.segments:
            raise ValueError(f"Parede de contraventamento '{self.wall_id}' deve conter ao menos um segmento.")

        # Validação de unicidade de IDs de segmento
        seen_ids: set[str] = set()
        for seg in self.segments:
            if seg.segment_id in seen_ids:
                raise ValueError(f"ID de segmento duplicado na parede '{self.wall_id}': '{seg.segment_id}'.")
            seen_ids.add(seg.segment_id)

    @property
    def webs(self) -> tuple[BracingSegment, ...]:
        """Coleção dos segmentos que atuam como alma principal (WEB)."""
        return tuple(s for s in self.segments if s.is_web)

    @property
    def flanges(self) -> tuple[BracingSegment, ...]:
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
        """Número de almas presentes na parede de contraventamento."""
        return len(self.webs)

    @property
    def num_flanges(self) -> int:
        """Número de abas colaborantes presentes na parede de contraventamento."""
        return len(self.flanges)

    @property
    def total_length(self) -> float:
        """Soma do comprimento de todos os segmentos da parede de contraventamento."""
        return sum(s.length for s in self.segments)

    @property
    def total_area(self) -> float:
        """Área transversal total bruta dos segmentos da parede de contraventamento."""
        return sum(s.area for s in self.segments)

    @property
    def global_to_local(self) -> Transform2D:
        """Transformação geométrica que mapeia do sistema global da planta para o sistema local da parede."""
        return self.local_to_global.inverse()

    def find_segment(self, segment_id: str) -> BracingSegment | None:
        """Busca um segmento componente pelo identificador."""
        for s in self.segments:
            if s.segment_id == segment_id:
                return s
        return None
