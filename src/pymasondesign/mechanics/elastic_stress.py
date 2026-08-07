from __future__ import annotations

import math
from attrs import define, field
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.properties import SectionProperties


@define(frozen=True, slots=True)
class ElasticStressState:
    """Representa a distribuição de tensões normais elásticas em uma seção transversal.

    Calcula o campo linear de tensões normais a partir do esforço normal (N)
    e momentos fletores (Mx, My) em coordenadas (x, y) relativas ao
    centro de gravidade da seção (onde 0, 0 é o CG).

    Attributes:
        properties: Propriedades geométricas da seção (SectionProperties).
        normal_force: Esforço normal solicitante (N), positivo para tração e negativo para compressão.
        moment_x: Momento fletor em torno do eixo baricêntrico X (Mx).
        moment_y: Momento fletor em torno do eixo baricêntrico Y (My).
    """

    properties: SectionProperties
    normal_force: float = field(default=0.0, converter=float)
    moment_x: float = field(default=0.0, converter=float)
    moment_y: float = field(default=0.0, converter=float)

    @property
    def c0(self) -> float:
        """Tensão média uniforme devida ao esforço normal (N / A)."""
        if self.properties.area <= 0:
            raise ValueError("Área da seção deve ser positiva para cálculo de tensões.")
        return self.normal_force / self.properties.area

    @property
    def cx(self) -> float:
        """Gradiente de variação da tensão em relação ao eixo X centroidal."""
        ixx = self.properties.ixx
        iyy = self.properties.iyy
        ixy = self.properties.ixy
        det = ixx * iyy - ixy**2
        if det == 0:
            raise ZeroDivisionError("Determinante dos momentos de inércia é nulo.")
        return (self.moment_y * ixx - self.moment_x * ixy) / det

    @property
    def cy(self) -> float:
        """Gradiente de variação da tensão em relação ao eixo Y centroidal."""
        ixx = self.properties.ixx
        iyy = self.properties.iyy
        ixy = self.properties.ixy
        det = ixx * iyy - ixy**2
        if det == 0:
            raise ZeroDivisionError("Determinante dos momentos de inércia é nulo.")
        return (self.moment_x * iyy - self.moment_y * ixy) / det

    def stress_at(self, x: float, y: float) -> float:
        """Calcula a tensão normal σ no ponto (x, y) relativo ao centro de gravidade (0.0, 0.0).

        Args:
            x: Coordenada horizontal relativa ao CG (x - x_cg).
            y: Coordenada vertical relativa ao CG (y - y_cg).

        Returns:
            Tensão normal σ resultante.
        """
        return self.c0 + self.cx * x + self.cy * y

    def stress_at_point(self, point: Point2D) -> float:
        """Calcula a tensão normal σ em um Point2D cujas coordenadas são relativas ao CG."""
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
