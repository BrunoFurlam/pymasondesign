from __future__ import annotations

from typing import TypeVar, Iterable

T = TypeVar("T")


def to_tuple(val: Iterable[T] | None) -> tuple[T, ...]:
    """Converte um iterável (lista, tupla, gerador) ou None em uma tupla imutável.

    Se val for None, retorna uma tupla vazia ().

    Args:
        val: Coleção iterável de elementos ou None.

    Returns:
        Tupla imutável com os elementos ou tupla vazia.
    """
    if val is None:
        return ()
    return tuple(val)
