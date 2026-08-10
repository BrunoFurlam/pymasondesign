from __future__ import annotations

from attrs import field, frozen


@frozen
class MortarSpecification:
    """Especificação de argamassa de assentamento (NBR 16868).

    Attributes:
        fa: Resistência característica à compressão da argamassa aos 28 dias em MPa.
    """

    fa: float = field(converter=float)

    def __attrs_post_init__(self) -> None:
        if self.fa <= 0:
            raise ValueError(f"fa (resistência da argamassa) deve ser positiva, obtido {self.fa}.")
