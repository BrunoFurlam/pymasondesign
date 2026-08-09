from __future__ import annotations

from attrs import define, field
from pymasondesign.materials.masonry import MasonrySpecification
from pymasondesign.drafting.floor_plan import FloorPlan


@define(frozen=True, slots=True)
class Story:
    """Representação de um pavimento/nível físico do edifício de alvenaria estrutural.

    Attributes:
        story_id: Identificador único do pavimento (ex.: "PAV_01", "PAV_02", "TERREO").
        elevation: Cota vertical Z do piso acabado em relação à origem do projeto.
        story_height: Altura total piso a piso em metros ou cm (story_height > 0).
        masonry_spec: Especificação da alvenaria estrutural que rege o pavimento.
        floor_plan: Planta baixa (FloorPlan / StoryLayout) referenciada por este pavimento.
    """

    story_id: str = field(converter=str)
    elevation: float = field(converter=float)
    story_height: float = field(converter=float)
    masonry_spec: MasonrySpecification = field()
    floor_plan: FloorPlan = field()

    def __attrs_post_init__(self) -> None:
        if self.story_height <= 0:
            raise ValueError(f"story_height deve ser positivo, obtido {self.story_height}.")

    @property
    def clear_height(self) -> float:
        """Pé-direito livre útil da alvenaria, derivado da altura da planta associada."""
        return self.floor_plan.height
