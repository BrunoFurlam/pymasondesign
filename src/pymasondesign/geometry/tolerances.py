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


def is_not_zero(value: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se um valor é diferente de zero além da tolerância."""
    return abs(value) > tolerance


def is_close(a: float, b: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se dois valores escalares são iguais dentro da tolerância (diferença absoluta)."""
    return abs(a - b) <= tolerance


def is_not_close(a: float, b: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se dois valores escalares são diferentes além da tolerância."""
    return abs(a - b) > tolerance


def is_greater(a: float, b: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se 'a' é estritamente maior que 'b' além da tolerância (a > b + tol)."""
    return a - b > tolerance


def is_greater_or_equal(a: float, b: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se 'a' é maior ou aproximadamente igual a 'b' dentro da tolerância (a >= b - tol)."""
    return a - b >= -tolerance


def is_less(a: float, b: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se 'a' é estritamente menor que 'b' além da tolerância (a < b - tol)."""
    return b - a > tolerance


def is_less_or_equal(a: float, b: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se 'a' é menor ou aproximadamente igual a 'b' dentro da tolerância (a <= b + tol)."""
    return a - b <= tolerance


def is_positive(value: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se um valor é estritamente positivo além da tolerância (value > tol)."""
    return value > tolerance


def is_negative(value: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se um valor é estritamente negativo além da tolerância (value < -tol)."""
    return value < -tolerance


def is_non_negative(value: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se um valor é não-negativo dentro da tolerância (value >= -tol)."""
    return value >= -tolerance


def is_non_positive(value: float, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
    """Verifica se um valor é não-positivo dentro da tolerância (value <= tol)."""
    return value <= tolerance


def is_between(
    value: float,
    low: float,
    high: float,
    inclusive: bool = True,
    tolerance: float = GEOMETRIC_TOLERANCE,
) -> bool:
    """Verifica se um valor está contido no intervalo [low, high] com tolerância.
    
    Args:
        value: Valor escalar a testar.
        low: Limite inferior do intervalo.
        high: Limite superior do intervalo.
        inclusive: Se True, inclui as extremidades com tolerância. Se False, exige interior estrito.
        tolerance: Tolerância numérica absoluta.
    """
    if inclusive:
        return (value >= low - tolerance) and (value <= high + tolerance)
    return (value > low + tolerance) and (value < high - tolerance)


def is_strictly_between(
    value: float,
    low: float,
    high: float,
    tolerance: float = GEOMETRIC_TOLERANCE,
) -> bool:
    """Verifica se um valor está estritamente no interior do intervalo (low, high) além da tolerância."""
    return (value > low + tolerance) and (value < high - tolerance)


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
    return is_strictly_between(t, 0.0, 1.0, tolerance=tolerance)


__all__ = [
    "GEOMETRIC_TOLERANCE",
    "JUNCTION_TOLERANCE",
    "OVERLAP_TOLERANCE",
    "DIVISION_GUARD",
    "is_zero",
    "is_not_zero",
    "is_close",
    "is_not_close",
    "is_greater",
    "is_greater_or_equal",
    "is_less",
    "is_less_or_equal",
    "is_positive",
    "is_negative",
    "is_non_negative",
    "is_non_positive",
    "is_between",
    "is_strictly_between",
    "is_within_unit",
    "is_at_start",
    "is_at_end",
    "is_at_vertex",
    "is_interior",
]
