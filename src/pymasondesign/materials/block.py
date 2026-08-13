from __future__ import annotations

from attrs import field, frozen
from pymasondesign.materials.enums import BlockMaterialType, StrengthClass, CeramicWallType
from pymasondesign.geometry.tolerances import is_positive


@frozen
class BlockSpecification:
    """Especificação de bloco estrutural (NBR 16868).

    Attributes:
        fbk: Resistência característica à compressão do bloco referida à área bruta em MPa.
        material: Tipo de material (concreto, cerâmico, sílico-calcário).
        strength_class: Classe de resistência do bloco de concreto ('A', 'B' ou 'C') ou None se cerâmico.
        wall_type: Tipo de parede para blocos cerâmicos (CeramicWallType.HOLLOW ou SOLID) ou None se concreto.
    """

    fbk: float = field(converter=float)
    material: BlockMaterialType = field(default=BlockMaterialType.CONCRETE)
    strength_class: StrengthClass | None = field(default=None)
    wall_type: CeramicWallType | None = field(default=None)

    def __attrs_post_init__(self) -> None:
        if not is_positive(self.fbk):
            raise ValueError(f"fbk (resistência do bloco na área bruta) deve ser positivo, obtido {self.fbk}.")

    @classmethod
    def concrete(
        cls,
        fbk: float,
        strength_class: StrengthClass = StrengthClass.A,
    ) -> BlockSpecification:
        """Cria uma especificação de bloco de concreto."""
        return cls(
            fbk=fbk,
            material=BlockMaterialType.CONCRETE,
            strength_class=strength_class,
            wall_type=None,
        )

    @classmethod
    def ceramic(
        cls,
        fbk: float,
        wall_type: CeramicWallType = CeramicWallType.HOLLOW,
    ) -> BlockSpecification:
        """Cria uma especificação de bloco cerâmico."""
        return cls(
            fbk=fbk,
            material=BlockMaterialType.CERAMIC,
            strength_class=None,
            wall_type=wall_type,
        )
