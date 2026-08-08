"""pymasondesign: Core para dimensionamento de alvenaria estrutural."""

from pymasondesign.geometry import (
    Point2D,
    Vector2D,
    BoundingBox,
    Transform2D,
    Polygon,
)
from pymasondesign.sections import (
    Section,
    SectionProperties,
    RectangularSection,
    PolygonSection,
    CompositeSection,
    SectionComponent,
)
from pymasondesign.mechanics import (
    NormalStressPlane,
    SectionForces,
    StressRegime,
    MechanicsService,
    DEFAULT_TOLERANCE,
)
from pymasondesign.materials import (
    SteelCategory,
    BlockMaterialType,
    StrengthClass,
    BlockStrengthClass,
    CeramicWallType,
    BlockWallType,
    SteelSpecification,
    BlockSpecification,
    MortarSpecification,
    GroutSpecification,
    MasonrySpecification,
    NBR16868TableEntry,
    NBR16868MasonryFactory,
)

__version__ = "0.1.0"

__all__ = [
    # Geometria pura 2D
    "Point2D",
    "Vector2D",
    "BoundingBox",
    "Transform2D",
    "Polygon",
    # Seções transversais estruturais
    "Section",
    "SectionProperties",
    "RectangularSection",
    "PolygonSection",
    "CompositeSection",
    "SectionComponent",
    # Mecânica e tensões
    "NormalStressPlane",
    "SectionForces",
    "StressRegime",
    "MechanicsService",
    "DEFAULT_TOLERANCE",
    # Materiais estruturais
    "SteelCategory",
    "BlockMaterialType",
    "StrengthClass",
    "BlockStrengthClass",
    "CeramicWallType",
    "BlockWallType",
    "SteelSpecification",
    "BlockSpecification",
    "MortarSpecification",
    "GroutSpecification",
    "MasonrySpecification",
    "NBR16868TableEntry",
    "NBR16868MasonryFactory",
    "__version__",
]
