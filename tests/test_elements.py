from __future__ import annotations

import unittest
from pymasondesign.geometry import Point2D, Axis
from pymasondesign.drafting import (
    Wall,
    Opening,
    OpeningType,
    Junction,
    PassingWall,
    ArrivingWall,
    WallEnd,
    BondType,
    FloorPlan,
    Story,
    Building,
)
from pymasondesign.materials import NBR16868MasonryFactory
from pymasondesign.elements import (
    MasonryPanel,
    PanelGroup,
    FloorPlanModel,
    StoryModel,
    BuildingModel,
    MasonryPanelService,
)


class TestElements(unittest.TestCase):
    def test_masonry_panel_attributes_and_validations(self):
        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(4.0, 3.0))
        panel = MasonryPanel(
            panel_id="P1_P1",
            wall_id="P1",
            axis=axis,
            thickness=0.14,
            height=2.80,
        )

        self.assertEqual(panel.panel_id, "P1_P1")
        self.assertEqual(panel.wall_id, "P1")
        self.assertEqual(panel.axis, axis)
        self.assertAlmostEqual(panel.thickness, 0.14)
        self.assertAlmostEqual(panel.height, 2.80)
        self.assertAlmostEqual(panel.length, 5.0)

        # Validações de espessura e altura positivas
        with self.assertRaises(ValueError):
            MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=axis, thickness=0.0, height=2.80)
        with self.assertRaises(ValueError):
            MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=axis, thickness=-0.14, height=2.80)
        with self.assertRaises(ValueError):
            MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=axis, thickness=0.14, height=0.0)
        with self.assertRaises(ValueError):
            MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=axis, thickness=0.14, height=-2.80)

    def test_derive_panels_from_solid_wall_no_openings(self):
        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(5.0, 0.0))
        wall = Wall(wall_id="P1", axis=axis, thickness=0.14, height=2.80)

        panels = MasonryPanelService.derive_panels_from_wall(wall)
        self.assertEqual(len(panels), 1)

        p1 = panels[0]
        self.assertEqual(p1.panel_id, "P1_P1")
        self.assertEqual(p1.wall_id, "P1")
        self.assertEqual(p1.axis.start, Point2D(0.0, 0.0))
        self.assertEqual(p1.axis.end, Point2D(5.0, 0.0))
        self.assertAlmostEqual(p1.length, 5.0)
        self.assertAlmostEqual(p1.thickness, 0.14)
        self.assertAlmostEqual(p1.height, 2.80)

    def test_derive_panels_with_intermediate_opening(self):
        # Parede de 6m com porta de 1m a 2m do início
        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(6.0, 0.0))
        door = Opening.door(opening_id="PORTA_1", offset_along_wall=2.0, width=1.0, height=2.10)
        wall = Wall(wall_id="P1", axis=axis, thickness=0.14, height=2.80, openings=[door])

        panels = MasonryPanelService.derive_panels_from_wall(wall)
        self.assertEqual(len(panels), 2)

        # Painel 1: de 0.0 a 2.0
        self.assertEqual(panels[0].panel_id, "P1_P1")
        self.assertEqual(panels[0].axis.start, Point2D(0.0, 0.0))
        self.assertEqual(panels[0].axis.end, Point2D(2.0, 0.0))
        self.assertAlmostEqual(panels[0].length, 2.0)

        # Painel 2: de 3.0 a 6.0
        self.assertEqual(panels[1].panel_id, "P1_P2")
        self.assertEqual(panels[1].axis.start, Point2D(3.0, 0.0))
        self.assertEqual(panels[1].axis.end, Point2D(6.0, 0.0))
        self.assertAlmostEqual(panels[1].length, 3.0)

    def test_derive_panels_with_opening_at_edges(self):
        # Abertura encostada no início (offset 0.0)
        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(5.0, 0.0))
        door_start = Opening.door(opening_id="PORTA_START", offset_along_wall=0.0, width=1.20, height=2.10)
        wall_start = Wall(wall_id="P1", axis=axis, thickness=0.14, height=2.80, openings=[door_start])

        panels_start = MasonryPanelService.derive_panels_from_wall(wall_start)
        self.assertEqual(len(panels_start), 1)
        self.assertEqual(panels_start[0].panel_id, "P1_P1")
        self.assertEqual(panels_start[0].axis.start, Point2D(1.20, 0.0))
        self.assertEqual(panels_start[0].axis.end, Point2D(5.0, 0.0))
        self.assertAlmostEqual(panels_start[0].length, 3.80)

        # Abertura encostada no fim (offset 3.80, width 1.20 -> termina em 5.0)
        door_end = Opening.door(opening_id="PORTA_END", offset_along_wall=3.80, width=1.20, height=2.10)
        wall_end = Wall(wall_id="P2", axis=axis, thickness=0.14, height=2.80, openings=[door_end])

        panels_end = MasonryPanelService.derive_panels_from_wall(wall_end)
        self.assertEqual(len(panels_end), 1)
        self.assertEqual(panels_end[0].panel_id, "P2_P1")
        self.assertEqual(panels_end[0].axis.start, Point2D(0.0, 0.0))
        self.assertEqual(panels_end[0].axis.end, Point2D(3.80, 0.0))
        self.assertAlmostEqual(panels_end[0].length, 3.80)

    def test_derive_panels_with_multiple_openings(self):
        # Parede de 10m com porta [2, 3] e janela [5, 7]
        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(10.0, 0.0))
        door = Opening.door(opening_id="D1", offset_along_wall=2.0, width=1.0, height=2.10)
        window = Opening.window(opening_id="J1", offset_along_wall=5.0, width=2.0, height=1.20, sill_height=1.00)
        wall = Wall(wall_id="P1", axis=axis, thickness=0.14, height=2.80, openings=[window, door])

        panels = MasonryPanelService.derive_panels_from_wall(wall)
        self.assertEqual(len(panels), 3)

        self.assertEqual(panels[0].panel_id, "P1_P1")
        self.assertAlmostEqual(panels[0].length, 2.0)

        self.assertEqual(panels[1].panel_id, "P1_P2")
        self.assertAlmostEqual(panels[1].length, 2.0)  # De 3.0 a 5.0

        self.assertEqual(panels[2].panel_id, "P1_P3")
        self.assertAlmostEqual(panels[2].length, 3.0)  # De 7.0 a 10.0

    def test_derive_panels_with_junction_split(self):
        # Parede de 6m sem aberturas dividida ao meio por nó de encontro em T (offset = 3.0)
        axis_main = Axis(start=Point2D(0.0, 0.0), end=Point2D(6.0, 0.0))
        wall_main = Wall(wall_id="P_MAIN", axis=axis_main, thickness=0.14, height=2.80)

        axis_cross = Axis(start=Point2D(3.0, 0.0), end=Point2D(3.0, 4.0))
        wall_cross = Wall(wall_id="P_CROSS", axis=axis_cross, thickness=0.14, height=2.80)

        junction = Junction(
            point=Point2D(3.0, 0.0),
            passing_walls=(PassingWall(wall_id="P_MAIN"),),
            arriving_walls=(ArrivingWall(wall_id="P_CROSS", wall_end=WallEnd.START, bond=BondType.DIRECT),),
        )

        panels = MasonryPanelService.derive_panels_from_wall(wall_main, junctions=(junction,))
        self.assertEqual(len(panels), 2)

        self.assertEqual(panels[0].panel_id, "P_MAIN_P1")
        self.assertEqual(panels[0].axis.start, Point2D(0.0, 0.0))
        self.assertEqual(panels[0].axis.end, Point2D(3.0, 0.0))
        self.assertAlmostEqual(panels[0].length, 3.0)

        self.assertEqual(panels[1].panel_id, "P_MAIN_P2")
        self.assertEqual(panels[1].axis.start, Point2D(3.0, 0.0))
        self.assertEqual(panels[1].axis.end, Point2D(6.0, 0.0))
        self.assertAlmostEqual(panels[1].length, 3.0)

    def test_derive_panels_with_both_opening_and_junction(self):
        # Parede de 10m com porta em [1, 2] e junção em T no ponto 6.0
        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(10.0, 0.0))
        door = Opening.door(opening_id="D1", offset_along_wall=1.0, width=1.0, height=2.10)
        wall = Wall(wall_id="P1", axis=axis, thickness=0.14, height=2.80, openings=[door])

        junction = Junction(
            point=Point2D(6.0, 0.0),
            passing_walls=(PassingWall(wall_id="P1"),),
        )

        panels = MasonryPanelService.derive_panels_from_wall(wall, junctions=(junction,))
        self.assertEqual(len(panels), 3)

        # Painel 1: de 0.0 a 1.0
        self.assertAlmostEqual(panels[0].length, 1.0)
        # Painel 2: de 2.0 a 6.0 (dividido pela junção)
        self.assertAlmostEqual(panels[1].length, 4.0)
        # Painel 3: de 6.0 a 10.0
        self.assertAlmostEqual(panels[2].length, 4.0)

    def test_derive_panels_height_resolution(self):
        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(4.0, 0.0))

        # Parede sem altura explicitada usando default_height
        wall_no_h = Wall(wall_id="P1", axis=axis, thickness=0.14, height=None)
        panels = MasonryPanelService.derive_panels_from_wall(wall_no_h, default_height=3.0)
        self.assertEqual(len(panels), 1)
        self.assertAlmostEqual(panels[0].height, 3.0)

        # Sem altura em nenhum lugar -> Erro
        with self.assertRaises(ValueError):
            MasonryPanelService.derive_panels_from_wall(wall_no_h, default_height=None)
        with self.assertRaises(ValueError):
            MasonryPanelService.derive_panels_from_wall(wall_no_h, default_height=-1.0)

    def test_panel_group_attributes_and_validations(self):
        p1 = MasonryPanel(
            panel_id="P1_P1",
            wall_id="P1",
            axis=Axis(start=Point2D(0.0, 0.0), end=Point2D(3.0, 0.0)),
            thickness=0.14,
            height=2.80,
        )
        p2 = MasonryPanel(
            panel_id="P2_P1",
            wall_id="P2",
            axis=Axis(start=Point2D(3.0, 0.0), end=Point2D(3.0, 4.0)),
            thickness=0.14,
            height=2.80,
        )

        group = PanelGroup(group_id="PG1", panels=(p1, p2))
        self.assertEqual(group.group_id, "PG1")
        self.assertEqual(len(group.panels), 2)
        self.assertAlmostEqual(group.total_length, 7.0)
        self.assertEqual(group.wall_ids, ("P1", "P2"))
        self.assertEqual(group.find_panel("P1_P1"), p1)
        self.assertEqual(group.find_panel("P2_P1"), p2)
        self.assertIsNone(group.find_panel("P_NON_EXISTING"))

        # Validação de grupo vazio
        with self.assertRaises(ValueError):
            PanelGroup(group_id="PG_EMPTY", panels=())

        # Validação de painel duplicado
        with self.assertRaises(ValueError):
            PanelGroup(group_id="PG_DUP", panels=(p1, p1))

    def test_group_panels_l_junction_direct_vs_indirect(self):
        from pymasondesign.drafting import FloorPlan

        # Caso 1: Encontro em L com amarração direta (DIRECT)
        w1_dir = Wall(
            wall_id="W1",
            axis=Axis(start=Point2D(0.0, 0.0), end=Point2D(4.0, 0.0)),
            thickness=0.14,
            end_bond=BondType.DIRECT,
        )
        w2_dir = Wall(
            wall_id="W2",
            axis=Axis(start=Point2D(4.0, 0.0), end=Point2D(4.0, 3.0)),
            thickness=0.14,
            start_bond=BondType.DIRECT,
        )
        plan_dir = FloorPlan(plan_id="PLAN_DIR", height=2.80, walls=(w1_dir, w2_dir))

        groups_dir = MasonryPanelService.group_panels_by_direct_bond(plan_dir)
        self.assertEqual(len(groups_dir), 1)
        self.assertEqual(len(groups_dir[0].panels), 2)
        self.assertAlmostEqual(groups_dir[0].total_length, 7.0)
        self.assertEqual(groups_dir[0].wall_ids, ("W1", "W2"))

        # Caso 2: Encontro em L com amarração indireta (INDIRECT)
        w1_ind = Wall(
            wall_id="W1",
            axis=Axis(start=Point2D(0.0, 0.0), end=Point2D(4.0, 0.0)),
            thickness=0.14,
            end_bond=BondType.INDIRECT,
        )
        w2_ind = Wall(
            wall_id="W2",
            axis=Axis(start=Point2D(4.0, 0.0), end=Point2D(4.0, 3.0)),
            thickness=0.14,
            start_bond=BondType.INDIRECT,
        )
        plan_ind = FloorPlan(plan_id="PLAN_IND", height=2.80, walls=(w1_ind, w2_ind))

        groups_ind = MasonryPanelService.group_panels_by_direct_bond(plan_ind)
        self.assertEqual(len(groups_ind), 2)
        self.assertEqual(len(groups_ind[0].panels), 1)
        self.assertEqual(len(groups_ind[1].panels), 1)

    def test_group_panels_t_junction_direct_vs_indirect(self):
        from pymasondesign.drafting import FloorPlan

        # Parede passante de 6m
        w_main = Wall(
            wall_id="W_MAIN",
            axis=Axis(start=Point2D(0.0, 0.0), end=Point2D(6.0, 0.0)),
            thickness=0.14,
        )

        # Parede que chega em (3,0) com DIRECT bond
        w_cross_dir = Wall(
            wall_id="W_CROSS",
            axis=Axis(start=Point2D(3.0, 0.0), end=Point2D(3.0, 4.0)),
            thickness=0.14,
            start_bond=BondType.DIRECT,
        )
        plan_t_dir = FloorPlan(plan_id="PLAN_T_DIR", height=2.80, walls=(w_main, w_cross_dir))

        groups_t_dir = MasonryPanelService.group_panels_by_direct_bond(plan_t_dir)
        # 1 grupo único com 3 painéis (2 da passante + 1 da chegando)
        self.assertEqual(len(groups_t_dir), 1)
        self.assertEqual(len(groups_t_dir[0].panels), 3)
        self.assertAlmostEqual(groups_t_dir[0].total_length, 10.0)

        # Parede que chega em (3,0) com INDIRECT bond
        w_cross_ind = Wall(
            wall_id="W_CROSS",
            axis=Axis(start=Point2D(3.0, 0.0), end=Point2D(3.0, 4.0)),
            thickness=0.14,
            start_bond=BondType.INDIRECT,
        )
        plan_t_ind = FloorPlan(plan_id="PLAN_T_IND", height=2.80, walls=(w_main, w_cross_ind))

        groups_t_ind = MasonryPanelService.group_panels_by_direct_bond(plan_t_ind)
        # 2 grupos: Grupo 1 com os 2 painéis da parede passante contínua, Grupo 2 com o painel da parede incidente
        self.assertEqual(len(groups_t_ind), 2)
        self.assertEqual(len(groups_t_ind[0].panels), 2)
        self.assertAlmostEqual(groups_t_ind[0].total_length, 6.0)
        self.assertEqual(len(groups_t_ind[1].panels), 1)
        self.assertAlmostEqual(groups_t_ind[1].total_length, 4.0)

    def test_group_panels_wall_with_opening_disconnects(self):
        from pymasondesign.drafting import FloorPlan

        # Parede de 6m com porta de 1m no meio -> 2 painéis desconectados por abertura
        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(6.0, 0.0))
        door = Opening.door(opening_id="D1", offset_along_wall=2.0, width=1.0, height=2.10)
        wall = Wall(wall_id="W1", axis=axis, thickness=0.14, openings=[door])
        plan = FloorPlan(plan_id="PLAN_DOOR", height=2.80, walls=(wall,))

        groups = MasonryPanelService.group_panels_by_direct_bond(plan)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0].panels), 1)
        self.assertEqual(len(groups[1].panels), 1)

    def test_floor_plan_model_creation_and_properties(self):
        p1 = MasonryPanel(
            panel_id="P1_P1",
            wall_id="P1",
            axis=Axis(Point2D(0, 0), Point2D(3, 0)),
            thickness=0.14,
            height=2.80,
        )
        p2 = MasonryPanel(
            panel_id="P2_P1",
            wall_id="P2",
            axis=Axis(Point2D(3, 0), Point2D(3, 4)),
            thickness=0.14,
            height=2.80,
        )
        p3 = MasonryPanel(
            panel_id="P3_P1",
            wall_id="P3",
            axis=Axis(Point2D(10, 0), Point2D(15, 0)),
            thickness=0.14,
            height=2.80,
        )

        g1 = PanelGroup(group_id="PG1", panels=(p1, p2))
        g2 = PanelGroup(group_id="PG2", panels=(p3,))

        model = FloorPlanModel(plan_id="PLAN_TIPO", height=2.80, groups=(g1, g2))

        self.assertEqual(model.plan_id, "PLAN_TIPO")
        self.assertAlmostEqual(model.height, 2.80)
        self.assertEqual(len(model.groups), 2)
        self.assertEqual(len(model.panels), 3)
        self.assertAlmostEqual(model.total_length, 12.0)  # 3 + 4 + 5 = 12
        self.assertEqual(model.wall_ids, ("P1", "P2", "P3"))

        # Consultas de busca
        self.assertIs(model.find_group("PG1"), g1)
        self.assertIs(model.find_group("PG2"), g2)
        self.assertIsNone(model.find_group("PG_UNKNOWN"))

        self.assertIs(model.find_panel("P1_P1"), p1)
        self.assertIs(model.find_panel("P3_P1"), p3)
        self.assertIsNone(model.find_panel("P_NONEXISTENT"))

        # Busca de grupos por parede
        self.assertEqual(model.find_groups_by_wall("P1"), (g1,))
        self.assertEqual(model.find_groups_by_wall("P2"), (g1,))
        self.assertEqual(model.find_groups_by_wall("P3"), (g2,))
        self.assertEqual(model.find_groups_by_wall("P_NONE"), ())

    def test_floor_plan_model_validations(self):
        p1 = MasonryPanel(
            panel_id="P1_P1",
            wall_id="P1",
            axis=Axis(Point2D(0, 0), Point2D(3, 0)),
            thickness=0.14,
            height=2.80,
        )
        g1 = PanelGroup(group_id="PG1", panels=(p1,))
        g1_dup = PanelGroup(group_id="PG1", panels=(p1,))

        # Altura <= 0 inválida
        with self.assertRaises(ValueError):
            FloorPlanModel(plan_id="PLAN_INV", height=0.0, groups=(g1,))

        # Grupos vazios inválidos
        with self.assertRaises(ValueError):
            FloorPlanModel(plan_id="PLAN_EMPTY", height=2.80, groups=())

        # ID de grupo duplicado
        with self.assertRaises(ValueError):
            FloorPlanModel(plan_id="PLAN_DUP", height=2.80, groups=(g1, g1_dup))

    def test_derive_floor_plan_model(self):
        from pymasondesign.drafting import FloorPlan

        # Planta com parede em L (amarração direta) e parede isolada
        w1 = Wall(
            wall_id="W1",
            axis=Axis(start=Point2D(0.0, 0.0), end=Point2D(5.0, 0.0)),
            thickness=0.14,
            end_bond=BondType.DIRECT,
        )
        w2 = Wall(
            wall_id="W2",
            axis=Axis(start=Point2D(5.0, 0.0), end=Point2D(5.0, 4.0)),
            thickness=0.14,
            start_bond=BondType.DIRECT,
        )
        w3 = Wall(
            wall_id="W3",
            axis=Axis(start=Point2D(10.0, 0.0), end=Point2D(14.0, 0.0)),
            thickness=0.14,
        )

        plan = FloorPlan(plan_id="PLAN_PAV_01", height=2.80, walls=(w1, w2, w3))

        model = MasonryPanelService.derive_floor_plan_model(plan)

        self.assertEqual(model.plan_id, "PLAN_PAV_01")
        self.assertAlmostEqual(model.height, 2.80)
        self.assertEqual(len(model.groups), 2)  # PG1 (W1 + W2) e PG2 (W3)
        self.assertEqual(len(model.panels), 3)
        self.assertAlmostEqual(model.total_length, 13.0)  # 5 + 4 + 4 = 13.0
        self.assertIn("W1", model.wall_ids)
        self.assertIn("W2", model.wall_ids)
        self.assertIn("W3", model.wall_ids)

    def test_story_model_attributes_and_validations(self):
        mat = NBR16868MasonryFactory.create(10.0)
        story = StoryModel(
            story_id="PAV_01",
            elevation=3.0,
            story_height=3.0,
            masonry_spec=mat,
            plan_id="PLAN_TIPO",
        )

        self.assertEqual(story.story_id, "PAV_01")
        self.assertAlmostEqual(story.elevation, 3.0)
        self.assertAlmostEqual(story.story_height, 3.0)
        self.assertIs(story.masonry_spec, mat)
        self.assertEqual(story.plan_id, "PLAN_TIPO")

        # Altura <= 0 inválida
        with self.assertRaises(ValueError):
            StoryModel(
                story_id="PAV_INV",
                elevation=0.0,
                story_height=0.0,
                masonry_spec=mat,
                plan_id="PLAN_TIPO",
            )

    def test_building_model_creation_and_properties(self):
        mat = NBR16868MasonryFactory.create(10.0)
        p1 = MasonryPanel("P1_P1", "P1", Axis(Point2D(0, 0), Point2D(5, 0)), 0.14, 2.80)
        g1 = PanelGroup("PG1", panels=(p1,))
        fpm1 = FloorPlanModel("PLAN_TIPO", 2.80, groups=(g1,))

        p2 = MasonryPanel("P2_P1", "P2", Axis(Point2D(0, 0), Point2D(8, 0)), 0.19, 3.00)
        g2 = PanelGroup("PG1", panels=(p2,))
        fpm2 = FloorPlanModel("PLAN_TERREO", 3.00, groups=(g2,))

        # Pavimentos em ordem estrita de cima para baixo: COB (9.0), PAV_02 (6.0), PAV_01 (3.0), TERREO (0.0)
        st_cob = StoryModel("COBERTURA", elevation=9.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        st_p2 = StoryModel("PAV_02", elevation=6.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        st_p1 = StoryModel("PAV_01", elevation=3.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        st_ter = StoryModel("TERREO", elevation=0.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TERREO")

        building = BuildingModel(
            building_id="EDIF_AURORA",
            floor_plan_models=(fpm1, fpm2),
            stories=(st_cob, st_p2, st_p1, st_ter),
        )

        self.assertEqual(building.building_id, "EDIF_AURORA")
        self.assertEqual(building.num_stories, 4)
        self.assertEqual(building.top_story.story_id, "COBERTURA")
        self.assertEqual(building.bottom_story.story_id, "TERREO")
        # Altura total: (9.0 + 3.0) - 0.0 = 12.0
        self.assertAlmostEqual(building.total_height, 12.0)

        # Consultas de catálogo e pavimentos
        self.assertIs(building.get_floor_plan_model("PLAN_TIPO"), fpm1)
        self.assertIs(building.get_floor_plan_model("PLAN_TERREO"), fpm2)
        self.assertIsNone(building.get_floor_plan_model("PLAN_UNKNOWN"))

        self.assertIs(building.find_story("PAV_02"), st_p2)
        self.assertIsNone(building.find_story("PAV_UNKNOWN"))

        # Busca de pavimentos por planta
        stories_tipo = building.find_stories_by_plan("PLAN_TIPO")
        self.assertEqual(len(stories_tipo), 3)
        self.assertEqual([s.story_id for s in stories_tipo], ["COBERTURA", "PAV_02", "PAV_01"])

        stories_terreo = building.find_stories_by_plan("PLAN_TERREO")
        self.assertEqual(len(stories_terreo), 1)
        self.assertEqual(stories_terreo[0].story_id, "TERREO")

        # get_story_plan_model
        self.assertIs(building.get_story_plan_model(st_p1), fpm1)
        self.assertIs(building.get_story_plan_model("TERREO"), fpm2)
        with self.assertRaises(KeyError):
            building.get_story_plan_model("NONEXISTENT_STORY")

    def test_building_model_validations(self):
        mat = NBR16868MasonryFactory.create(10.0)
        p1 = MasonryPanel("P1_P1", "P1", Axis(Point2D(0, 0), Point2D(5, 0)), 0.14, 2.80)
        g1 = PanelGroup("PG1", panels=(p1,))
        fpm1 = FloorPlanModel("PLAN_TIPO", 2.80, groups=(g1,))
        fpm1_dup = FloorPlanModel("PLAN_TIPO", 2.80, groups=(g1,))

        st_p2 = StoryModel("PAV_02", elevation=6.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        st_p1 = StoryModel("PAV_01", elevation=3.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        st_p1_dup = StoryModel("PAV_01", elevation=0.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")

        # 1. Sem pavimentos
        with self.assertRaises(ValueError):
            BuildingModel("EDIF_EMPTY", floor_plan_models=(fpm1,), stories=())

        # 2. Sem modelos de planta no catálogo
        with self.assertRaises(ValueError):
            BuildingModel("EDIF_NO_CATALOG", floor_plan_models=(), stories=(st_p1,))

        # 3. ID de pavimento duplicado
        with self.assertRaises(ValueError):
            BuildingModel("EDIF_DUP_STORY", floor_plan_models=(fpm1,), stories=(st_p1, st_p1_dup))

        # 4. ID de planta duplicado no catálogo
        with self.assertRaises(ValueError):
            BuildingModel("EDIF_DUP_CATALOG", floor_plan_models=(fpm1, fpm1_dup), stories=(st_p1,))

        # 5. Integridade referencial: story referencia planta inexistente
        st_missing_plan = StoryModel(
            "PAV_01", elevation=3.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_NONEXISTENT"
        )
        with self.assertRaises(ValueError):
            BuildingModel("EDIF_REF_ERR", floor_plan_models=(fpm1,), stories=(st_missing_plan,))

        # 6. Ordenação inválida: de baixo para cima (Z crescente)
        with self.assertRaises(ValueError):
            BuildingModel("EDIF_BOTTOM_UP", floor_plan_models=(fpm1,), stories=(st_p1, st_p2))

        # 7. Mesma cota Z em pavimentos distintos
        st_p1_same_z = StoryModel("PAV_01B", elevation=3.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        with self.assertRaises(ValueError):
            BuildingModel("EDIF_SAME_Z", floor_plan_models=(fpm1,), stories=(st_p1, st_p1_same_z))

    def test_derive_building_model(self):
        mat = NBR16868MasonryFactory.create(12.0)

        # Plantas de lançamento
        w_tipo = Wall("W_TIPO", Axis(Point2D(0, 0), Point2D(6, 0)), 0.14)
        plan_tipo = FloorPlan("PLAN_TIPO", 2.80, walls=(w_tipo,))

        w_ter = Wall("W_TER", Axis(Point2D(0, 0), Point2D(8, 0)), 0.19)
        plan_ter = FloorPlan("PLAN_TERREO", 3.00, walls=(w_ter,))

        # Stories com plan_id em ordem top-to-bottom
        s4 = Story("COBERTURA", elevation=9.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        s3 = Story("PAV_02", elevation=6.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        s2 = Story("PAV_01", elevation=3.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TIPO")
        s1 = Story("TERREO", elevation=0.0, story_height=3.0, masonry_spec=mat, plan_id="PLAN_TERREO")

        drafting_building = Building(
            building_id="EDIF_DERIVE",
            floor_plans=(plan_tipo, plan_ter),
            stories=(s4, s3, s2, s1),
        )

        building_model = MasonryPanelService.derive_building_model(drafting_building)

        self.assertEqual(building_model.building_id, "EDIF_DERIVE")
        self.assertEqual(building_model.num_stories, 4)
        # Ordenado top-to-bottom
        self.assertEqual([s.story_id for s in building_model.stories], ["COBERTURA", "PAV_02", "PAV_01", "TERREO"])
        self.assertEqual([s.elevation for s in building_model.stories], [9.0, 6.0, 3.0, 0.0])
        # Catálogo tem apenas 2 plantas discretizadas distintas
        self.assertEqual(len(building_model.floor_plan_models), 2)
        self.assertIsNotNone(building_model.get_floor_plan_model("PLAN_TIPO"))
        self.assertIsNotNone(building_model.get_floor_plan_model("PLAN_TERREO"))
        self.assertAlmostEqual(building_model.total_height, 12.0)


if __name__ == "__main__":
    unittest.main()

