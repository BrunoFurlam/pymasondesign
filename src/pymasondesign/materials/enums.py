from __future__ import annotations

from enum import Enum


class SteelCategory(Enum):
    """Categorias normativas de aço para armaduras (NBR 6118 / NBR 7480)."""

    CA50 = "CA50"
    CA60 = "CA60"


class BlockMaterialType(Enum):
    """Tipos de material para blocos de alvenaria estrutural (NBR 16868)."""

    CONCRETE = "CONCRETE"
    CERAMIC = "CERAMIC"
    CALCIUM_SILICATE = "CALCIUM_SILICATE"


class StrengthClass(Enum):
    """Classes de resistência de blocos de concreto conforme a NBR 16868 ('A', 'B' ou 'C')."""

    A = "A"
    B = "B"
    C = "C"


class CeramicWallType(Enum):
    """Tipo de parede do bloco cerâmico conforme a NBR 16868 (Vazada ou Maciça)."""

    HOLLOW = "HOLLOW"  # Vazada
    SOLID = "SOLID"    # Maciça


# Aliases de conveniência
BlockStrengthClass = StrengthClass
BlockWallType = CeramicWallType
