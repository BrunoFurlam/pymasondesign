from __future__ import annotations

import math
from attrs import field, frozen
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.tolerances import (
    JUNCTION_TOLERANCE,
    OVERLAP_TOLERANCE,
    is_within_unit,
    is_at_start,
    is_at_end,
    is_interior,
)
from pymasondesign.common import to_tuple
from pymasondesign.drafting.enums import BondType, WallEnd
from pymasondesign.drafting.wall import Wall
from pymasondesign.drafting.opening import Opening
from pymasondesign.drafting.junction import Junction, ArrivingWall, PassingWall


@frozen
class FloorPlan:
    """Planta baixa de alvenaria estrutural 2D compartilhável entre pavimentos.

    Attributes:
        plan_id: Identificador único da planta (ex.: "PLAN_TIPO", "PLAN_TERREO").
        height: Altura padrão das paredes nesta planta em metros ou cm (H > 0).
        walls: Coleção imutável de paredes da planta.
    """

    plan_id: str = field(converter=str)
    height: float = field(converter=float)
    walls: tuple[Wall, ...] = field(default=(), converter=to_tuple)

    def __attrs_post_init__(self) -> None:
        if self.height <= 0:
            raise ValueError(f"Altura da planta (height) deve ser positiva, obtido {self.height}.")

        # Validação de unicidade de IDs de parede
        seen_ids = set()
        for wall in self.walls:
            if wall.wall_id in seen_ids:
                raise ValueError(f"ID de parede duplicado na planta '{self.plan_id}': '{wall.wall_id}'.")
            seen_ids.add(wall.wall_id)

        # Validações de amarração e aberturas contra encontros
        self._validate_wall_bonds_have_junctions()
        self._validate_openings_do_not_intersect_junctions()

    @property
    def total_wall_length(self) -> float:
        """Soma dos comprimentos de todas as paredes da planta."""
        return sum(w.length for w in self.walls)

    def find_wall(self, wall_id: str) -> Wall | None:
        """Busca uma parede pelo seu identificador na planta."""
        for w in self.walls:
            if w.wall_id == wall_id:
                return w
        return None

    def add_wall(self, wall: Wall) -> FloorPlan:
        """Adiciona uma parede na planta e retorna a nova FloorPlan."""
        return FloorPlan(plan_id=self.plan_id, height=self.height, walls=self.walls + (wall,))

    def add_opening(self, wall_id: str, opening: Opening) -> FloorPlan:
        """Adiciona uma abertura a uma parede existente na planta e retorna a nova FloorPlan."""
        target_wall = self.find_wall(wall_id)
        if target_wall is None:
            raise KeyError(f"Parede '{wall_id}' não encontrada na planta '{self.plan_id}'.")

        updated_wall = target_wall.add_opening(opening)
        new_walls = tuple(updated_wall if w.wall_id == wall_id else w for w in self.walls)
        return FloorPlan(plan_id=self.plan_id, height=self.height, walls=new_walls)

    def add_door(
        self,
        wall_id: str,
        opening_id: str,
        offset_along_wall: float,
        width: float,
        height: float,
    ) -> FloorPlan:
        """Adiciona uma porta na parede indicada da planta e retorna a nova FloorPlan."""
        door = Opening.door(
            opening_id=opening_id,
            offset_along_wall=offset_along_wall,
            width=width,
            height=height,
        )
        return self.add_opening(wall_id=wall_id, opening=door)

    def add_window(
        self,
        wall_id: str,
        opening_id: str,
        offset_along_wall: float,
        width: float,
        height: float,
        sill_height: float,
    ) -> FloorPlan:
        """Adiciona uma janela na parede indicada da planta e retorna a nova FloorPlan."""
        window = Opening.window(
            opening_id=opening_id,
            offset_along_wall=offset_along_wall,
            width=width,
            height=height,
            sill_height=sill_height,
        )
        return self.add_opening(wall_id=wall_id, opening=window)

    def set_wall_bond(self, wall_id: str, wall_end: WallEnd, bond: BondType | str | None) -> FloorPlan:
        """Altera a amarração no extremo de uma parede existente na planta e retorna a nova FloorPlan.

        Só é permitido definir amarração (DIRECT ou INDIRECT) se houver uma junção real naquele extremo.
        """
        target_wall = self.find_wall(wall_id)
        if target_wall is None:
            raise KeyError(f"Parede '{wall_id}' não encontrada na planta '{self.plan_id}'.")

        if bond is None:
            bond_enum = BondType.NONE
        elif isinstance(bond, BondType):
            bond_enum = bond
        else:
            bond_enum = BondType(str(bond))

        if bond_enum != BondType.NONE:
            # Verifica se há junção no extremo indicado
            junctions = self.find_junctions()
            has_junction = False
            for j in junctions:
                part = j.get_participation(wall_id)
                if isinstance(part, ArrivingWall) and part.wall_end == wall_end:
                    has_junction = True
                    break

            if not has_junction:
                raise ValueError(
                    f"Não é possível definir amarração '{bond_enum.value}' na extremidade {wall_end.value} "
                    f"da parede '{wall_id}', pois não há junção com outra parede neste ponto."
                )

        updated_wall = target_wall.set_bond(wall_end=wall_end, bond=bond_enum)
        new_walls = tuple(updated_wall if w.wall_id == wall_id else w for w in self.walls)
        return FloorPlan(plan_id=self.plan_id, height=self.height, walls=new_walls)

    def find_junctions(self, tolerance: float = JUNCTION_TOLERANCE) -> tuple[Junction, ...]:
        """Calcula e identifica todos os nós de encontro (Junctions) entre as paredes da planta.

        Returns:
            Coleção imutável de Junctions contendo as paredes passando e chegando em cada nó.
        """
        candidate_points: list[Point2D] = []

        def get_or_add_point(pt: Point2D) -> Point2D:
            for c in candidate_points:
                if pt.distance_to(c) <= tolerance:
                    return c
            candidate_points.append(pt)
            return pt

        # 1. Coleta pontos de interseção e extremos de eixos que tocam outras paredes
        n_walls = len(self.walls)
        for i in range(n_walls):
            w_i = self.walls[i]
            for j in range(i + 1, n_walls):
                w_j = self.walls[j]
                res = w_i.axis.intersect(w_j.axis, tolerance=tolerance)
                if res.point is not None:
                    get_or_add_point(res.point)

        for w_i in self.walls:
            for end_pt in (w_i.axis.start, w_i.axis.end):
                for w_j in self.walls:
                    if w_i.wall_id == w_j.wall_id:
                        continue
                    # Projeção de end_pt sobre w_j.axis
                    p_start = w_j.axis.start
                    r = Vector2D(w_j.axis.dx, w_j.axis.dy)
                    r_sq = r.dot(r)
                    v_pt = Vector2D(end_pt.x - p_start.x, end_pt.y - p_start.y)
                    t = v_pt.dot(r) / r_sq
                    if is_within_unit(t, tolerance):
                        p_proj = Point2D(p_start.x + t * r.x, p_start.y + t * r.y)
                        if end_pt.distance_to(p_proj) <= tolerance:
                            get_or_add_point(p_proj)

        # 2. Para cada ponto de encontro encontrado, analisa as incidências de todas as paredes
        junctions: list[Junction] = []
        for pt in candidate_points:
            passing: list[PassingWall] = []
            arriving: list[ArrivingWall] = []

            for wall in self.walls:
                p_start = wall.axis.start
                r = Vector2D(wall.axis.dx, wall.axis.dy)
                r_sq = r.dot(r)
                v_pt = Vector2D(pt.x - p_start.x, pt.y - p_start.y)
                t = v_pt.dot(r) / r_sq

                if is_within_unit(t, tolerance):
                    p_proj = Point2D(p_start.x + t * r.x, p_start.y + t * r.y)
                    if pt.distance_to(p_proj) <= tolerance:
                        # Chegando no início (START)
                        if is_at_start(t, tolerance) or pt.distance_to(wall.axis.start) <= tolerance:
                            arriving.append(ArrivingWall.from_wall(wall, WallEnd.START))
                        # Chegando no fim (END)
                        elif is_at_end(t, tolerance) or pt.distance_to(wall.axis.end) <= tolerance:
                            arriving.append(ArrivingWall.from_wall(wall, WallEnd.END))
                        # Passando no interior (0 < t < 1)
                        elif is_interior(t, tolerance):
                            passing.append(PassingWall(wall_id=wall.wall_id))

            if len(passing) + len(arriving) >= 2:
                junctions.append(
                    Junction(
                        point=pt,
                        passing_walls=tuple(passing),
                        arriving_walls=tuple(arriving),
                    )
                )

        return tuple(junctions)

    def get_junction_exclusion_intervals(
        self, wall_id: str, tolerance: float = JUNCTION_TOLERANCE
    ) -> tuple[tuple[float, float, str], ...]:
        """Calcula os intervalos ao longo do eixo da parede ocupados por cruzamentos/encontros com outras paredes.

        Returns:
            Tupla de tuplas (offset_min, offset_max, intersecting_wall_id).
        """
        target_wall = self.find_wall(wall_id)
        if target_wall is None:
            raise KeyError(f"Parede '{wall_id}' não encontrada na planta '{self.plan_id}'.")

        wall_len = target_wall.length
        v1 = Vector2D(target_wall.axis.dx, target_wall.axis.dy)
        mag_v1 = v1.magnitude

        intervals: list[tuple[float, float, str]] = []
        junctions = self.find_junctions(tolerance=tolerance)

        for j in junctions:
            # 1. Caso o target_wall passe pela junção (PassingWall)
            for pw in j.passing_walls:
                if pw.wall_id == wall_id:
                    offset = target_wall.axis.projected_offset(j.point)
                    # Para todas as outras paredes na junção
                    for other_pw in j.passing_walls:
                        if other_pw.wall_id != wall_id:
                            other_w = self.find_wall(other_pw.wall_id)
                            if other_w is not None:
                                delta_s = self._calc_projected_half_thickness(v1, mag_v1, other_w)
                                s_min = max(0.0, offset - delta_s)
                                s_max = min(wall_len, offset + delta_s)
                                intervals.append((s_min, s_max, other_pw.wall_id))
                    for other_aw in j.arriving_walls:
                        if other_aw.wall_id != wall_id:
                            other_w = self.find_wall(other_aw.wall_id)
                            if other_w is not None:
                                delta_s = self._calc_projected_half_thickness(v1, mag_v1, other_w)
                                s_min = max(0.0, offset - delta_s)
                                s_max = min(wall_len, offset + delta_s)
                                intervals.append((s_min, s_max, other_aw.wall_id))

            # 2. Caso o target_wall chegue à junção (ArrivingWall)
            for aw in j.arriving_walls:
                if aw.wall_id == wall_id:
                    # Para todas as outras paredes na junção
                    other_wall_ids: list[str] = []
                    for other_pw in j.passing_walls:
                        if other_pw.wall_id != wall_id:
                            other_wall_ids.append(other_pw.wall_id)
                    for other_aw in j.arriving_walls:
                        if other_aw.wall_id != wall_id:
                            other_wall_ids.append(other_aw.wall_id)

                    for other_wid in other_wall_ids:
                        other_w = self.find_wall(other_wid)
                        if other_w is not None:
                            delta_s = self._calc_projected_half_thickness(v1, mag_v1, other_w)
                            if aw.wall_end == WallEnd.START:
                                s_min = 0.0
                                s_max = min(wall_len, delta_s)
                                intervals.append((s_min, s_max, other_w.wall_id))
                            else:  # WallEnd.END
                                s_min = max(0.0, wall_len - delta_s)
                                s_max = wall_len
                                intervals.append((s_min, s_max, other_w.wall_id))

        return tuple(intervals)

    @staticmethod
    def _calc_projected_half_thickness(v1: Vector2D, mag_v1: float, other_wall: Wall) -> float:
        """Calcula a meia-espessura projetada da outra parede ao longo do eixo da parede principal."""
        v2 = Vector2D(other_wall.axis.dx, other_wall.axis.dy)
        mag_v2 = v2.magnitude
        if mag_v1 <= 1e-9 or mag_v2 <= 1e-9:
            return other_wall.thickness / 2.0

        sin_theta = abs(v1.cross(v2)) / (mag_v1 * mag_v2)
        if sin_theta <= 1e-4:
            return other_wall.thickness / 2.0

        return (other_wall.thickness / 2.0) / sin_theta

    def _validate_wall_bonds_have_junctions(self) -> None:
        """Garante que paredes só possuam amarrações (DIRECT ou INDIRECT) em extremidades onde há junção."""
        if not self.walls:
            return

        junctions = self.find_junctions()
        arriving_ends: set[tuple[str, WallEnd]] = set()
        for j in junctions:
            for aw in j.arriving_walls:
                arriving_ends.add((aw.wall_id, aw.wall_end))

        for wall in self.walls:
            if wall.start_bond != BondType.NONE:
                if (wall.wall_id, WallEnd.START) not in arriving_ends:
                    raise ValueError(
                        f"A parede '{wall.wall_id}' possui amarração '{wall.start_bond.value}' no início (START), "
                        f"mas não há junção com outra parede neste ponto."
                    )
            if wall.end_bond != BondType.NONE:
                if (wall.wall_id, WallEnd.END) not in arriving_ends:
                    raise ValueError(
                        f"A parede '{wall.wall_id}' possui amarração '{wall.end_bond.value}' no fim (END), "
                        f"mas não há junção com outra parede neste ponto."
                    )

    def _validate_openings_do_not_intersect_junctions(self) -> None:
        """Garante que nenhuma abertura intercepte zonas de cruzamento ou encontro de paredes."""
        if not self.walls:
            return

        for wall in self.walls:
            if not wall.openings:
                continue
            exclusion_intervals = self.get_junction_exclusion_intervals(wall.wall_id)
            for op in wall.openings:
                op_start = op.offset_along_wall
                op_end = op.offset_along_wall + op.width
                for s_min, s_max, other_id in exclusion_intervals:
                    if max(op_start, s_min) < min(op_end, s_max) - OVERLAP_TOLERANCE:
                        raise ValueError(
                            f"Abertura '{op.opening_id}' na parede '{wall.wall_id}' ([{op_start:.3f}, {op_end:.3f}]) "
                            f"intercepta a zona de cruzamento com a parede '{other_id}' ([{s_min:.3f}, {s_max:.3f}])."
                        )
