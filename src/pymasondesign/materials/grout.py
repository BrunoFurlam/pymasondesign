from __future__ import annotations

from attrs import define, field


@define(frozen=True, slots=True)
class GroutSpecification:
    """Especificação de graute para preenchimento de alvenaria estrutural (NBR 16868).

    Attributes:
        fg: Resistência característica à compressão do graute aos 28 dias em MPa.
    """

    fg: float = field(converter=float)

    def __attrs_post_init__(self) -> None:
        if self.fg <= 0:
            raise ValueError(f"fg (resistência do graute aos 28 dias) deve ser positiva, obtido {self.fg}.")
