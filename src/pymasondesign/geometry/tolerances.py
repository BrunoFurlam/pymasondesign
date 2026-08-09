"""Constantes de tolerância geométrica e funções auxiliares de comparação numérica com tolerância."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Constantes de tolerância padrão
# ---------------------------------------------------------------------------

GEOMETRIC_TOLERANCE: float = 1e-9
"""Tolerância padrão para comparações geométricas (paralelismo, interseção, ortogonalidade)."""

JUNCTION_TOLERANCE: float = 1e-4
"""Tolerância para detecção de encontros (junctions) entre paredes em plantas baixas."""

OVERLAP_TOLERANCE: float = 1e-9
"""Tolerância para validação de sobreposição de aberturas em paredes."""

DIVISION_GUARD: float = 1e-15
"""Guarda numérica para evitar divisão por zero em algoritmos de ray-casting."""


# ---------------------------------------------------------------------------
# Funções auxiliares de comparação com tolerância
# ---------------------------------------------------------------------------

def is_zero(value: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se um valor é efetivamente zero dentro da tolerância."""
    return abs(value) <= tolerance


def is_close(a: float, b: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se dois valores escalares são iguais dentro da tolerância (diferença absoluta)."""
    return abs(a - b) <= tolerance


def is_within_unit(t: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se um parâmetro t está no intervalo [0, 1] dentro da tolerância."""
    return -tolerance <= t <= 1.0 + tolerance


def is_at_start(t: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se o parâmetro t corresponde ao início (t ≈ 0)."""
    return abs(t) <= tolerance


def is_at_end(t: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se o parâmetro t corresponde ao fim (t ≈ 1)."""
    return abs(t - 1.0) <= tolerance


def is_at_vertex(t: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se o parâmetro t corresponde a um vértice (início ou fim)."""
    return is_at_start(t, tolerance) or is_at_end(t, tolerance)


def is_interior(t: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se o parâmetro t está estritamente no interior do segmento (0 < t < 1)."""
    return t > tolerance and t < 1.0 - tolerance
