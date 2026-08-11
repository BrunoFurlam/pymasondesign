from __future__ import annotations

from enum import Enum


class SegmentRole(str, Enum):
    """Papel funcional do segmento estrutural na parede de contraventamento."""

    WEB = "WEB"        # Alma principal (orientada na direção da ação resistente analisada)
    FLANGE = "FLANGE"  # Aba colaborante transversal (conectada por amarração direta)
