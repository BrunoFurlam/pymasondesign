from __future__ import annotations

import math
from attrs import field, frozen
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.bounds import BoundingBox
from pymasondesign.geometry.tolerances import is_positive


@frozen
class SectionProperties:
    """Propriedades geométricas e de resistência de uma seção transversal 2D.

    Attributes:
        area: Área da seção transversal (A).
        ixx: Momento de inércia em relação ao eixo centroidal X (Ixx).
        iyy: Momento de inércia em relação ao eixo centroidal Y (Iyy).
        ixy: Produto de inércia em relação aos eixos centroidais (Ixy).
        cg: Centro de gravidade / baricentro da seção (Point2D).
        bounds: Limites máximos e mínimos da seção (BoundingBox).
    """

    area: float = field(converter=float)
    ixx: float = field(converter=float)
    iyy: float = field(converter=float)
    ixy: float = field(default=0.0, converter=float)
    cg: Point2D = field(default=Point2D(0.0, 0.0))
    bounds: BoundingBox = field(default=BoundingBox(0.0, 0.0, 0.0, 0.0))

    @property
    def x_min(self) -> float:
        """Coordenada X mínima da seção."""
        return self.bounds.xmin

    @property
    def x_max(self) -> float:
        """Coordenada X máxima da seção."""
        return self.bounds.xmax

    @property
    def y_min(self) -> float:
        """Coordenada Y mínima da seção."""
        return self.bounds.ymin

    @property
    def y_max(self) -> float:
        """Coordenada Y máxima da seção."""
        return self.bounds.ymax

    @property
    def rx(self) -> float:
        """Raio de giração em torno do eixo X centroidal: rx = sqrt(Ixx / A)."""
        return math.sqrt(self.ixx / self.area) if is_positive(self.area) else 0.0

    @property
    def ry(self) -> float:
        """Raio de giração em torno do eixo Y centroidal: ry = sqrt(Iyy / A)."""
        return math.sqrt(self.iyy / self.area) if is_positive(self.area) else 0.0

    @property
    def y_top(self) -> float:
        """Distância do centro de gravidade até a fibra superior: y_max - y_cg."""
        return self.bounds.ymax - self.cg.y

    @property
    def y_bot(self) -> float:
        """Distância do centro de gravidade até a fibra inferior: y_cg - y_min."""
        return self.cg.y - self.bounds.ymin

    @property
    def x_right(self) -> float:
        """Distância do centro de gravidade até a fibra mais à direita: x_max - x_cg."""
        return self.bounds.xmax - self.cg.x

    @property
    def x_left(self) -> float:
        """Distância do centro de gravidade até a fibra mais à esquerda: x_cg - x_min."""
        return self.cg.x - self.bounds.xmin

    @property
    def wx_top(self) -> float:
        """Módulo de resistência elástico para a fibra superior: Ixx / y_top."""
        d = self.y_top
        return self.ixx / d if is_positive(d) else 0.0

    @property
    def wx_bot(self) -> float:
        """Módulo de resistência elástico para a fibra inferior: Ixx / y_bot."""
        d = self.y_bot
        return self.ixx / d if is_positive(d) else 0.0

    @property
    def wy_right(self) -> float:
        """Módulo de resistência elástico para a fibra direita: Iyy / x_right."""
        d = self.x_right
        return self.iyy / d if is_positive(d) else 0.0

    @property
    def wy_left(self) -> float:
        """Módulo de resistência elástico para a fibra esquerda: Iyy / x_left."""
        d = self.x_left
        return self.iyy / d if is_positive(d) else 0.0

    @property
    def wx_min(self) -> float:
        """Módulo de resistência elástico mínimo em torno do eixo X."""
        return min(self.wx_top, self.wx_bot)

    @property
    def wy_min(self) -> float:
        """Módulo de resistência elástico mínimo em torno do eixo Y."""
        return min(self.wy_right, self.wy_left)

    @property
    def principal_moments(self) -> tuple[float, float, float]:
        """Calcula os momentos principais de inércia (I1, I2) e o ângulo principal θp (em radianos)."""
        avg = (self.ixx + self.iyy) / 2.0
        diff = (self.ixx - self.iyy) / 2.0
        r = math.hypot(diff, self.ixy)
        i1 = avg + r
        i2 = avg - r
        theta_p = 0.5 * math.atan2(-2 * self.ixy, self.ixx - self.iyy)
        return i1, i2, theta_p
