from __future__ import annotations

import math
from attrs import define, field
from pymasondesign.geometry.point import Point2D


@define(frozen=True, slots=True)
class Vector2D:
    """Representa um vetor euclidiano 2D (x, y).

    Attributes:
        x: Componente horizontal do vetor.
        y: Componente vertical do vetor.
    """

    x: float = field(converter=float)
    y: float = field(converter=float)

    @classmethod
    def from_points(cls, start: Point2D, end: Point2D) -> Vector2D:
        """Cria um vetor a partir de dois pontos (start -> end)."""
        return cls(x=end.x - start.x, y=end.y - start.y)

    @classmethod
    def unit_x(cls) -> Vector2D:
        """Retorna o vetor unitário na direção X (1, 0)."""
        return cls(x=1.0, y=0.0)

    @classmethod
    def unit_y(cls) -> Vector2D:
        """Retorna o vetor unitário na direção Y (0, 1)."""
        return cls(x=0.0, y=1.0)

    @property
    def magnitude(self) -> float:
        """Comprimento / norma euclidiana do vetor: ||v|| = sqrt(x^2 + y^2)."""
        return math.hypot(self.x, self.y)

    @property
    def magnitude_squared(self) -> float:
        """Quadrado da norma euclidiana: ||v||^2 = x^2 + y^2."""
        return self.x**2 + self.y**2

    def normalized(self) -> Vector2D:
        """Retorna o vetor unitário (versor) na mesma direção."""
        mag = self.magnitude
        if mag == 0:
            raise ZeroDivisionError("Não é possível normalizar o vetor nulo.")
        return Vector2D(x=self.x / mag, y=self.y / mag)

    def dot(self, other: Vector2D) -> float:
        """Produto escalar (dot product): u . v = u_x * v_x + u_y * v_y."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vector2D) -> float:
        """Produto vetorial 2D (componente Z do produto vetorial / determinante): u_x * v_y - u_y * v_x."""
        return self.x * other.y - self.y * other.x

    def perpendicular(self) -> Vector2D:
        """Retorna um vetor perpendicular girado 90 graus no sentido anti-horário: (-y, x)."""
        return Vector2D(x=-self.y, y=self.x)

    def rotated(self, angle_rad: float) -> Vector2D:
        """Rotaciona o vetor por um ângulo em radianos no sentido anti-horário."""
        cos_t = math.cos(angle_rad)
        sin_t = math.sin(angle_rad)
        return Vector2D(
            x=self.x * cos_t - self.y * sin_t,
            y=self.x * sin_t + self.y * cos_t,
        )

    def reflected(self, normal: Vector2D) -> Vector2D:
        """Reflete o vetor através de um vetor normal (espelhamento): v_ref = v - 2 * (v . n_unit) * n_unit."""
        n = normal.normalized()
        d = 2.0 * self.dot(n)
        return Vector2D(x=self.x - d * n.x, y=self.y - d * n.y)

    def to_point(self) -> Point2D:
        """Converte o vetor em um Point2D com as mesmas coordenadas."""
        return Point2D(x=self.x, y=self.y)

    def __add__(self, other: Vector2D) -> Vector2D:
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(x=self.x + other.x, y=self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        if not isinstance(other, Vector2D):
            return NotImplemented
        return Vector2D(x=self.x - other.x, y=self.y - other.y)

    def __mul__(self, factor: float) -> Vector2D:
        return Vector2D(x=self.x * factor, y=self.y * factor)

    def __rmul__(self, factor: float) -> Vector2D:
        return self * factor

    def __truediv__(self, divisor: float) -> Vector2D:
        if divisor == 0:
            raise ZeroDivisionError("Divisão por zero em Vector2D.")
        return Vector2D(x=self.x / divisor, y=self.y / divisor)

    def __neg__(self) -> Vector2D:
        return Vector2D(x=-self.x, y=-self.y)
