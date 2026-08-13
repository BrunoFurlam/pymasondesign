from __future__ import annotations

from attrs import field, frozen
from pymasondesign.common import to_tuple
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.tolerances import (
    OVERLAP_TOLERANCE,
    is_greater,
    is_less,
    is_positive,
)
from pymasondesign.drafting.enums import BondType, WallEnd
from pymasondesign.drafting.opening import Opening


def _convert_bond(val: BondType | str | None) -> BondType:
    if val is None:
        return BondType.NONE
    if isinstance(val, BondType):
        return val
    return BondType(str(val))


@frozen
class Wall:
    """Representação de uma parede estrutural de alvenaria em planta.

    Attributes:
        wall_id: Identificador único da parede no plano (ex.: "P1", "P2").
        axis: Eixo geométrico orientado 2D da parede (Axis).
        thickness: Espessura nominal da parede em metros ou cm (t > 0).
        height: Altura livre específica da parede (se None, herda a altura padrão da FloorPlan).
        openings: Coleção imutável de aberturas contidas na parede.
        start_bond: Tipo de amarração no extremo inicial (start) da parede (DIRECT, INDIRECT, NONE ou None).
        end_bond: Tipo de amarração no extremo final (end) da parede (DIRECT, INDIRECT, NONE ou None).
    """

    wall_id: str = field(converter=str)
    axis: Axis = field()
    thickness: float = field(converter=float)
    height: float | None = field(default=None)
    openings: tuple[Opening, ...] = field(default=(), converter=to_tuple)
    start_bond: BondType = field(default=BondType.NONE, converter=_convert_bond)
    end_bond: BondType = field(default=BondType.NONE, converter=_convert_bond)

    def __attrs_post_init__(self) -> None:
        if not is_positive(self.thickness):
            raise ValueError(f"Espessura da parede (thickness) deve ser positiva, obtido {self.thickness}.")
        if self.height is not None and not is_positive(self.height):
            raise ValueError(f"Altura da parede (height) deve ser positiva se fornecida, obtido {self.height}.")

        # Validação das aberturas
        wall_len = self.axis.length
        sorted_openings = sorted(self.openings, key=lambda op: op.offset_along_wall)

        for i, op in enumerate(sorted_openings):
            op_end = op.offset_along_wall + op.width
            if is_greater(op_end, wall_len, OVERLAP_TOLERANCE):
                raise ValueError(
                    f"Abertura '{op.opening_id}' excede o comprimento da parede '{self.wall_id}' "
                    f"(fim da abertura em {op_end:.3f}, comprimento da parede={wall_len:.3f})."
                )
            if i > 0:
                prev_op = sorted_openings[i - 1]
                prev_end = prev_op.offset_along_wall + prev_op.width
                if is_less(op.offset_along_wall, prev_end, OVERLAP_TOLERANCE):
                    raise ValueError(
                        f"Abertura '{op.opening_id}' sobrepõe a abertura anterior '{prev_op.opening_id}' "
                        f"na parede '{self.wall_id}'."
                    )

    @property
    def length(self) -> float:
        """Comprimento total do eixo da parede."""
        return self.axis.length

    def add_opening(self, opening: Opening) -> Wall:
        """Adiciona uma abertura na parede e retorna a nova instância de Wall."""
        return Wall(
            wall_id=self.wall_id,
            axis=self.axis,
            thickness=self.thickness,
            height=self.height,
            openings=self.openings + (opening,),
            start_bond=self.start_bond,
            end_bond=self.end_bond,
        )

    def add_door(
        self,
        opening_id: str,
        offset_along_wall: float,
        width: float,
        height: float,
    ) -> Wall:
        """Adiciona uma porta na parede e retorna a nova instância de Wall."""
        door = Opening.door(
            opening_id=opening_id,
            offset_along_wall=offset_along_wall,
            width=width,
            height=height,
        )
        return self.add_opening(door)

    def add_window(
        self,
        opening_id: str,
        offset_along_wall: float,
        width: float,
        height: float,
        sill_height: float,
    ) -> Wall:
        """Adiciona uma janela na parede e retorna a nova instância de Wall."""
        window = Opening.window(
            opening_id=opening_id,
            offset_along_wall=offset_along_wall,
            width=width,
            height=height,
            sill_height=sill_height,
        )
        return self.add_opening(window)

    def set_start_bond(self, bond: BondType | str | None) -> Wall:
        """Altera a amarração no extremo inicial (start) da parede (suporta BondType, string ou None)."""
        return Wall(
            wall_id=self.wall_id,
            axis=self.axis,
            thickness=self.thickness,
            height=self.height,
            openings=self.openings,
            start_bond=_convert_bond(bond),
            end_bond=self.end_bond,
        )

    def set_end_bond(self, bond: BondType | str | None) -> Wall:
        """Altera a amarração no extremo final (end) da parede (suporta BondType, string ou None)."""
        return Wall(
            wall_id=self.wall_id,
            axis=self.axis,
            thickness=self.thickness,
            height=self.height,
            openings=self.openings,
            start_bond=self.start_bond,
            end_bond=_convert_bond(bond),
        )

    def set_bond(self, wall_end: WallEnd, bond: BondType | str | None) -> Wall:
        """Altera a amarração no extremo especificado da parede (suporta BondType, string ou None)."""
        if wall_end == WallEnd.START:
            return self.set_start_bond(bond)
        return self.set_end_bond(bond)
