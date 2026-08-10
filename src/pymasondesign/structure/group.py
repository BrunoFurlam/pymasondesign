from __future__ import annotations

from attrs import field, frozen
from pymasondesign.common import to_tuple
from pymasondesign.structure.panel import MasonryPanel


@frozen
class PanelGroup:
    """Grupo estrutural de painéis de alvenaria conectados monoliticamente por amarração direta.

    Attributes:
        group_id: Identificador único do grupo de painéis (ex.: "PG1", "PG2").
        panels: Coleção imutável de painéis que formam este grupo conexo.
    """

    group_id: str = field(converter=str)
    panels: tuple[MasonryPanel, ...] = field(default=(), converter=to_tuple)

    def __attrs_post_init__(self) -> None:
        if not self.panels:
            raise ValueError(f"Grupo de painéis '{self.group_id}' não pode ser vazio.")

        # Validação de unicidade de IDs de painel dentro do grupo
        seen_ids = set()
        for p in self.panels:
            if p.panel_id in seen_ids:
                raise ValueError(f"ID de painel duplicado no grupo '{self.group_id}': '{p.panel_id}'.")
            seen_ids.add(p.panel_id)

    @property
    def total_length(self) -> float:
        """Soma dos comprimentos de todos os painéis do grupo."""
        return sum(p.length for p in self.panels)

    @property
    def wall_ids(self) -> tuple[str, ...]:
        """IDs únicos das paredes representadas no grupo, preservando a ordem de aparição."""
        seen: list[str] = []
        for p in self.panels:
            if p.wall_id not in seen:
                seen.append(p.wall_id)
        return tuple(seen)

    def find_panel(self, panel_id: str) -> MasonryPanel | None:
        """Busca um painel dentro do grupo pelo seu identificador."""
        for p in self.panels:
            if p.panel_id == panel_id:
                return p
        return None
