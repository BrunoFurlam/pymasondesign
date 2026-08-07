from __future__ import annotations

from enum import Enum


class StressRegime(str, Enum):
    """Classificação do regime de esforços solicitantes e tensões na seção."""

    NO_LOAD = "NO_LOAD"
    PURE_COMPRESSION = "PURE_COMPRESSION"
    PURE_TENSION = "PURE_TENSION"
    PURE_BENDING_X = "PURE_BENDING_X"
    PURE_BENDING_Y = "PURE_BENDING_Y"
    PURE_BENDING_XY = "PURE_BENDING_XY"
    FLEXO_COMPRESSION_X = "FLEXO_COMPRESSION_X"
    FLEXO_COMPRESSION_Y = "FLEXO_COMPRESSION_Y"
    FLEXO_COMPRESSION_XY = "FLEXO_COMPRESSION_XY"
    FLEXO_TENSION_X = "FLEXO_TENSION_X"
    FLEXO_TENSION_Y = "FLEXO_TENSION_Y"
    FLEXO_TENSION_XY = "FLEXO_TENSION_XY"
