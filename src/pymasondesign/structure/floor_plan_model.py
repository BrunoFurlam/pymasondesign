from __future__ import annotations

from attrs import define, field
from pymasondesign.common import to_tuple
from pymasondesign.structure.group import PanelGroup
from pymasondesign.structure.panel import MasonryPanel


@define(frozen=True, slots=True)
class FloorPlanModel:
    """Modelo estrutural derivado de uma planta baixa (FloorPlan), contendo seus grupos de painéis discretizados.

    Representa a geometria dos painéis e suas conexões por amarração para uma dada tipologia de pavimento,
    podendo ser reutilizado por múltiplos pavimentos (Story) do edifício.

    Attributes:
        plan_id: Identificador da planta/modelo de referência (ex.: "PLAN_TIPO", "TERREO").
        height: Pé-direito útil da alvenaria adotado na discretização dos painéis.
        groups: Coleção imutável de PanelGroup que compõem o modelo da planta.
    """

    plan_id: str = field(converter=str)
    height: float = field(converter=float)
    groups: tuple[PanelGroup, ...] = field(default=(), converter=to_tuple)

    def __attrs_post_init__(self) -> None:
        if self.height <= 0:
            raise ValueError(f"A altura (height) do modelo deve ser positiva, obtido {self.height}.")

        if not self.groups:
            raise ValueError(f"Modelo da planta '{self.plan_id}' não pode ser vazio.")

        seen_group_ids: set[str] = set()
        for g in self.groups:
            if g.group_id in seen_group_ids:
                raise ValueError(f"ID de grupo duplicado no modelo da planta '{self.plan_id}': '{g.group_id}'.")
            seen_group_ids.add(g.group_id)

    @property
    def panels(self) -> tuple[MasonryPanel, ...]:
        """Coleção completa de todos os painéis resistentes de todos os grupos da planta."""
        all_p: list[MasonryPanel] = []
        for g in self.groups:
            all_p.extend(g.panels)
        return tuple(all_p)

    @property
    def total_length(self) -> float:
        """Soma do comprimento de todos os painéis resistentes da planta baixa."""
        return sum(g.total_length for g in self.groups)

    @property
    def wall_ids(self) -> tuple[str, ...]:
        """IDs únicos de todas as paredes representadas no modelo, preservando a ordem de aparição."""
        seen: list[str] = []
        for g in self.groups:
            for wid in g.wall_ids:
                if wid not in seen:
                    seen.append(wid)
        return tuple(seen)

    def find_group(self, group_id: str) -> PanelGroup | None:
        """Busca um grupo de painéis pelo seu identificador."""
        for g in self.groups:
            if g.group_id == group_id:
                return g
        return None

    def find_panel(self, panel_id: str) -> MasonryPanel | None:
        """Busca um painel individual dentro de todos os grupos do modelo pelo seu identificador."""
        for g in self.groups:
            p = g.find_panel(panel_id)
            if p is not None:
                return p
        return None

    def find_groups_by_wall(self, wall_id: str) -> tuple[PanelGroup, ...]:
        """Retorna todos os grupos que contêm painéis pertencentes à parede especificada."""
        return tuple(g for g in self.groups if wall_id in g.wall_ids)
