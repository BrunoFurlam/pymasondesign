from __future__ import annotations

from attrs import field, frozen
from pymasondesign.geometry.tolerances import is_positive


@frozen
class FlangeOptions:
    """Opções para determinação da largura colaborante das abas (flanges) na seção resistente.

    Attributes:
        max_multiplier: Multiplicador máximo sobre a espessura da alma considerada (k * t_web)
                        para a projeção externa de cada lado da aba (padrão: 6.0 conforme NBR 16868-1).
        custom_width: Largura efetiva customizada fixa por lado da aba para sobrescrita explícita de projeto.
    """

    max_multiplier: float = field(default=6.0, converter=float)
    custom_width: float | None = field(default=None)

    def __attrs_post_init__(self) -> None:
        if not is_positive(self.max_multiplier):
            raise ValueError(f"max_multiplier deve ser positivo, obtido: {self.max_multiplier}.")
        if self.custom_width is not None and not is_positive(self.custom_width):
            raise ValueError(f"custom_width deve ser positivo quando informado, obtido: {self.custom_width}.")
