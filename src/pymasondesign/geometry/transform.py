from __future__ import annotations

import math
from attrs import define, field
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.tolerances import GEOMETRIC_TOLERANCE


@define(frozen=True, slots=True)
class Transform2D:
    """Representa uma transformação geométrica 2D geral baseada em vetores diretores de eixos e origem.

    Permite representar translações, rotações e espelhamentos/reflexões com total generalidade:
        p_global = origin + x_local * u_axis + y_local * v_axis

    Attributes:
        origin: Ponto de origem do novo sistema de coordenadas.
        u_axis: Vetor diretor do eixo X local na base global (Vector2D).
        v_axis: Vetor diretor do eixo Y local na base global (Vector2D).
    """

    origin: Point2D = field(default=Point2D(0.0, 0.0))
    u_axis: Vector2D = field(default=Vector2D(1.0, 0.0))
    v_axis: Vector2D = field(default=Vector2D(0.0, 1.0))

    def __attrs_post_init__(self) -> None:
        if self.determinant == 0.0:
            raise ValueError("Os vetores diretores u_axis e v_axis não podem ser colineares (determinante nulo).")

    @property
    def determinant(self) -> float:
        """Determinante da matriz de base: u_x * v_y - u_y * v_x."""
        return self.u_axis.cross(self.v_axis)

    @property
    def is_reflection(self) -> bool:
        """Indica se a transformação contém reflexão/espelhamento (determinante < 0)."""
        return self.determinant < 0.0

    @property
    def is_orthogonal(self) -> bool:
        """Indica se os eixos locais são perpendiculares entre si: u . v == 0."""
        return math.isclose(self.u_axis.dot(self.v_axis), 0.0, abs_tol=GEOMETRIC_TOLERANCE)

    @classmethod
    def identity(cls) -> Transform2D:
        """Retorna a transformação identidade."""
        return cls(
            origin=Point2D(0.0, 0.0),
            u_axis=Vector2D(1.0, 0.0),
            v_axis=Vector2D(0.0, 1.0),
        )

    @classmethod
    def translation(cls, dx: float, dy: float) -> Transform2D:
        """Cria uma transformação puramente translacional."""
        return cls(
            origin=Point2D(dx, dy),
            u_axis=Vector2D(1.0, 0.0),
            v_axis=Vector2D(0.0, 1.0),
        )

    @classmethod
    def rotation(cls, angle_rad: float) -> Transform2D:
        """Cria uma transformação rotacional pura em torno da origem (0, 0)."""
        cos_t = math.cos(angle_rad)
        sin_t = math.sin(angle_rad)
        return cls(
            origin=Point2D(0.0, 0.0),
            u_axis=Vector2D(cos_t, sin_t),
            v_axis=Vector2D(-sin_t, cos_t),
        )

    @classmethod
    def from_origin_and_angle(cls, origin: Point2D, angle_rad: float) -> Transform2D:
        """Cria uma transformação com translação de origem e rotação de eixos."""
        cos_t = math.cos(angle_rad)
        sin_t = math.sin(angle_rad)
        return cls(
            origin=origin,
            u_axis=Vector2D(cos_t, sin_t),
            v_axis=Vector2D(-sin_t, cos_t),
        )

    @classmethod
    def mirror_x(cls, origin_y: float = 0.0) -> Transform2D:
        """Espelhamento em relação à reta horizontal y = origin_y (inverte o eixo Y: v = (0, -1))."""
        return cls(
            origin=Point2D(0.0, origin_y),
            u_axis=Vector2D(1.0, 0.0),
            v_axis=Vector2D(0.0, -1.0),
        )

    @classmethod
    def mirror_y(cls, origin_x: float = 0.0) -> Transform2D:
        """Espelhamento em relação à reta vertical x = origin_x (inverte o eixo X: u = (-1, 0))."""
        return cls(
            origin=Point2D(origin_x, 0.0),
            u_axis=Vector2D(-1.0, 0.0),
            v_axis=Vector2D(0.0, 1.0),
        )

    @classmethod
    def from_basis(
        cls,
        origin: Point2D,
        u_axis: Vector2D,
        v_axis: Vector2D,
    ) -> Transform2D:
        """Cria uma transformação a partir da origem e dos vetores de base arbitrários."""
        return cls(origin=origin, u_axis=u_axis, v_axis=v_axis)

    def apply_point(self, point: Point2D) -> Point2D:
        """Mapeia um ponto do sistema local para o global: p_global = origin + x_local*u + y_local*v."""
        x_global = self.origin.x + point.x * self.u_axis.x + point.y * self.v_axis.x
        y_global = self.origin.y + point.x * self.u_axis.y + point.y * self.v_axis.y
        return Point2D(x_global, y_global)

    def apply_vector(self, vector: Vector2D) -> Vector2D:
        """Mapeia um vetor do sistema local para o global: v_global = vector.x*u + vector.y*v."""
        x_global = vector.x * self.u_axis.x + vector.y * self.v_axis.x
        y_global = vector.x * self.u_axis.y + vector.y * self.v_axis.y
        return Vector2D(x_global, y_global)

    def apply_inverse_point(self, point: Point2D) -> Point2D:
        """Mapeia um ponto do sistema global para o local (resolvendo a matriz inversa de base)."""
        dx = point.x - self.origin.x
        dy = point.y - self.origin.y
        det = self.determinant
        # Matriz inversa: (1/det) * [[v_y, -v_x], [-u_y, u_x]]
        x_local = (dy * (-self.v_axis.x) + dx * self.v_axis.y) / det
        y_local = (dx * (-self.u_axis.y) + dy * self.u_axis.x) / det
        return Point2D(x_local, y_local)

    def inverse(self) -> Transform2D:
        """Retorna a transformação inversa."""
        det = self.determinant
        inv_u = Vector2D(self.v_axis.y / det, -self.u_axis.y / det)
        inv_v = Vector2D(-self.v_axis.x / det, self.u_axis.x / det)
        # Nova origem = apply_inverse_point(Point2D(0, 0))
        inv_origin = self.apply_inverse_point(Point2D(0.0, 0.0))
        return Transform2D(origin=inv_origin, u_axis=inv_u, v_axis=inv_v)
