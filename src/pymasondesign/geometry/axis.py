from __future__ import annotations

import math
from enum import Enum
from attrs import field, frozen
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.bounds import BoundingBox
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.geometry.tolerances import (
    GEOMETRIC_TOLERANCE,
    JUNCTION_TOLERANCE,
    is_zero,
    is_not_zero,
    is_close,
    is_within_unit,
    is_at_vertex,
    is_greater,
    is_greater_or_equal,
    is_non_positive,
    is_less_or_equal,
)


class AxisRelation(Enum):
    """Relação geométrica entre dois eixos lineares 2D."""

    DISJOINT = "DISJOINT"                # Sem interseção ou contato
    POINT_INTERSECT = "POINT_INTERSECT"  # Interseção em um único ponto interior
    TOUCHING_VERTEX = "TOUCHING_VERTEX"  # Contato em um vértice de extremidade (L / T)
    OVERLAPPING = "OVERLAPPING"          # Colineares com sobreposição de segmento


@frozen
class AxisIntersectionResult:
    """Resultado da análise geométrica de interseção entre dois eixos 2D.

    Attributes:
        relation: Relação geométrica (DISJOINT, POINT_INTERSECT, TOUCHING_VERTEX, OVERLAPPING).
        point: Ponto de interseção quando POINT_INTERSECT ou TOUCHING_VERTEX.
        overlap_segment: Segmento resultante da sobreposição quando OVERLAPPING.
        t: Parâmetro normalizado [0, 1] no primeiro eixo.
        u: Parâmetro normalizado [0, 1] no segundo eixo.
    """

    relation: AxisRelation = field()
    point: Point2D | None = field(default=None)
    overlap_segment: Axis | None = field(default=None)
    t: float | None = field(default=None)
    u: float | None = field(default=None)


