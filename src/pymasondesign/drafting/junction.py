from __future__ import annotations

from attrs import define, field
from pymasondesign.common import to_tuple
from pymasondesign.geometry.point import Point2D
from pymasondesign.drafting.enums import BondType, WallEnd
from pymasondesign.drafting.wall import Wall


@define(frozen=True, slots=True)
class PassingWall:
    """Representação de uma parede que atravessa (passa por) um nó de encontro (Junction).

    Attributes:
        wall_id: Identificador da parede que passa pelo nó.
    """

    wall_id: str = field(converter=str)


@define(frozen=True, slots=True)
class ArrivingWall:
    """Representação de uma parede cuja extremidade chega a um nó de encontro (Junction).

    Attributes:
        wall_id: Identificador da parede incidente.
        wall_end: Extremidade da parede que toca o nó (START ou END).
        bond: Tipo de amarração efetivo nessa extremidade (DIRECT ou INDIRECT).
    """

    wall_id: str = field(converter=str)
    wall_end: WallEnd = field()
    bond: BondType = field()

    @classmethod
    def from_wall(cls, wall: Wall, wall_end: WallEnd) -> ArrivingWall:
        """Cria ArrivingWall extraindo o tipo de amarração configurado na própria parede."""
        bond = wall.start_bond if wall_end == WallEnd.START else wall.end_bond
        return cls(wall_id=wall.wall_id, wall_end=wall_end, bond=bond)


@define(frozen=True, slots=True)
class Junction:
    """Nó de encontro geométrico calculado entre paredes em uma planta baixa (FloorPlan).

    Attributes:
        point: Coordenadas 2D do ponto de encontro.
        passing_walls: Coleção imutável de PassingWall (paredes que atravessam o ponto, com offset).
        arriving_walls: Coleção imutável de ArrivingWall (paredes cujas extremidades chegam ao ponto).
    """

    point: Point2D = field()
    passing_walls: tuple[PassingWall, ...] = field(default=(), converter=to_tuple)
    arriving_walls: tuple[ArrivingWall, ...] = field(default=(), converter=to_tuple)

    @property
    def total_incident_walls(self) -> int:
        """Número total de paredes conectadas a esta junção."""
        return len(self.passing_walls) + len(self.arriving_walls)

    @property
    def has_indirect_bonds(self) -> bool:
        """Indica se alguma parede que chega a este nó possui amarração indireta."""
        return any(aw.bond == BondType.INDIRECT for aw in self.arriving_walls)

    def has_wall(self, wall_id: str) -> bool:
        """Verifica se uma parede participa desta junção (seja como passante ou incidente)."""
        return self.is_passing(wall_id) or self.is_arriving(wall_id)

    def is_passing(self, wall_id: str) -> bool:
        """Verifica se a parede informada atravessa (passa por) esta junção."""
        return any(pw.wall_id == wall_id for pw in self.passing_walls)

    def is_arriving(self, wall_id: str) -> bool:
        """Verifica se a parede informada chega (tem extremidade conectada a) esta junção."""
        return any(aw.wall_id == wall_id for aw in self.arriving_walls)

    def get_participation(self, wall_id: str) -> PassingWall | ArrivingWall | None:
        """Retorna a instância de participação (PassingWall ou ArrivingWall) da parede nesta junção."""
        for pw in self.passing_walls:
            if pw.wall_id == wall_id:
                return pw
        for aw in self.arriving_walls:
            if aw.wall_id == wall_id:
                return aw
        return None
