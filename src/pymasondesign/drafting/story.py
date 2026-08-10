from __future__ import annotations

from attrs import field, frozen
from pymasondesign.materials.masonry import MasonrySpecification


@frozen
class Story:
    """Representação de um pavimento/nível físico do edifício de alvenaria estrutural no lançamento.

    Attributes:
        story_id: Identificador único do pavimento (ex.: "PAV_01", "PAV_02", "TERREO").
        elevation: Cota vertical Z do piso acabado em relação à origem do projeto.
        story_height: Altura total piso a piso em metros ou cm (story_height > 0).
        masonry_spec: Especificação da alvenaria estrutural que rege o pavimento.
        plan_id: Identificador da planta baixa (FloorPlan) adotada neste nível (ex.: "PLAN_TIPO").
    """

    story_id: str = field(converter=str)
    elevation: float = field(converter=float)
    story_height: float = field(converter=float)
    masonry_spec: MasonrySpecification = field()
    plan_id: str = field(converter=str)

    def __attrs_post_init__(self) -> None:
        if self.story_height <= 0:
            raise ValueError(f"story_height deve ser positivo, obtido {self.story_height}.")

