from __future__ import annotations

from attrs import field, frozen
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.tolerances import JUNCTION_TOLERANCE, is_positive


@frozen
class MasonryPanel:
    """Representação de um painel resistente de alvenaria estrutural (pier / sub-parede).

    Attributes:
        panel_id: Identificador único do painel (ex.: "P1_P1", "P1_P2").
        wall_id: Identificador da parede de origem no drafting.
        axis: Eixo geométrico orientado 2D do painel.
        thickness: Espessura nominal da seção do painel em metros ou cm (t > 0).
        height: Altura livre do painel em metros ou cm (H > 0).
    """

    panel_id: str = field(converter=str)
    wall_id: str = field(converter=str)
    axis: Axis = field()
    thickness: float = field(converter=float)
    height: float = field(converter=float)

    def __attrs_post_init__(self) -> None:
        if not is_positive(self.thickness):
            raise ValueError(
                f"Espessura do painel (thickness) deve ser positiva, obtido: {self.thickness}."
            )
        if not is_positive(self.height):
            raise ValueError(
                f"Altura do painel (height) deve ser positiva, obtido: {self.height}."
            )

    @property
    def length(self) -> float:
        """Comprimento linear do painel."""
        return self.axis.length

    def touches(
        self, other: MasonryPanel, tolerance: float = JUNCTION_TOLERANCE
    ) -> bool:
        """Verifica se este painel toca o outro painel em alguma extremidade."""
        return self.axis.touches_endpoints(other.axis, tolerance=tolerance)
