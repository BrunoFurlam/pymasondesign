from __future__ import annotations

from typing import TYPE_CHECKING
from attrs import field, frozen
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.polygon import Polygon
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.geometry.tolerances import (
    JUNCTION_TOLERANCE,
    is_close,
    is_positive,
    is_greater,
    is_less,
    is_less_or_equal,
)
from pymasondesign.structure.enums import SegmentRole
from pymasondesign.structure.bracing_segment import (
    BracingSegment,
    create_rectangle_polygon,
)
from pymasondesign.structure.bracing_wall import BracingWall

if TYPE_CHECKING:
    from pymasondesign.structure.panel import MasonryPanel
    from pymasondesign.structure.group import PanelGroup
    from pymasondesign.structure.floor_plan_model import FloorPlanModel


@frozen
class BracingOptions:
    """Configurações e parâmetros para determinação de abas colaborantes e paredes de contraventamento.

    Attributes:
        flange_multiplier: Multiplicador k sobre a espessura da alma para limite da aba (padrão 6.0, conforme NBR 16868-1).
        custom_width: Largura colaborante fixa customizada em cm ou metros. Se fornecido, sobrepõe flange_multiplier.
    """

    flange_multiplier: float = field(default=6.0, converter=float)
    custom_width: float | None = field(default=None)

    def __attrs_post_init__(self) -> None:
        if not is_positive(self.flange_multiplier):
            raise ValueError(
                f"Multiplicador de flange (flange_multiplier) deve ser positivo, obtido: {self.flange_multiplier}."
            )
        if self.custom_width is not None and not is_positive(self.custom_width):
            raise ValueError(
                f"Largura colaborante customizada (custom_width) deve ser positiva, obtido: {self.custom_width}."
            )


