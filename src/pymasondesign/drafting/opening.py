from __future__ import annotations

from attrs import field, frozen
from pymasondesign.drafting.enums import OpeningType


@frozen
class Opening:
    """Especificação de abertura / vão em parede de alvenaria.

    Attributes:
        opening_id: Identificador único do vão (ex.: "JAN-01", "P-01").
        offset_along_wall: Distância a partir do ponto inicial do eixo da parede até o início do vão.
        width: Largura livre horizontal da abertura em metros ou cm.
        height: Altura livre vertical da abertura em metros ou cm.
        opening_type: Tipo de abertura (DOOR, WINDOW, PASSAGE, DUCT).
        sill_height: Altura do peitoril em relação à base da parede (padrão 0.0 para portas).
    """

    opening_id: str = field(converter=str)
    offset_along_wall: float = field(converter=float)
    width: float = field(converter=float)
    height: float = field(converter=float)
    opening_type: OpeningType = field(default=OpeningType.DOOR)
    sill_height: float = field(default=0.0, converter=float)

    def __attrs_post_init__(self) -> None:
        if self.offset_along_wall < 0:
            raise ValueError(f"offset_along_wall deve ser não-negativo, obtido {self.offset_along_wall}.")
        if self.width <= 0:
            raise ValueError(f"Largura da abertura (width) deve ser positiva, obtido {self.width}.")
        if self.height <= 0:
            raise ValueError(f"Altura da abertura (height) deve ser positiva, obtido {self.height}.")
        if self.sill_height < 0:
            raise ValueError(f"sill_height deve ser não-negativo, obtido {self.sill_height}.")

    @classmethod
    def door(
        cls,
        opening_id: str,
        offset_along_wall: float,
        width: float,
        height: float,
    ) -> Opening:
        """Cria uma abertura do tipo porta (sill_height = 0.0)."""
        return cls(
            opening_id=opening_id,
            offset_along_wall=offset_along_wall,
            width=width,
            height=height,
            opening_type=OpeningType.DOOR,
            sill_height=0.0,
        )

    @classmethod
    def window(
        cls,
        opening_id: str,
        offset_along_wall: float,
        width: float,
        height: float,
        sill_height: float,
    ) -> Opening:
        """Cria uma abertura do tipo janela com peitoril."""
        return cls(
            opening_id=opening_id,
            offset_along_wall=offset_along_wall,
            width=width,
            height=height,
            opening_type=OpeningType.WINDOW,
            sill_height=sill_height,
        )
