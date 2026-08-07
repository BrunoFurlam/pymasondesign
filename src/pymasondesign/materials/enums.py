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
