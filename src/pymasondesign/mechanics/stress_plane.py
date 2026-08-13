from __future__ import annotations

import math
from typing import Iterable
from attrs import field, frozen
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.geometry.tolerances import is_zero, is_not_zero


@frozen
class NormalStressPlane:
    """Representa o plano linear de tensões normais em uma seção transversal.

    O campo de tensões é definido pela equação de plano:
        σ(x, y) = c0 + cx * x + cy * y

    onde (x, y) são coordenadas relativas ao centro de gravidade (0.0, 0.0).

    Attributes:
        c0: Parcela uniforme de tensão devida ao esforço normal (N / A).
        cx: Gradiente de variação da tensão em relação ao eixo X centroidal.
        cy: Gradiente de variação da tensão em relação ao eixo Y centroidal.
    """

    c0: float = field(default=0.0, converter=float)
    cx: float = field(default=0.0, converter=float)
    cy: float = field(default=0.0, converter=float)

    def stress_at(self, x: float, y: float) -> float:
        """Calcula a tensão normal σ no ponto (x, y) relativo ao centro de gravidade (0.0, 0.0)."""
        return self.c0 + self.cx * x + self.cy * y

    def stress_at_point(self, point: Point2D) -> float:
        """Calcula a tensão normal σ no Point2D relativo ao centro de gravidade."""
        return self.stress_at(point.x, point.y)

    @property
    def neutral_axis_distance(self) -> float:
        """Distância perpendicular do centro de gravidade (0, 0) até a Linha Neutra (σ = 0)."""
        grad_norm = math.hypot(self.cx, self.cy)
        if is_zero(grad_norm):
            return float("inf") if is_not_zero(self.c0) else 0.0
        return abs(self.c0) / grad_norm

    @property
    def neutral_axis_angle(self) -> float:
        """Ângulo de inclinação da Linha Neutra em relação ao eixo X (em radianos)."""
        if is_zero(self.cx) and is_zero(self.cy):
            return 0.0
        return math.atan2(-self.cx, self.cy)

    def scale(self, factor: float) -> NormalStressPlane:
        """Multiplica todos os coeficientes do plano de tensões por um escalar."""
        return NormalStressPlane(
            c0=self.c0 * factor,
            cx=self.cx * factor,
            cy=self.cy * factor,
        )

    def transform(self, transform: Transform2D) -> NormalStressPlane:
        """Expressa o plano de tensões em um novo sistema de coordenadas 2D (incluindo rotação e espelhamento).

        Args:
            transform: Transformação 2D contendo origem e vetores de base (u_axis, v_axis).

        Returns:
            Novo NormalStressPlane ajustado para as coordenadas do novo sistema.
        """
        # Tensão na nova origem (onde x_local=0, y_local=0)
        c0_new = self.stress_at(transform.origin.x, transform.origin.y)

        # Projeção do gradiente de tensão nos novos eixos u e v
        cx_new = self.cx * transform.u_axis.x + self.cy * transform.u_axis.y
        cy_new = self.cx * transform.v_axis.x + self.cy * transform.v_axis.y

        return NormalStressPlane(c0=c0_new, cx=cx_new, cy=cy_new)

    def __add__(self, other: NormalStressPlane) -> NormalStressPlane:
        """Aplica o princípio da superposição somando dois planos de tensões."""
        if not isinstance(other, NormalStressPlane):
            return NotImplemented
        return NormalStressPlane(
            c0=self.c0 + other.c0,
            cx=self.cx + other.cx,
            cy=self.cy + other.cy,
        )

    def __mul__(self, factor: float) -> NormalStressPlane:
        return self.scale(factor)

    def __rmul__(self, factor: float) -> NormalStressPlane:
        return self.scale(factor)

    @classmethod
    def combine(cls, items: Iterable[NormalStressPlane]) -> NormalStressPlane:
        """Combina e totaliza múltiplos planos de tensões aplicando o princípio da superposição."""
        total_c0 = 0.0
        total_cx = 0.0
        total_cy = 0.0
        for p in items:
            total_c0 += p.c0
            total_cx += p.cx
            total_cy += p.cy
        return cls(c0=total_c0, cx=total_cx, cy=total_cy)
