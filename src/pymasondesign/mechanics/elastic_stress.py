from __future__ import annotations

import math
from attrs import define, field
from pymasondesign.geometry.point import Point2D


@define(frozen=True, slots=True)
class ElasticStressState:
    """Representa a distribuição linear de tensões normais elásticas em uma seção transversal.

    O campo de tensões é definido pela equação de plano:
        σ(x, y) = c0 + cx * x + cy * y

    onde (x, y) são coordenadas medidas a partir do centro de gravidade (0.0, 0.0).

    Attributes:
        c0: Parcela uniforme de tensão devida ao esforço normal (N / A).
        cx: Gradiente de variação da tensão em relação ao eixo X centroidal.
        cy: Gradiente de variação da tensão em relação ao eixo Y centroidal.
    """

    c0: float = field(default=0.0, converter=float)
    cx: float = field(default=0.0, converter=float)
    cy: float = field(default=0.0, converter=float)

    @classmethod
    def from_forces(
        cls,
        normal_force: float = 0.0,
        moment_x: float = 0.0,
        moment_y: float = 0.0,
        area: float = 0.0,
        ixx: float = 0.0,
        iyy: float = 0.0,
        ixy: float = 0.0,
    ) -> ElasticStressState:
        """Constrói o estado de tensões elásticas a partir dos esforços e valores geométricos.

        Args:
            normal_force: Esforço normal solicitante (N), positivo para tração e negativo para compressão.
            moment_x: Momento fletor em torno do eixo baricêntrico X (Mx).
            moment_y: Momento fletor em torno do eixo baricêntrico Y (My).
            area: Área da seção transversal (A).
            ixx: Momento de inércia em relação ao eixo baricêntrico X (Ixx).
            iyy: Momento de inércia em relação ao eixo baricêntrico Y (Iyy).
            ixy: Produto de inércia baricêntrico (Ixy), padrão 0.0.

        Returns:
            Instância de ElasticStressState.
        """
        if area <= 0:
            raise ValueError(f"Área deve ser estritamente positiva, recebido: {area}.")

        c0 = normal_force / area

        det = ixx * iyy - ixy**2
        if det == 0:
            if moment_x != 0.0 or moment_y != 0.0:
                raise ZeroDivisionError("Determinante dos momentos de inércia é nulo para momentos não-nulos.")
            cx = 0.0
            cy = 0.0
        else:
            cx = (moment_y * ixx - moment_x * ixy) / det
            cy = (moment_x * iyy - moment_y * ixy) / det

        return cls(c0=c0, cx=cx, cy=cy)

    def stress_at(self, x: float, y: float) -> float:
        """Calcula a tensão normal σ no ponto (x, y) medido em relação ao centro de gravidade (0.0, 0.0)."""
        return self.c0 + self.cx * x + self.cy * y

    def stress_at_point(self, point: Point2D) -> float:
        """Calcula a tensão normal σ no Point2D cujas coordenadas são relativas ao CG."""
        return self.stress_at(point.x, point.y)

    @property
    def neutral_axis_distance(self) -> float:
        """Distância perpendicular do centro de gravidade (0, 0) até a Linha Neutra (σ = 0)."""
        grad_norm = math.hypot(self.cx, self.cy)
        if grad_norm == 0:
            return float("inf") if self.c0 != 0 else 0.0
        return abs(self.c0) / grad_norm

    @property
    def neutral_axis_angle(self) -> float:
        """Ângulo de inclinação da Linha Neutra em relação ao eixo X (em radianos)."""
        if self.cx == 0.0 and self.cy == 0.0:
            return 0.0
        return math.atan2(-self.cx, self.cy)
