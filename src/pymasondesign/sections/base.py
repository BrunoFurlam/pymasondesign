from __future__ import annotations

from abc import ABC, abstractmethod
from pymasondesign.sections.properties import SectionProperties


class Section(ABC):
    """Classe base abstrata para todas as seções transversais estruturais 2D."""

    @abstractmethod
    def compute_properties(self) -> SectionProperties:
        """Calcula e retorna as propriedades geométricas e mecânicas da seção transversal."""
        raise NotImplementedError

    @property
    def properties(self) -> SectionProperties:
        """Propriedades geométricas e mecânicas da seção transversal."""
        return self.compute_properties()
