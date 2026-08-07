from __future__ import annotations

from attrs import define, field
from pymasondesign.materials.enums import BlockMaterialType


@define(frozen=True, slots=True)
class BlockSpecification:
    """Especificação de bloco estrutural (NBR 16868).

    Attributes:
        fbk: Resistência característica à compressão do bloco referida à área bruta em MPa.
        material: Tipo de material (concreto, cerâmico, sílico-calcário).
    """

    fbk: float = field(converter=float)
    material: BlockMaterialType = field(default=BlockMaterialType.CONCRETE)

    def __attrs_post_init__(self) -> None:
        if self.fbk <= 0:
            raise ValueError(f"fbk (resistência do bloco na área bruta) deve ser positivo, obtido {self.fbk}.")

    @classmethod
    def concrete(cls, fbk: float) -> BlockSpecification:
        """Cria uma especificação de bloco de concreto."""
        return cls(fbk=fbk, material=BlockMaterialType.CONCRETE)

    @classmethod
    def ceramic(cls, fbk: float) -> BlockSpecification:
        """Cria uma especificação de bloco cerâmico."""
        return cls(fbk=fbk, material=BlockMaterialType.CERAMIC)
