from __future__ import annotations

import math
from typing import TYPE_CHECKING
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.polygon import Polygon
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.geometry.tolerances import (
    GEOMETRIC_TOLERANCE,
    JUNCTION_TOLERANCE,
    is_zero,
    is_close,
)
from pymasondesign.sections.composite import CompositeSection
from pymasondesign.sections.polygon import PolygonSection
from pymasondesign.design.enums import SegmentRole
from pymasondesign.design.options import FlangeOptions
from pymasondesign.design.segment import ResistantSegment
from pymasondesign.design.section import ResistantSection

if TYPE_CHECKING:
    from pymasondesign.structure.panel import MasonryPanel
    from pymasondesign.structure.group import PanelGroup
    from pymasondesign.structure.floor_plan_model import FloorPlanModel


def create_rectangle_polygon(axis: Axis, thickness: float) -> Polygon:
    """Gera um polígono retangular 2D fechado e orientado no sentido anti-horário centrado no eixo fornecido."""
    half_t = thickness / 2.0
    u = axis.direction
    n = axis.normal  # u.perpendicular() rotacionado 90 graus anti-horário

    # 4 vértices do contorno em sentido anti-horário
    v0 = Point2D(axis.start.x - half_t * n.x, axis.start.y - half_t * n.y)
    v1 = Point2D(axis.end.x - half_t * n.x, axis.end.y - half_t * n.y)
    v2 = Point2D(axis.end.x + half_t * n.x, axis.end.y + half_t * n.y)
    v3 = Point2D(axis.start.x + half_t * n.x, axis.start.y + half_t * n.y)

    return Polygon(vertices=(v0, v1, v2, v3))


