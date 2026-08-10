from __future__ import annotations

from attrs import field, frozen
from pymasondesign.materials.enums import BlockMaterialType, CeramicWallType
from pymasondesign.materials.block import BlockSpecification
from pymasondesign.materials.mortar import MortarSpecification
from pymasondesign.materials.grout import GroutSpecification


@frozen
class MasonrySpecification:
    """Especificação mecânica do compósito de alvenaria estrutural (NBR 16868).

    Attributes:
        block: Especificação do bloco estrutural.
        mortar: Especificação da argamassa de assentamento.
        grout: Especificação do graute de preenchimento.
        fpk: Resistência característica à compressão do prisma simples (área bruta) em MPa.
        fpgk: Resistência característica à compressão do prisma grauteado (área bruta) em MPa.
        transverse_joints_filled: Se True, juntas transversais preenchidas (fator 1.0); se False, fator de redução de 0.8.
        elastic_modulus: Módulo de elasticidade longitudinal (Em) em MPa; se None, calculado conforme NBR 16868.
    """

    block: BlockSpecification = field()
    mortar: MortarSpecification = field()
    grout: GroutSpecification = field()
    fpk: float = field(converter=float)
    fpgk: float = field(converter=float)
    transverse_joints_filled: bool = field(default=True)
    elastic_modulus: float | None = field(default=None)

    def __attrs_post_init__(self) -> None:
        if self.fpk <= 0:
            raise ValueError(f"fpk deve ser positivo, obtido {self.fpk}.")
        if self.fpgk <= 0:
            raise ValueError(f"fpgk deve ser positivo, obtido {self.fpgk}.")
        if self.elastic_modulus is not None and self.elastic_modulus <= 0:
            raise ValueError(f"elastic_modulus deve ser positivo se fornecido, obtido {self.elastic_modulus}.")

    @classmethod
    def from_nbr16868(
        cls,
        fbk: float,
        material: BlockMaterialType = BlockMaterialType.CONCRETE,
        wall_type: CeramicWallType = CeramicWallType.HOLLOW,
        transverse_joints_filled: bool = True,
        elastic_modulus: float | None = None,
    ) -> MasonrySpecification:
        """Cria uma especificação de alvenaria a partir da tabela oficial da NBR 16868 (concreto ou cerâmico)."""
        from pymasondesign.materials.factory import NBR16868MasonryFactory

        return NBR16868MasonryFactory.create(
            fbk=fbk,
            material=material,
            wall_type=wall_type,
            transverse_joints_filled=transverse_joints_filled,
            elastic_modulus=elastic_modulus,
        )

    @property
    def joint_factor(self) -> float:
        """Fator de correção de junta (1.0 com junta transversal preenchida, 0.8 sem preenchimento transversal)."""
        return 1.0 if self.transverse_joints_filled else 0.8

    @property
    def fk_hollow(self) -> float:
        """Resistência característica da parede/alvenaria oca: fk = 0.70 * eta_j * fpk."""
        return 0.70 * self.joint_factor * self.fpk

    @property
    def fk_grouted(self) -> float:
        """Resistência característica da parede/alvenaria totalmente grauteada: fkg = 0.70 * eta_j * fpgk."""
        return 0.70 * self.joint_factor * self.fpgk

    @property
    def em(self) -> float:
        """Módulo de elasticidade longitudinal da alvenaria (Em) em MPa.

        Se não informado explicitamente, calcula conforme escalonamento da NBR 16868 por fbk:
            - 800 * fpk para fbk <= 20 MPa
            - 750 * fpk para 20 < fbk < 26 MPa (inclui 22 e 24 MPa)
            - 700 * fpk para fbk >= 26 MPa
        """
        if self.elastic_modulus is not None:
            return self.elastic_modulus

        fbk = self.block.fbk
        if fbk <= 20.0:
            alpha = 800.0
        elif fbk < 26.0:
            alpha = 750.0
        else:
            alpha = 700.0

        return alpha * self.fpk

    def calculate_fk(self, grout_ratio: float = 0.0) -> float:
        """Calcula a resistência característica da alvenaria (fk) interpolada linearmente pela taxa de grauteamento.

        Args:
            grout_ratio: Porcentagem ou fração de grauteamento da seção (entre 0.0 para oco e 1.0 para totalmente grauteado).

        Returns:
            fk interpolado linearmente: (1 - rho_g) * fk_hollow + rho_g * fk_grouted.
        """
        if not (0.0 <= grout_ratio <= 1.0):
            raise ValueError(f"Taxa de grauteamento deve estar entre 0.0 e 1.0, obtido {grout_ratio}.")

        return (1.0 - grout_ratio) * self.fk_hollow + grout_ratio * self.fk_grouted

    def calculate_fd(self, gamma_m: float, grout_ratio: float = 0.0) -> float:
        """Calcula a resistência de cálculo da alvenaria (fd = fk(rho_g) / gamma_m).

        Args:
            gamma_m: Coeficiente de ponderação da alvenaria da verificação em análise.
            grout_ratio: Taxa de grauteamento entre 0.0 e 1.0.

        Returns:
            Resistência de cálculo à compressão da alvenaria (fd).
        """
        if gamma_m <= 0:
            raise ValueError(f"gamma_m deve ser estritamente positivo, obtido {gamma_m}.")

        fk = self.calculate_fk(grout_ratio=grout_ratio)
        return fk / gamma_m
