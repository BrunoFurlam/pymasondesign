from __future__ import annotations

from typing import TYPE_CHECKING
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.tolerances import (
    GEOMETRIC_TOLERANCE,
    JUNCTION_TOLERANCE,
    is_interior,
)
from pymasondesign.drafting.enums import BondType
from pymasondesign.drafting.wall import Wall
from pymasondesign.drafting.junction import Junction, PassingWall, ArrivingWall
from pymasondesign.elements.panel import MasonryPanel
from pymasondesign.elements.group import PanelGroup
from pymasondesign.elements.floor_plan_model import FloorPlanModel
from pymasondesign.elements.story_model import StoryModel
from pymasondesign.elements.building_model import BuildingModel

if TYPE_CHECKING:
    from pymasondesign.drafting.floor_plan import FloorPlan
    from pymasondesign.drafting.story import Story
    from pymasondesign.drafting.building import Building


class MasonryPanelService:
    """Serviço de domínio responsável pela discretização, derivação e agrupamento de painéis estruturais de alvenaria."""

    @staticmethod
    def derive_panels_from_wall(
        wall: Wall,
        junctions: tuple[Junction, ...] | list[Junction] = (),
        default_height: float | None = None,
    ) -> tuple[MasonryPanel, ...]:
        """Deriva a coleção de painéis resistentes de alvenaria (MasonryPanel) a partir de uma parede.

        A segmentação considera:
        1. As aberturas contidas na parede (vãos de portas e janelas).
        2. Os nós de encontro (Junctions) onde outras paredes chegam ou cruzam o interior da parede.

        Args:
            wall: Parede estrutural do modelo de lançamento (drafting).
            junctions: Coleção opcional de nós de encontro na planta contendo esta parede.
            default_height: Altura padrão a ser utilizada caso wall.height seja None.

        Returns:
            Tupla contendo as instâncias de MasonryPanel derivadas ao longo do eixo da parede.
        """
        effective_height = wall.height if wall.height is not None else default_height
        if effective_height is None or effective_height <= 0:
            raise ValueError(
                f"Altura da parede '{wall.wall_id}' deve ser fornecida e positiva, obtido: {effective_height}."
            )

        wall_len = wall.axis.length
        if wall_len <= GEOMETRIC_TOLERANCE:
            return ()

        # 1. Coleta e ordenação das aberturas
        sorted_openings = sorted(wall.openings, key=lambda op: op.offset_along_wall)

        # 2. Gera segmentos sólidos subtraindo os intervalos das aberturas de [0, wall_len]
        solid_intervals: list[tuple[float, float]] = []
        current_s = 0.0

        for op in sorted_openings:
            op_start = max(0.0, op.offset_along_wall)
            op_end = min(wall_len, op.offset_along_wall + op.width)

            if op_start - current_s > GEOMETRIC_TOLERANCE:
                solid_intervals.append((current_s, op_start))
            current_s = max(current_s, op_end)

        if wall_len - current_s > GEOMETRIC_TOLERANCE:
            solid_intervals.append((current_s, wall_len))

        # 3. Coleta os pontos de corte provenientes de encontros (Junctions)
        junction_offsets: set[float] = set()

        for junc in junctions:
            if junc.is_passing(wall.wall_id):
                offset = wall.axis.projected_offset(junc.point)
                if offset > GEOMETRIC_TOLERANCE and offset < wall_len - GEOMETRIC_TOLERANCE:
                    junction_offsets.add(offset)

        # 4. Subdivide os intervalos sólidos nos pontos de corte das junções
        final_intervals: list[tuple[float, float]] = []

        for seg_start, seg_end in solid_intervals:
            # Encontra pontos de junção estritamente no interior deste segmento
            seg_cuts = sorted(
                [
                    pt
                    for pt in junction_offsets
                    if pt > seg_start + GEOMETRIC_TOLERANCE and pt < seg_end - GEOMETRIC_TOLERANCE
                ]
            )

            c_start = seg_start
            for cut in seg_cuts:
                if cut - c_start > GEOMETRIC_TOLERANCE:
                    final_intervals.append((c_start, cut))
                c_start = cut
            if seg_end - c_start > GEOMETRIC_TOLERANCE:
                final_intervals.append((c_start, seg_end))

        # 5. Constrói as instâncias de MasonryPanel
        panels: list[MasonryPanel] = []
        for idx, (s_start, s_end) in enumerate(final_intervals, start=1):
            pt_a = wall.axis.point_at(s_start)
            pt_b = wall.axis.point_at(s_end)
            panel_axis = Axis(start=pt_a, end=pt_b)

            panels.append(
                MasonryPanel(
                    panel_id=f"{wall.wall_id}_P{idx}",
                    wall_id=wall.wall_id,
                    axis=panel_axis,
                    thickness=wall.thickness,
                    height=effective_height,
                )
            )

        return tuple(panels)

    @staticmethod
    def group_panels_by_direct_bond(floor_plan: FloorPlan) -> tuple[PanelGroup, ...]:
        """Agrupa os painéis de alvenaria de uma planta baixa em componentes conexas de amarração direta.

        Dois painéis são conectados no mesmo grupo se:
        1. Pertencerem à mesma parede contínua e se encontrarem no mesmo ponto de corte de uma junção.
        2. Pertencerem a paredes que se encontram em um nó (Junction) onde a conexão é por amarração direta (BondType.DIRECT).

        Args:
            floor_plan: Planta baixa contendo as paredes, aberturas e configurações de amarração.

        Returns:
            Tupla de instâncias de PanelGroup (PG1, PG2, ...) contendo os painéis agrupados.
        """
        junctions = floor_plan.find_junctions()

        # 1. Deriva todos os painéis para cada parede da planta baixa
        all_panels: list[MasonryPanel] = []
        for wall in floor_plan.walls:
            panels = MasonryPanelService.derive_panels_from_wall(wall, junctions, floor_plan.height)
            all_panels.extend(panels)

        if not all_panels:
            return ()

        num_panels = len(all_panels)
        adj: dict[int, set[int]] = {i: set() for i in range(num_panels)}

        def panel_touches_point(panel: MasonryPanel, pt) -> bool:
            return (
                panel.axis.start.distance_to(pt) <= JUNCTION_TOLERANCE
                or panel.axis.end.distance_to(pt) <= JUNCTION_TOLERANCE
            )

        # 2. Conexões internas entre painéis adjacentes da MESMA parede
        for i in range(num_panels):
            p_i = all_panels[i]
            for j in range(i + 1, num_panels):
                p_j = all_panels[j]
                if p_i.wall_id == p_j.wall_id:
                    # Se extremidades se tocam no mesmo ponto (subdivisão por junção interna sem abertura)
                    if (
                        p_i.axis.end.distance_to(p_j.axis.start) <= JUNCTION_TOLERANCE
                        or p_i.axis.start.distance_to(p_j.axis.end) <= JUNCTION_TOLERANCE
                    ):
                        adj[i].add(j)
                        adj[j].add(i)

        # 3. Conexões entre paredes distintas nos nós de encontro (Junctions)
        for junc in junctions:
            # Coleta os índices dos painéis que tocam o ponto da junção
            passing_indices: list[int] = []
            direct_arriving_indices: list[int] = []

            for idx, panel in enumerate(all_panels):
                if panel_touches_point(panel, junc.point):
                    part = junc.get_participation(panel.wall_id)
                    if isinstance(part, PassingWall):
                        passing_indices.append(idx)
                    elif isinstance(part, ArrivingWall) and part.bond == BondType.DIRECT:
                        direct_arriving_indices.append(idx)

            # Conecta arriving com BondType.DIRECT aos passing panels
            for arr_idx in direct_arriving_indices:
                for pass_idx in passing_indices:
                    adj[arr_idx].add(pass_idx)
                    adj[pass_idx].add(arr_idx)

            # Conecta arriving com BondType.DIRECT entre si (ex.: nós em L com 2 arriving)
            n_arr = len(direct_arriving_indices)
            for a in range(n_arr):
                for b in range(a + 1, n_arr):
                    idx_a = direct_arriving_indices[a]
                    idx_b = direct_arriving_indices[b]
                    adj[idx_a].add(idx_b)
                    adj[idx_b].add(idx_a)

        # 4. Extração das componentes conexas via BFS
        visited = [False] * num_panels
        groups: list[PanelGroup] = []
        group_counter = 1

        for i in range(num_panels):
            if not visited[i]:
                component: list[int] = []
                queue = [i]
                visited[i] = True

                while queue:
                    curr = queue.pop(0)
                    component.append(curr)
                    for neighbor in adj[curr]:
                        if not visited[neighbor]:
                            visited[neighbor] = True
                            queue.append(neighbor)

                # Coleta e ordena os painéis da componente conexa
                comp_panels = tuple(all_panels[idx] for idx in sorted(component))
                groups.append(
                    PanelGroup(
                        group_id=f"PG{group_counter}",
                        panels=comp_panels,
                    )
                )
                group_counter += 1

        return tuple(groups)

    @staticmethod
    def derive_floor_plan_model(floor_plan: FloorPlan) -> FloorPlanModel:
        """Deriva o modelo estrutural da planta baixa (FloorPlanModel) contendo todos os grupos de painéis.

        Args:
            floor_plan: Planta baixa contendo as paredes, aberturas e configurações de amarração.

        Returns:
            Instância imutável de FloorPlanModel com os grupos de painéis conectados por amarração direta.
        """
        groups = MasonryPanelService.group_panels_by_direct_bond(floor_plan)
        return FloorPlanModel(
            plan_id=floor_plan.plan_id,
            height=floor_plan.height,
            groups=groups,
        )

    @staticmethod
    def derive_building_model(
        building: Building,
    ) -> BuildingModel:
        """Deriva o modelo estrutural da edificação completa (BuildingModel) a partir de um Building de lançamento.

        - Discretiza e constrói o catálogo de FloorPlanModel para todas as plantas do edifício.
        - Converte cada Story em StoryModel.
        - Preserva a ordenação estrita de cima para baixo (cota Z decrescente).

        Args:
            building: Edifício físico de lançamento contendo plantas e pavimentos.

        Returns:
            Instância imutável de BuildingModel contendo o catálogo de plantas e os pavimentos ordenados.
        """
        if not building.stories:
            raise ValueError(f"O edifício '{building.building_id}' não possui pavimentos para derivar o modelo.")

        distinct_plans = {
            fp.plan_id: MasonryPanelService.derive_floor_plan_model(fp)
            for fp in building.floor_plans
        }

        building_stories = tuple(
            StoryModel(
                story_id=st.story_id,
                elevation=st.elevation,
                story_height=st.story_height,
                masonry_spec=st.masonry_spec,
                plan_id=st.plan_id,
            )
            for st in building.stories
        )

        return BuildingModel(
            building_id=building.building_id,
            floor_plan_models=tuple(distinct_plans.values()),
            stories=building_stories,
        )
