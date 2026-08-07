"""Módulo de seções transversais estruturais e propriedades de seção."""

from pymasondesign.sections.base import Section
from pymasondesign.sections.properties import SectionProperties
from pymasondesign.sections.rectangle import RectangularSection
from pymasondesign.sections.polygon import PolygonSection
from pymasondesign.sections.composite import CompositeSection, SectionComponent

__all__ = [
    "Section",
    "SectionProperties",
    "RectangularSection",
    "PolygonSection",
    "CompositeSection",
    "SectionComponent",
]
