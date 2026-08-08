"""Módulo de especificação de materiais e compósitos de alvenaria estrutural."""

from pymasondesign.materials.enums import (
    SteelCategory,
    BlockMaterialType,
    StrengthClass,
    BlockStrengthClass,
    CeramicWallType,
    BlockWallType,
)
from pymasondesign.materials.steel import SteelSpecification
from pymasondesign.materials.block import BlockSpecification
from pymasondesign.materials.mortar import MortarSpecification
from pymasondesign.materials.grout import GroutSpecification
from pymasondesign.materials.masonry import MasonrySpecification
from pymasondesign.materials.factory import NBR16868TableEntry, NBR16868MasonryFactory

__all__ = [
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
]