class ResistantSectionService:
    """Serviço de domínio para derivação e montagem de seções resistentes (ResistantSection).

    Executa a análise de precedência de almas, determinação das larguras colaborantes de abas
    conforme opções normativas e cálculo de inércias e transformações em coordenadas locais.
    """

    @staticmethod
    def derive_for_group(
        group: PanelGroup,
        direction: Vector2D,
        options: FlangeOptions | None = None,
    ) -> tuple[ResistantSection, ...]:
        """Deriva as seções resistentes de um PanelGroup para uma dada direção de análise.

        Args:
            group: Grupo estrutural de painéis conexos por amarração direta.
            direction: Vetor de direção da ação resistente analisada (ex.: Vector2D(1, 0) para X).
            options: Opções de cálculo de flange (FlangeOptions). Se None, adota os padrões da NBR 16868-1.

        Returns:
            Tupla de instâncias de ResistantSection derivadas no grupo para a direção especificada.
        """
        if direction.magnitude <= GEOMETRIC_TOLERANCE:
            raise ValueError("Vetor de direção de análise não pode ser nulo.")

        flange_opts = options if options is not None else FlangeOptions()
        u_dir = direction.normalized()

        # 1. Classificação dos painéis do grupo: almas (paralelos à direção) vs transversais (potenciais abas)
        web_panels: list[MasonryPanel] = []
        transverse_panels: list[MasonryPanel] = []

        for p in group.panels:
            u_p = p.axis.direction
            cross_val = abs(u_p.cross(u_dir))
            if cross_val <= JUNCTION_TOLERANCE:
                web_panels.append(p)
            else:
                transverse_panels.append(p)

        if not web_panels:
            return ()

        # 2. Agrupamento de almas conectadas em seções resistentes
        # Dois painéis de alma pertencem à mesma seção se:
        # a) Se tocam diretamente ou são colineares adjacentes; OU
        # b) Estão conectados por um painel transversal em comum (flange de acoplamento como em U, C, H).
        num_webs = len(web_panels)
        web_adj: dict[int, set[int]] = {i: set() for i in range(num_webs)}

        for i in range(num_webs):
            w_i = web_panels[i]
            for j in range(i + 1, num_webs):
                w_j = web_panels[j]

                # Contato direto
                touches = w_i.touches(w_j)
                shares_transverse = False

                if not touches:
                    for t_p in transverse_panels:
                        if t_p.touches(w_i) and t_p.touches(w_j):
                            if flange_opts.custom_width is not None:
                                max_couple_len = 2.0 * flange_opts.custom_width
                            else:
                                max_couple_len = (
                                    flange_opts.max_multiplier * w_i.thickness
                                    + flange_opts.max_multiplier * w_j.thickness
                                )
                            # Duas almas são acopladas apenas se o painel transversal que as acopla
                            # tem comprimento menor que a soma dos limites de abas (ex.: 6*t_1 + 6*t_2).
                            if t_p.length < max_couple_len:
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

        # 3. Derivação de cada ResistantSection
        sections: list[ResistantSection] = []
        dir_label = "X" if is_close(abs(u_dir.x), 1.0, JUNCTION_TOLERANCE) else ("Y" if is_close(abs(u_dir.y), 1.0, JUNCTION_TOLERANCE) else "DIR")

        for s_idx, cluster_webs in enumerate(web_clusters, start=1):
            section_id = f"RS_{group.group_id}_{dir_label}_{s_idx:02d}"
            segments_data: list[tuple[str, str, SegmentRole, Axis, float, float, float, Polygon]] = []

            # 3.1. Criação dos segmentos de ALMA (precedência total, retângulos integrais)
            for w in cluster_webs:
                seg_id = f"{section_id}_WEB_{w.panel_id}"
                w_axis = w.axis
                w_thick = w.thickness
                w_len = w.length
                w_height = w.height
                w_poly = create_rectangle_polygon(w_axis, w_thick)

                segments_data.append(
                    (seg_id, w.panel_id, SegmentRole.WEB, w_axis, w_thick, w_len, w_height, w_poly)
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
                    if l_disp_ext <= JUNCTION_TOLERANCE:
                        continue

                    # Limite da largura efetiva
                    if flange_opts.custom_width is not None:
                        bf_limit = flange_opts.custom_width
                    else:
                        bf_limit = flange_opts.max_multiplier * w_thick

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
                            if dist_between_webs > JUNCTION_TOLERANCE:
                                v_other = Vector2D(other_pt.x - j_pt.x, other_pt.y - j_pt.y)
                                if v_other.dot(u_branch) > 0.0:
                                    clear_span = dist_between_webs - (w_thick + other_w.thickness) / 2.0
                                    if clear_span > 0:
                                        bf_limit = min(bf_limit, clear_span / 2.0)

                    bf = min(l_disp_ext, bf_limit)
                    if bf <= JUNCTION_TOLERANCE:
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
                    f_seg_id = f"{section_id}_FLANGE_{t_p.panel_id}_{flange_seg_count:02d}"

                    segments_data.append(
                        (f_seg_id, t_p.panel_id, SegmentRole.FLANGE, f_axis, t_thick, bf, t_p.height, f_poly)
                    )

            # 4. Construção do sistema local de coordenadas e da CompositeSection
            # Eixo X local alinhado à direção de análise u_dir
            # Eixo Y local é u_dir.perpendicular() (perpendicular à esquerda)
            u_local = u_dir
            v_local = u_local.perpendicular()

            # Cálculo do centróide global combinado
            total_a = sum(poly.area for _, _, _, _, _, _, _, poly in segments_data)
            if total_a <= 0:
                continue

            qx_global = sum(poly.area * poly.centroid.y for _, _, _, _, _, _, _, poly in segments_data)
            qy_global = sum(poly.area * poly.centroid.x for _, _, _, _, _, _, _, poly in segments_data)
            cg_global = Point2D(qy_global / total_a, qx_global / total_a)

            # Transformações Local <-> Global
            local_to_global = Transform2D(origin=cg_global, u_axis=u_local, v_axis=v_local)
            global_to_local = local_to_global.inverse()

            # Conversão dos segmentos para o sistema local
            final_segments: list[ResistantSegment] = []
            comp_section = CompositeSection()

            for seg_id, src_id, role, g_axis, thick, eff_len, seg_h, g_poly in segments_data:
                l_axis = g_axis.transformed(global_to_local)
                l_poly = g_poly.transformed(global_to_local)

                final_segments.append(
                    ResistantSegment(
                        segment_id=seg_id,
                        source_panel_id=src_id,
                        role=role,
                        local_axis=l_axis,
                        global_axis=g_axis,
                        thickness=thick,
                        effective_length=eff_len,
                        height=seg_h,
                        local_polygon=l_poly,
                        global_polygon=g_poly,
                    )
                )

                comp_section.add_solid(PolygonSection(polygon=l_poly))

            # Propriedades da seção em coordenadas locais
            props = comp_section.compute_properties()

            section_height = cluster_webs[0].height

            sections.append(
                ResistantSection(
                    section_id=section_id,
                    group_id=group.group_id,
                    direction=u_dir,
                    segments=tuple(final_segments),
                    height=section_height,
                    properties=props,
                    geometric_section=comp_section,
                    local_to_global=local_to_global,
                )
            )

        return tuple(sections)

    @staticmethod
    def derive_for_floor_plan(
        floor_plan_model: FloorPlanModel,
        direction: Vector2D,
        options: FlangeOptions | None = None,
    ) -> tuple[ResistantSection, ...]:
        """Deriva todas as seções resistentes de um modelo estrutural de pavimento para uma direção de análise.

        Args:
            floor_plan_model: Modelo estrutural da planta baixa contendo todos os PanelGroups discretizados.
            direction: Vetor unitário de direção da ação resistente analisada.
            options: Opções de cálculo de flange (FlangeOptions). Se None, adota os padrões da NBR 16868-1.

        Returns:
            Tupla contendo todas as ResistantSections derivadas de todos os grupos do pavimento.
        """
        all_sections: list[ResistantSection] = []
        for group in floor_plan_model.groups:
            group_sections = ResistantSectionService.derive_for_group(group, direction, options)
            all_sections.extend(group_sections)
        return tuple(all_sections)
