"""pymasondesign: Core para dimensionamento de alvenaria estrutural."""

from pymasondesign.geometry import (
    Point2D,
    BoundingBox,
    SectionProperties,
    Section,
    RectangularSection,
    CompositeSection,
)
from pymasondesign.mechanics import NormalStressPlane, SectionForces

__version__ = "0.1.0"

__all__ = [
    "Point2D",
    "BoundingBox",
    "SectionProperties",
    "Section",
    "RectangularSection",
    "CompositeSection",
    "NormalStressPlane",
    "SectionForces",
    "__version__",
]