@frozen
class Axis:
    """Value Object representando um eixo linear orientado 2D.

    Attributes:
        start: Ponto inicial do eixo no plano XY.
        end: Ponto final do eixo no plano XY.
    """

    start: Point2D = field()
    end: Point2D = field()

    def __attrs_post_init__(self) -> None:
        if self.start.is_same(self.end, GEOMETRIC_TOLERANCE):
            raise ValueError(f"Eixo não pode ter comprimento nulo: start={self.start} e end={self.end}.")

    @property
    def dx(self) -> float:
        """Delta X do eixo."""
        return self.end.x - self.start.x

    @property
    def dy(self) -> float:
        """Delta Y do eixo."""
        return self.end.y - self.start.y

    @property
    def length(self) -> float:
        """Comprimento Euclidiano do eixo."""
        return math.hypot(self.dx, self.dy)

    @property
    def as_vector(self) -> Vector2D:
        """Vetor Euclidiano 2D orientado de start para end com componentes (dx, dy)."""
        return Vector2D(self.dx, self.dy)

    @property
    def direction(self) -> Vector2D:
        """Vetor diretor unitário orientado de start para end."""
        return self.as_vector.normalized()

    @property
    def normal(self) -> Vector2D:
        """Vetor normal unitário perpendicular à direção (rotacionado 90 graus anti-horário)."""
        return self.direction.perpendicular()

    @property
    def midpoint(self) -> Point2D:
        """Ponto médio do eixo."""
        return Point2D((self.start.x + self.end.x) / 2.0, (self.start.y + self.end.y) / 2.0)

    @property
    def bounds(self) -> BoundingBox:
        """Caixa delimitadora (BoundingBox) do eixo."""
        return BoundingBox.from_points([self.start, self.end])

    def point_at(self, distance: float) -> Point2D:
        """Calcula o ponto 2D situado a uma distância ao longo do eixo a partir do ponto inicial.

        Args:
            distance: Distância a partir do ponto inicial (pode ser negativa ou superior ao comprimento).
        """
        return self.start.moved_by(self.direction * distance)

    def projected_offset(self, point: Point2D) -> float:
        """Calcula a distância escalar da projeção ortogonal de um ponto 2D sobre a reta suporte do eixo, a partir de start.

        Args:
            point: Ponto 2D no plano XY (pode ou não estar contido no segmento do eixo).

        Returns:
            Distância escalar ao longo da direção do eixo (0.0 em start, length em end).
        """
        return self.start.vector_to(point).dot(self.direction)

    def distance_to_point(self, point: Point2D) -> float:
        """Calcula a menor distância Euclidiana entre um ponto 2D e o segmento linear do eixo.

        Args:
            point: Ponto 2D no plano XY.

        Returns:
            Menor distância até o segmento de reta (perpendicular ou até as extremidades start/end).
        """
        v = self.as_vector
        w = self.start.vector_to(point)

        c1 = w.dot(v)
        if is_non_positive(c1):
            return point.distance_to(self.start)

        c2 = v.dot(v)
        if is_greater_or_equal(c1, c2):
            return point.distance_to(self.end)

        b = c1 / c2
        pb = self.start.moved_by(v * b)
        return point.distance_to(pb)

    def touches_endpoints(self, other: Axis, tolerance: float = JUNCTION_TOLERANCE) -> bool:
        """Verifica se alguma das extremidades (start ou end) deste eixo toca uma extremidade do outro eixo."""
        return (
            self.start.is_same(other.start, tolerance)
            or self.start.is_same(other.end, tolerance)
            or self.end.is_same(other.start, tolerance)
            or self.end.is_same(other.end, tolerance)
        )

    def reversed(self) -> Axis:
        """Retorna o eixo com a orientação invertida (start e end trocados)."""
        return Axis(start=self.end, end=self.start)

    def translated(self, vector: Vector2D) -> Axis:
        """Translada o eixo pelo vetor 2D informado."""
        return Axis(
            start=self.start.moved_by(vector),
            end=self.end.moved_by(vector),
        )

    def transformed(self, transform: Transform2D) -> Axis:
        """Aplica uma transformação afim/rígida 2D ao eixo."""
        return Axis(
            start=transform.apply_point(self.start),
            end=transform.apply_point(self.end),
        )

    def is_parallel(self, other: Axis, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
        """Verifica se este eixo é paralelo ao outro eixo dentro da tolerância."""
        v1 = self.as_vector
        v2 = other.as_vector
        return is_less_or_equal(abs(v1.cross(v2)), tolerance * self.length * other.length, tolerance=0.0)

    def is_collinear(self, other: Axis, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
        """Verifica se ambos os eixos pertencem à mesma reta suporte no plano 2D."""
        if not self.is_parallel(other, tolerance):
            return False
        v_start = self.start.vector_to(other.start)
        if is_zero(v_start.magnitude, tolerance):
            return True
        v1 = self.as_vector
        return is_less_or_equal(abs(v1.cross(v_start)), tolerance * self.length * v_start.magnitude, tolerance=0.0)

    def intersect(self, other: Axis, tolerance: float = GEOMETRIC_TOLERANCE) -> AxisIntersectionResult:
        """Calcula a relação e a interseção geométrica exata entre dois eixos lineares 2D.

        Returns:
            AxisIntersectionResult com relation (DISJOINT, POINT_INTERSECT, TOUCHING_VERTEX ou OVERLAPPING).
        """
        p = self.start
        r = self.as_vector
        q = other.start
        s = other.as_vector

        r_cross_s = r.cross(s)
        qp = p.vector_to(q)
        qp_cross_r = qp.cross(r)

        # 1. Linhas paralelas ou colineares
        if is_zero(r_cross_s, tolerance):
            # Não colineares -> Paralelas disjuntas
            if is_not_zero(qp_cross_r, tolerance):
                return AxisIntersectionResult(relation=AxisRelation.DISJOINT)

            # Colineares: projetamos 'other' sobre o eixo 'self' no parâmetro t
            r_dot_r = r.dot(r)
            t0 = qp.dot(r) / r_dot_r
            t1 = (qp + s).dot(r) / r_dot_r

            t_min = min(t0, t1)
            t_max = max(t0, t1)

            t_start = max(0.0, t_min)
            t_end = min(1.0, t_max)

            # Sem sobreposição
            if is_greater(t_start, t_end, tolerance):
                return AxisIntersectionResult(relation=AxisRelation.DISJOINT)

            # Toque em um único ponto extremo
            if is_close(t_start, t_end, tolerance):
                pt = p.moved_by(r * t_start)
                return AxisIntersectionResult(relation=AxisRelation.TOUCHING_VERTEX, point=pt, t=t_start)

            # Sobreposição contínua (OVERLAPPING)
            pt_a = p.moved_by(r * t_start)
            pt_b = p.moved_by(r * t_end)
            overlap = Axis(start=pt_a, end=pt_b)
            return AxisIntersectionResult(relation=AxisRelation.OVERLAPPING, overlap_segment=overlap)

        # 2. Linhas concorrentes
        t = qp.cross(s) / r_cross_s
        u = qp.cross(r) / r_cross_s

        if is_within_unit(t, tolerance) and is_within_unit(u, tolerance):
            # Clamping numérico para [0.0, 1.0]
            t_clamped = max(0.0, min(1.0, t))
            u_clamped = max(0.0, min(1.0, u))
            pt = p.moved_by(r * t_clamped)

            # Verifica se toca em vértice
            is_vertex_self = is_at_vertex(t_clamped, tolerance)
            is_vertex_other = is_at_vertex(u_clamped, tolerance)

            relation = AxisRelation.TOUCHING_VERTEX if (is_vertex_self or is_vertex_other) else AxisRelation.POINT_INTERSECT
            return AxisIntersectionResult(relation=relation, point=pt, t=t_clamped, u=u_clamped)

        return AxisIntersectionResult(relation=AxisRelation.DISJOINT)

    def intersects(self, other: Axis, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
        """Verifica se há qualquer interseção, toque ou sobreposição entre os eixos."""
        res = self.intersect(other, tolerance=tolerance)
        return res.relation != AxisRelation.DISJOINT

    def overlaps(self, other: Axis, tolerance: float = GEOMETRIC_TOLERANCE) -> bool:
        """Verifica se os eixos são colineares com trecho contínuo sobreposto."""
        res = self.intersect(other, tolerance=tolerance)
        return res.relation == AxisRelation.OVERLAPPING
