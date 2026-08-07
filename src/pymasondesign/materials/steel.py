from __future__ import annotations

from attrs import define, field
from pymasondesign.materials.enums import SteelCategory


@define(frozen=True, slots=True)
class SteelSpecification:
    """Especificação mecânica de aço para armaduras passivas (NBR 6118 / NBR 7480 / NBR 16868).

    Attributes:
        category: Categoria do aço (CA50 ou CA60).
        fyk: Resistência característica de escoamento em MPa (padrão: 500 para CA50, 600 para CA60).
        es: Módulo de elasticidade longitudinal em MPa (constante normativa de 210.000 MPa).
    """

    category: SteelCategory = field(default=SteelCategory.CA50)
    fyk: float = field(default=500.0, converter=float)
    es: float = field(default=210000.0, converter=float)

    def __attrs_post_init__(self) -> None:
        if self.fyk <= 0:
            raise ValueError(f"fyk deve ser positivo, obtido {self.fyk}.")
        if self.es <= 0:
            raise ValueError(f"Módulo de elasticidade (Es) deve ser positivo, obtido {self.es}.")

    @classmethod
    def ca50(cls, fyk: float = 500.0) -> SteelSpecification:
        """Cria uma especificação padrão de aço CA-50."""
        return cls(category=SteelCategory.CA50, fyk=fyk, es=210000.0)

    @classmethod
    def ca60(cls, fyk: float = 600.0) -> SteelSpecification:
        """Cria uma especificação padrão de aço CA-60."""
        return cls(category=SteelCategory.CA60, fyk=fyk, es=210000.0)

    def calculate_fyd(self, gamma_s: float, fyk_fraction: float = 1.0) -> float:
        """Calcula a resistência de cálculo do aço considerando o coeficiente de minoração e a fração útil de fyk.

        Args:
            gamma_s: Coeficiente de minoração da resistência do aço da verificação (ex: 1.15).
            fyk_fraction: Fração ou porcentagem de fyk permitida para o tipo de bloco e análise (ex: 0.50, 0.70 ou 1.0).

        Returns:
            Resistência de cálculo fyd = (fyk * fyk_fraction) / gamma_s.
        """
        if gamma_s <= 0:
            raise ValueError(f"gamma_s deve ser estritamente positivo, obtido {gamma_s}.")
        if fyk_fraction <= 0.0 or fyk_fraction > 1.0:
            raise ValueError(f"fyk_fraction deve estar no intervalo (0.0, 1.0], obtido {fyk_fraction}.")

        return (self.fyk * fyk_fraction) / gamma_s

    def calculate_eyd(self, gamma_s: float, fyk_fraction: float = 1.0) -> float:
        """Calcula a deformação de escoamento de cálculo correspondente: eyd = fyd / Es."""
        fyd = self.calculate_fyd(gamma_s=gamma_s, fyk_fraction=fyk_fraction)
        return fyd / self.es
