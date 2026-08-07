from __future__ import annotations

from abc import ABC, abstractmethod
from pymasondesign.geometry.properties import SectionProperties


class Section(ABC):
    """Classe base abstrata para todas as seções transversais 2D."""

    @abstractmethod
    def compute_properties(self) -> SectionProperties:
        """Calcula e retorna as propriedades geométricas da seção."""
        raise NotImplementedError

    @property
    def properties(self) -> SectionProperties:
        """Propriedades geométricas da seção transversal."""
        return self.compute_properties()
