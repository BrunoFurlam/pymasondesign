from __future__ import annotations

from attrs import define, field
from pymasondesign.geometry.point import Point2D
from pymasondesign.drafting.enums import BondType, WallEnd
from pymasondesign.drafting.wall import Wall


def _convert_passing(val: tuple[PassingWall, ...] | list[PassingWall] | None) -> tuple[PassingWall, ...]:
    if val is None:
        return ()
    return tuple(val)


def _convert_arriving(val: tuple[ArrivingWall, ...] | list[ArrivingWall] | None) -> tuple[ArrivingWall, ...]:
    if val is None:
        return ()
    return tuple(val)


@define(frozen=True, slots=True)
class PassingWall:
    """Representação de uma parede que atravessa (passa por) um nó de encontro (Junction).

    Attributes:
        wall: Parede que passa pelo nó.
        offset: Distância ao longo do eixo da parede onde ocorre a junção (em unidade de comprimento).
    """

    wall: Wall = field()
    offset: float = field(converter=float)

    @classmethod
    def from_wall_and_parameter(cls, wall: Wall, t: float) -> PassingWall:
        """Cria PassingWall a partir da parede e do parâmetro normalizado t (0 < t < 1)."""
        offset = t * wall.axis.length
        return cls(wall=wall, offset=offset)


@define(frozen=True, slots=True)
class ArrivingWall:
    """Representação de uma parede cuja extremidade chega a um nó de encontro (Junction).

    Attributes:
        wall: Parede incidente.
        wall_end: Extremidade da parede que toca o nó (START ou END).
        bond: Tipo de amarração efetivo nessa extremidade (DIRECT ou INDIRECT).
    """

    wall: Wall = field()
    wall_end: WallEnd = field()
    bond: BondType = field()

    @classmethod
    def from_wall(cls, wall: Wall, wall_end: WallEnd) -> ArrivingWall:
        """Cria ArrivingWall extraindo o tipo de amarração configurado na própria parede."""
        bond = wall.start_bond if wall_end == WallEnd.START else wall.end_bond
        return cls(wall=wall, wall_end=wall_end, bond=bond)


@define(frozen=True, slots=True)
class Junction:
    """Nó de encontro geométrico calculado entre paredes em uma planta baixa (FloorPlan).

    Attributes:
        point: Coordenadas 2D do ponto de encontro.
        passing_walls: Coleção imutável de PassingWall (paredes que atravessam o ponto, com offset).
        arriving_walls: Coleção imutável de ArrivingWall (paredes cujas extremidades chegam ao ponto).
    """

    point: Point2D = field()
    passing_walls: tuple[PassingWall, ...] = field(default=(), converter=_convert_passing)
    arriving_walls: tuple[ArrivingWall, ...] = field(default=(), converter=_convert_arriving)

    @property
    def total_incident_walls(self) -> int:
        """Número total de paredes conectadas a esta junção."""
        return len(self.passing_walls) + len(self.arriving_walls)

    @property
    def has_indirect_bonds(self) -> bool:
        """Indica se alguma parede que chega a este nó possui amarração indireta."""
        return any(aw.bond == BondType.INDIRECT for aw in self.arriving_walls)
