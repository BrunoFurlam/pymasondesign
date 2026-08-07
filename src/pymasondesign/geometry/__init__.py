"""Módulo de geometria e cálculo de propriedades de seções transversais."""

from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.bounds import BoundingBox
from pymasondesign.geometry.properties import SectionProperties
from pymasondesign.geometry.base import Section
from pymasondesign.geometry.rectangle import RectangularSection
from pymasondesign.geometry.composite import CompositeSection, SectionComponent

__all__ = [
    "Point2D",
    "BoundingBox",
    "SectionProperties",
    "Section",
    "RectangularSection",
    "CompositeSection",
    "SectionComponent",
]
