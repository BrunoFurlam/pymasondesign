from __future__ import annotations

from attrs import field, frozen
from pymasondesign.materials.masonry import MasonrySpecification
from pymasondesign.geometry.tolerances import is_positive


@frozen
class StoryModel:
    """Modelo estrutural de um pavimento na edificação, associando cota vertical, material e referência ao modelo de planta.

    Attributes:
        story_id: Identificador único do nível (ex.: "COBERTURA", "PAV_03", "PAV_02", "TERREO").
        elevation: Cota vertical Z do piso acabado em relação à base do edifício.
        story_height: Altura total piso a piso (story_height > 0).
        masonry_spec: Especificação da alvenaria estrutural que rege o pavimento.
        plan_id: Identificador do modelo de planta (FloorPlanModel) adotado neste nível (ex.: "PLAN_TIPO").
    """

    story_id: str = field(converter=str)
    elevation: float = field(converter=float)
    story_height: float = field(converter=float)
    masonry_spec: MasonrySpecification = field()
    plan_id: str = field(converter=str)

    def __attrs_post_init__(self) -> None:
        if not is_positive(self.story_height):
            raise ValueError(f"story_height deve ser positivo, obtido {self.story_height}.")