class BracingWallService:
    """Serviço de domínio para derivação e montagem de paredes de contraventamento (BracingWall).

    Identifica almas orientadas na direção de análise, acoplamentos de almas paralelas por flanges
    curtos e calcula as larguras colaborantes efetivas de abas conforme as prescrições normativas.
    """

    @staticmethod
    def derive_for_group(
        group: PanelGroup,
        direction: Vector2D,
        options: BracingOptions | None = None,
    ) -> tuple[BracingWall, ...]:
        """Deriva as paredes de contraventamento de um PanelGroup para uma dada direção de análise.

        Args:
            group: Grupo estrutural de painéis conexos por amarração direta.
            direction: Vetor de direção da ação resistente analisada (ex.: Vector2D(1, 0) para X).
            options: Opções de cálculo de abas (BracingOptions). Se None, adota os padrões da NBR 16868-1.

        Returns:
            Tupla de instâncias de BracingWall derivadas no grupo para a direção especificada.
        """
        if not is_positive(direction.magnitude):
            raise ValueError("Vetor de direção de análise não pode ser nulo.")

        flange_opts = options if options is not None else BracingOptions()
        u_dir = direction.normalized()

        # 1. Classificação dos painéis do grupo: almas (paralelos à direção) vs transversais (potenciais abas)
        web_panels: list[MasonryPanel] = []
        transverse_panels: list[MasonryPanel] = []

        for p in group.panels:
            u_p = p.axis.direction
            cross_val = abs(u_p.cross(u_dir))
            if is_less_or_equal(cross_val, JUNCTION_TOLERANCE):
                web_panels.append(p)
            else:
                transverse_panels.append(p)

        if not web_panels:
            return ()

        # 2. Agrupamento de almas conectadas em paredes de contraventamento
        num_webs = len(web_panels)
        web_adj: dict[int, set[int]] = {i: set() for i in range(num_webs)}

        for i in range(num_webs):
            w_i = web_panels[i]
            for j in range(i + 1, num_webs):
                w_j = web_panels[j]

                touches = w_i.touches(w_j)
                shares_transverse = False

                if not touches:
                    for t_p in transverse_panels:
                        if t_p.touches(w_i) and t_p.touches(w_j):
                            if flange_opts.custom_width is not None:
                                max_couple_len = 2.0 * flange_opts.custom_width
                            else:
                                max_couple_len = (
                                    flange_opts.flange_multiplier * w_i.thickness
                                    + flange_opts.flange_multiplier * w_j.thickness
                                )
                            # Duas almas são acopladas apenas se o painel transversal tem vão menor que a soma dos limites de abas
                            if is_less(t_p.length, max_couple_len):
                                shares_transverse = True
                                break

                if touches or shares_transverse:
                    web_adj[i].add(j)
                    web_adj[j].add(i)

        # Extração de componentes conexas de almas
        visited: set[int] = set()
        web_clusters: list[list[MasonryPanel]] = []

        for i in range(num_webs):
            if i not in visited:
                cluster = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop(0)
                    cluster.append(web_panels[curr])
                    for nxt in web_adj[curr]:
                        if nxt not in visited:
                            visited.add(nxt)
                            queue.append(nxt)
                web_clusters.append(cluster)

        # 3. Derivação de cada BracingWall
        bracing_walls: list[BracingWall] = []
        dir_label = (
            "X"
            if is_close(abs(u_dir.x), 1.0, JUNCTION_TOLERANCE)
            else ("Y" if is_close(abs(u_dir.y), 1.0, JUNCTION_TOLERANCE) else "DIR")
        )

        for s_idx, cluster_webs in enumerate(web_clusters, start=1):
            wall_id = f"BW_{group.group_id}_{dir_label}_{s_idx:02d}"
            segments_data: list[tuple[str, str, SegmentRole, Axis, float, float, Polygon]] = []

            # 3.1. Criação dos segmentos de ALMA (precedência total, retângulos integrais)
            for w in cluster_webs:
                seg_id = f"{wall_id}_WEB_{w.panel_id}"
                w_axis = w.axis
                w_thick = w.thickness
                w_height = w.height
                w_poly = create_rectangle_polygon(w_axis, w_thick)

                segments_data.append(
                    (seg_id, w.panel_id, SegmentRole.WEB, w_axis, w_thick, w_height, w_poly)
                )

            # 3.2. Identificação e cálculo de ABAS COLABORANTES (FLANGES)
            flange_seg_count = 0
            processed_flange_branches: set[tuple[str, str]] = set()

            for w in cluster_webs:
                w_axis = w.axis
                w_thick = w.thickness

                for t_p in transverse_panels:
                    if not w.touches(t_p):
                        continue

                    t_axis = t_p.axis
                    t_thick = t_p.thickness

                    # Identifica o nó de contato compartilhado entre w e t_p
                    if (
                        w_axis.start.is_same(t_axis.start, JUNCTION_TOLERANCE)
                        or w_axis.end.is_same(t_axis.start, JUNCTION_TOLERANCE)
                    ):
                        j_pt = t_axis.start
                        contact_end = "START"
                        u_branch = t_axis.direction
                        l_disp = t_axis.length
                    else:
                        j_pt = t_axis.end
                        contact_end = "END"
                        u_branch = Vector2D(-t_axis.direction.x, -t_axis.direction.y)
                        l_disp = t_axis.length

                    branch_key = (t_p.panel_id, contact_end)
                    if branch_key in processed_flange_branches:
                        continue
                    processed_flange_branches.add(branch_key)

                    # Precedência da alma: a aba projeta-se para fora da face externa da alma (offset = w_thick / 2)
                    l_disp_ext = l_disp - (w_thick / 2.0)
                    if is_less_or_equal(l_disp_ext, JUNCTION_TOLERANCE):
                        continue

                    # Limite da largura efetiva
                    if flange_opts.custom_width is not None:
                        bf_limit = flange_opts.custom_width
                    else:
                        bf_limit = flange_opts.flange_multiplier * w_thick

                    # Se houver outra alma no cluster conectada a este mesmo painel t_p
                    for other_w in cluster_webs:
                        if other_w.panel_id != w.panel_id and other_w.touches(t_p):
                            other_pt = (
                                t_axis.start
                                if (
                                    other_w.axis.start.is_same(t_axis.start, JUNCTION_TOLERANCE)
                                    or other_w.axis.end.is_same(t_axis.start, JUNCTION_TOLERANCE)
                                )
                                else t_axis.end
                            )
                            dist_between_webs = j_pt.distance_to(other_pt)
                            if is_greater(dist_between_webs, JUNCTION_TOLERANCE):
                                v_other = Vector2D(other_pt.x - j_pt.x, other_pt.y - j_pt.y)
                                if is_positive(v_other.dot(u_branch)):
                                    clear_span = dist_between_webs - (w_thick + other_w.thickness) / 2.0
                                    if is_positive(clear_span):
                                        bf_limit = min(bf_limit, clear_span / 2.0)

                    bf = min(l_disp_ext, bf_limit)
                    if is_less_or_equal(bf, JUNCTION_TOLERANCE):
                        continue

                    # Ponto inicial na face externa da alma
                    p_flange_start = Point2D(
                        j_pt.x + (w_thick / 2.0) * u_branch.x,
                        j_pt.y + (w_thick / 2.0) * u_branch.y,
                    )
                    p_flange_end = Point2D(
                        p_flange_start.x + bf * u_branch.x,
                        p_flange_start.y + bf * u_branch.y,
                    )
                    f_axis = Axis(start=p_flange_start, end=p_flange_end)
                    f_poly = create_rectangle_polygon(f_axis, t_thick)

                    flange_seg_count += 1
                    f_seg_id = f"{wall_id}_FLANGE_{t_p.panel_id}_{flange_seg_count:02d}"

                    segments_data.append(
                        (f_seg_id, t_p.panel_id, SegmentRole.FLANGE, f_axis, t_thick, t_p.height, f_poly)
                    )

            # 4. Construção do sistema local de coordenadas
            u_local = u_dir
            v_local = u_local.perpendicular()

            # Cálculo do centróide global combinado
            total_a = sum(poly.area for _, _, _, _, _, _, poly in segments_data)
            if not is_positive(total_a):
                continue

            qx_global = sum(poly.area * poly.centroid.y for _, _, _, _, _, _, poly in segments_data)
            qy_global = sum(poly.area * poly.centroid.x for _, _, _, _, _, _, poly in segments_data)
            cg_global = Point2D(qy_global / total_a, qx_global / total_a)

            # Transformações Local <-> Global
            local_to_global = Transform2D(origin=cg_global, u_axis=u_local, v_axis=v_local)
            global_to_local = local_to_global.inverse()

            # Conversão dos segmentos para o sistema local
            final_segments: list[BracingSegment] = []

            for seg_id, src_id, role, g_axis, thick, seg_h, _ in segments_data:
                l_axis = g_axis.transformed(global_to_local)

                final_segments.append(
                    BracingSegment(
                        segment_id=seg_id,
                        source_panel_id=src_id,
                        role=role,
                        local_axis=l_axis,
                        global_axis=g_axis,
                        thickness=thick,
                        height=seg_h,
                    )
                )

            wall_height = cluster_webs[0].height

            bracing_walls.append(
                BracingWall(
                    wall_id=wall_id,
                    group_id=group.group_id,
                    direction=u_dir,
                    segments=tuple(final_segments),
                    height=wall_height,
                    local_to_global=local_to_global,
                )
            )

        return tuple(bracing_walls)

    @staticmethod
    def derive_for_floor_plan(
        floor_plan_model: FloorPlanModel,
        direction: Vector2D,
        options: BracingOptions | None = None,
    ) -> tuple[BracingWall, ...]:
        """Deriva todas as paredes de contraventamento de um modelo estrutural de pavimento para uma direção de análise.

        Args:
            floor_plan_model: Modelo estrutural da planta baixa contendo todos os PanelGroups discretizados.
            direction: Vetor unitário de direção da ação resistente analisada.
            options: Opções de cálculo de abas (BracingOptions). Se None, adota os padrões da NBR 16868-1.

        Returns:
            Tupla contendo todas as instâncias de BracingWall derivadas de todos os grupos do pavimento.
        """
        all_walls: list[BracingWall] = []
        for group in floor_plan_model.groups:
            group_walls = BracingWallService.derive_for_group(group, direction, options)
            all_walls.extend(group_walls)
        return tuple(all_walls)
