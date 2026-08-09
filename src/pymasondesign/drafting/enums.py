from __future__ import annotations

from enum import Enum


class OpeningType(Enum):
    """Tipos de abertura em alvenaria estrutural."""

    DOOR = "DOOR"
    WINDOW = "WINDOW"
    PASSAGE = "PASSAGE"
    DUCT = "DUCT"


class BondType(Enum):
    """Tipo de amarração/ligação no extremo de paredes.

    Attributes:
        DIRECT: Amarração direta / travada fiada a fiada (padrão quando há encontro).
        INDIRECT: Amarração indireta / junta a prumo com telas, grampos ou conectores metálicos.
        NONE: Sem amarração / extremidade livre (topo isolado ou sem interseção).
    """

    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"
    NONE = "NONE"


class WallEnd(Enum):
    """Identificador do extremo do eixo da parede."""

    START = "START"  # Ponto inicial do eixo (t = 0.0)
    END = "END"      # Ponto final do eixo (t = 1.0)
