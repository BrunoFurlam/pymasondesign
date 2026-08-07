"""pymasondesign: Core para dimensionamento de alvenaria estrutural."""

from pymasondesign.geometry import (
    Point2D,
    Vector2D,
    BoundingBox,
    SectionProperties,
    Section,
    RectangularSection,
    CompositeSection,
    Transform2D,
)
from pymasondesign.mechanics import (
    NormalStressPlane,
    SectionForces,
    StressRegime,
    MechanicsService,
    DEFAULT_TOLERANCE,
)

__version__ = "0.1.0"

__all__ = [
    "Point2D",
    "Vector2D",
    "BoundingBox",
    "SectionProperties",
    "Section",
    "RectangularSection",
    "CompositeSection",
    "Transform2D",
    "NormalStressPlane",
    "SectionForces",
    "StressRegime",
    "MechanicsService",
    "DEFAULT_TOLERANCE",
    "__version__",
]
