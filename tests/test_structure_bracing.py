from __future__ import annotations

import unittest
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.transform import Transform2D
from pymasondesign.geometry.tolerances import is_close
from pymasondesign.structure.enums import SegmentRole
from pymasondesign.structure.panel import MasonryPanel
from pymasondesign.structure.group import PanelGroup
from pymasondesign.structure.floor_plan_model import FloorPlanModel
from pymasondesign.structure.bracing_segment import (
    BracingSegment,
    create_rectangle_polygon,
)
from pymasondesign.structure.bracing_wall import BracingWall
from pymasondesign.structure.bracing_service import (
    BracingOptions,
    BracingWallService,
)


class TestBracingSegment(unittest.TestCase):
    """Testes unitários para BracingSegment e geração de polígonos."""

    def setUp(self) -> None:
        self.axis_loc = Axis(Point2D(0.0, 0.0), Point2D(100.0, 0.0))
        self.axis_glob = Axis(Point2D(10.0, 20.0), Point2D(110.0, 20.0))

    def test_valid_creation(self) -> None:
        seg = BracingSegment(
            segment_id="SEG_1",
            source_panel_id="P1",
            role=SegmentRole.WEB,
            local_axis=self.axis_loc,
            global_axis=self.axis_glob,
            thickness=14.0,
            height=280.0,
        )
        self.assertEqual(seg.segment_id, "SEG_1")
        self.assertEqual(seg.source_panel_id, "P1")
        self.assertEqual(seg.role, SegmentRole.WEB)
        self.assertTrue(seg.is_web)
        self.assertFalse(seg.is_flange)
        self.assertTrue(is_close(seg.length, 100.0))
        self.assertTrue(is_close(seg.area, 1400.0))

    def test_invalid_thickness_and_height(self) -> None:
        with self.assertRaises(ValueError):
            BracingSegment(
                segment_id="SEG_1",
                source_panel_id="P1",
                role=SegmentRole.WEB,
                local_axis=self.axis_loc,
                global_axis=self.axis_glob,
                thickness=0.0,
                height=280.0,
            )
        with self.assertRaises(ValueError):
            BracingSegment(
                segment_id="SEG_1",
                source_panel_id="P1",
                role=SegmentRole.WEB,
                local_axis=self.axis_loc,
                global_axis=self.axis_glob,
                thickness=14.0,
                height=-10.0,
            )

    def test_polygons_generation(self) -> None:
        seg = BracingSegment(
            segment_id="SEG_1",
            source_panel_id="P1",
            role=SegmentRole.WEB,
            local_axis=self.axis_loc,
            global_axis=self.axis_glob,
            thickness=14.0,
            height=280.0,
        )
        poly_loc = seg.local_polygon()
        poly_glob = seg.global_polygon()
        self.assertEqual(len(poly_loc.vertices), 4)
        self.assertEqual(len(poly_glob.vertices), 4)
        self.assertTrue(is_close(poly_loc.area, 1400.0))
        self.assertTrue(is_close(poly_glob.area, 1400.0))

    def test_touches(self) -> None:
        seg1 = BracingSegment(
            segment_id="S1",
            source_panel_id="P1",
            role=SegmentRole.WEB,
            local_axis=Axis(Point2D(0.0, 0.0), Point2D(100.0, 0.0)),
            global_axis=Axis(Point2D(0.0, 0.0), Point2D(100.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        seg2 = BracingSegment(
            segment_id="S2",
            source_panel_id="P2",
            role=SegmentRole.FLANGE,
            local_axis=Axis(Point2D(100.0, 0.0), Point2D(100.0, 80.0)),
            global_axis=Axis(Point2D(100.0, 0.0), Point2D(100.0, 80.0)),
            thickness=14.0,
            height=280.0,
        )
        seg3 = BracingSegment(
            segment_id="S3",
            source_panel_id="P3",
            role=SegmentRole.WEB,
            local_axis=Axis(Point2D(200.0, 0.0), Point2D(300.0, 0.0)),
            global_axis=Axis(Point2D(200.0, 0.0), Point2D(300.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        self.assertTrue(seg1.touches(seg2))
        self.assertFalse(seg1.touches(seg3))


class TestBracingWall(unittest.TestCase):
    """Testes unitários para o modelo estrutural BracingWall."""

    def setUp(self) -> None:
        self.seg1 = BracingSegment(
            segment_id="S1",
            source_panel_id="P1",
            role=SegmentRole.WEB,
            local_axis=Axis(Point2D(-50.0, 0.0), Point2D(50.0, 0.0)),
            global_axis=Axis(Point2D(0.0, 0.0), Point2D(100.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        self.seg2 = BracingSegment(
            segment_id="S2",
            source_panel_id="P2",
            role=SegmentRole.FLANGE,
            local_axis=Axis(Point2D(50.0, 7.0), Point2D(50.0, 87.0)),
            global_axis=Axis(Point2D(100.0, 7.0), Point2D(100.0, 87.0)),
            thickness=14.0,
            height=280.0,
        )
        self.t2d = Transform2D(origin=Point2D(50.0, 0.0), u_axis=Vector2D(1.0, 0.0), v_axis=Vector2D(0.0, 1.0))

    def test_valid_creation_and_properties(self) -> None:
        wall = BracingWall(
            wall_id="BW_1",
            group_id="PG1",
            direction=Vector2D(1.0, 0.0),
            segments=(self.seg1, self.seg2),
            height=280.0,
            local_to_global=self.t2d,
        )
        self.assertEqual(wall.wall_id, "BW_1")
        self.assertEqual(wall.group_id, "PG1")
        self.assertEqual(wall.num_webs, 1)
        self.assertEqual(wall.num_flanges, 1)
        self.assertEqual(wall.web_panel_ids, ("P1",))
        self.assertEqual(wall.flange_panel_ids, ("P2",))
        self.assertTrue(is_close(wall.total_length, 180.0))
        self.assertTrue(is_close(wall.total_area, 100.0 * 14.0 + 80.0 * 14.0))

        # find_segment
        self.assertEqual(wall.find_segment("S1"), self.seg1)
        self.assertEqual(wall.find_segment("S2"), self.seg2)
        self.assertIsNone(wall.find_segment("NON_EXISTING"))

    def test_invalid_attributes(self) -> None:
        with self.assertRaises(ValueError):
            BracingWall(
                wall_id="BW_1",
                group_id="PG1",
                direction=Vector2D(1.0, 0.0),
                segments=(self.seg1,),
                height=-10.0,
                local_to_global=self.t2d,
            )
        with self.assertRaises(ValueError):
            BracingWall(
                wall_id="BW_1",
                group_id="PG1",
                direction=Vector2D(1.0, 0.0),
                segments=(),
                height=280.0,
                local_to_global=self.t2d,
            )
        # Duplicate segment ID
        with self.assertRaises(ValueError):
            BracingWall(
                wall_id="BW_1",
                group_id="PG1",
                direction=Vector2D(1.0, 0.0),
                segments=(self.seg1, self.seg1),
                height=280.0,
                local_to_global=self.t2d,
            )


class TestBracingOptions(unittest.TestCase):
    """Testes de validação de BracingOptions."""

    def test_valid_options(self) -> None:
        opts = BracingOptions()
        self.assertEqual(opts.flange_multiplier, 6.0)
        self.assertIsNone(opts.custom_width)

        opts2 = BracingOptions(flange_multiplier=8.0, custom_width=50.0)
        self.assertEqual(opts2.flange_multiplier, 8.0)
        self.assertEqual(opts2.custom_width, 50.0)

    def test_invalid_options(self) -> None:
        with self.assertRaises(ValueError):
            BracingOptions(flange_multiplier=0.0)
        with self.assertRaises(ValueError):
            BracingOptions(custom_width=-5.0)


class TestBracingWallService(unittest.TestCase):
    """Testes de integração do serviço BracingWallService para derivação de paredes de contraventamento."""

    def test_isolated_panel_wall(self) -> None:
        # Painel horizontal isolado (em X)
        p1 = MasonryPanel(
            panel_id="P1",
            wall_id="W1",
            axis=Axis(Point2D(0.0, 0.0), Point2D(300.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        group = PanelGroup(group_id="PG1", panels=(p1,))

        # Derivação em X
        walls_x = BracingWallService.derive_for_group(group, Vector2D(1.0, 0.0))
        self.assertEqual(len(walls_x), 1)
        wall_x = walls_x[0]
        self.assertEqual(wall_x.wall_id, "BW_PG1_X_01")
        self.assertEqual(wall_x.num_webs, 1)
        self.assertEqual(wall_x.num_flanges, 0)
        self.assertTrue(is_close(wall_x.total_length, 300.0))
        self.assertTrue(is_close(wall_x.total_area, 300.0 * 14.0))

        # Derivação em Y (não há almas em Y)
        walls_y = BracingWallService.derive_for_group(group, Vector2D(0.0, 1.0))
        self.assertEqual(len(walls_y), 0)

    def test_l_shaped_wall(self) -> None:
        # Encontro em L: Painel 1 em X (L=200, t=14) e Painel 2 em Y (L=150, t=14) conectado no ponto (200, 0)
        p1 = MasonryPanel(
            panel_id="P1",
            wall_id="W1",
            axis=Axis(Point2D(0.0, 0.0), Point2D(200.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        p2 = MasonryPanel(
            panel_id="P2",
            wall_id="W2",
            axis=Axis(Point2D(200.0, 0.0), Point2D(200.0, 150.0)),
            thickness=14.0,
            height=280.0,
        )
        group = PanelGroup(group_id="PG_L", panels=(p1, p2))

        # Derivação para a direção X: P1 é alma, P2 é aba colaborante
        walls_x = BracingWallService.derive_for_group(group, Vector2D(1.0, 0.0))
        self.assertEqual(len(walls_x), 1)
        wall_x = walls_x[0]
        self.assertEqual(wall_x.num_webs, 1)
        self.assertEqual(wall_x.num_flanges, 1)

        # Alma: L = 200, t = 14
        web = wall_x.webs[0]
        self.assertEqual(web.source_panel_id, "P1")
        self.assertTrue(is_close(web.length, 200.0))

        # Flange: b_f = min(150 - 7, 6 * 14) = min(143, 84) = 84.0
        flange = wall_x.flanges[0]
        self.assertEqual(flange.source_panel_id, "P2")
        self.assertTrue(is_close(flange.length, 84.0))
        self.assertTrue(is_close(wall_x.total_length, 200.0 + 84.0))

    def test_t_shaped_wall(self) -> None:
        # Encontro em T: Alma em X (P1 de (0,0) a (300,0)) e duas abas em Y conectadas em (300,0):
        # P2 para cima (0 a +100) e P3 para baixo (0 a -100)
        p1 = MasonryPanel(
            panel_id="P1",
            wall_id="W1",
            axis=Axis(Point2D(0.0, 0.0), Point2D(300.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        p2 = MasonryPanel(
            panel_id="P2",
            wall_id="W2",
            axis=Axis(Point2D(300.0, 0.0), Point2D(300.0, 100.0)),
            thickness=14.0,
            height=280.0,
        )
        p3 = MasonryPanel(
            panel_id="P3",
            wall_id="W3",
            axis=Axis(Point2D(300.0, 0.0), Point2D(300.0, -100.0)),
            thickness=14.0,
            height=280.0,
        )
        group = PanelGroup(group_id="PG_T", panels=(p1, p2, p3))

        walls_x = BracingWallService.derive_for_group(group, Vector2D(1.0, 0.0))
        self.assertEqual(len(walls_x), 1)
        wall = walls_x[0]
        self.assertEqual(wall.num_webs, 1)
        self.assertEqual(wall.num_flanges, 2)
        for f in wall.flanges:
            self.assertTrue(is_close(f.length, 84.0))

    def test_u_coupled_vs_decoupled_walls(self) -> None:
        # Duas almas paralelas em X: P1 (Y=0, L=200) e P2 (Y=100, L=200)
        # Painel transversal P3 conectando (0,0) a (0,100), L=100.
        # Como 100 < 6*14 + 6*14 = 168, as duas almas são acopladas em 1 única BracingWall.
        p1 = MasonryPanel(
            panel_id="P1",
            wall_id="W1",
            axis=Axis(Point2D(0.0, 0.0), Point2D(200.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        p2 = MasonryPanel(
            panel_id="P2",
            wall_id="W2",
            axis=Axis(Point2D(0.0, 100.0), Point2D(200.0, 100.0)),
            thickness=14.0,
            height=280.0,
        )
        p3_short = MasonryPanel(
            panel_id="P3",
            wall_id="W3",
            axis=Axis(Point2D(0.0, 0.0), Point2D(0.0, 100.0)),
            thickness=14.0,
            height=280.0,
        )
        group_coupled = PanelGroup(group_id="PG_U1", panels=(p1, p2, p3_short))
        walls_coupled = BracingWallService.derive_for_group(group_coupled, Vector2D(1.0, 0.0))
        self.assertEqual(len(walls_coupled), 1)
        self.assertEqual(walls_coupled[0].num_webs, 2)

        # Se o painel transversal for longo (L=250 > 168), as almas desacoplam em 2 BracingWalls
        p3_long = MasonryPanel(
            panel_id="P3",
            wall_id="W3",
            axis=Axis(Point2D(0.0, 0.0), Point2D(0.0, 250.0)),
            thickness=14.0,
            height=280.0,
        )
        p2_far = MasonryPanel(
            panel_id="P2",
            wall_id="W2",
            axis=Axis(Point2D(0.0, 250.0), Point2D(200.0, 250.0)),
            thickness=14.0,
            height=280.0,
        )
        group_decoupled = PanelGroup(group_id="PG_U2", panels=(p1, p2_far, p3_long))
        walls_decoupled = BracingWallService.derive_for_group(group_decoupled, Vector2D(1.0, 0.0))
        self.assertEqual(len(walls_decoupled), 2)
        self.assertEqual(walls_decoupled[0].num_webs, 1)
        self.assertEqual(walls_decoupled[1].num_webs, 1)

    def test_derive_for_floor_plan(self) -> None:
        p1 = MasonryPanel(
            panel_id="P1",
            wall_id="W1",
            axis=Axis(Point2D(0.0, 0.0), Point2D(200.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        p2 = MasonryPanel(
            panel_id="P2",
            wall_id="W2",
            axis=Axis(Point2D(500.0, 0.0), Point2D(700.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        g1 = PanelGroup(group_id="PG1", panels=(p1,))
        g2 = PanelGroup(group_id="PG2", panels=(p2,))
        plan_model = FloorPlanModel(plan_id="PLAN_1", height=280.0, groups=(g1, g2))

        walls = BracingWallService.derive_for_floor_plan(plan_model, Vector2D(1.0, 0.0))
        self.assertEqual(len(walls), 2)
        self.assertEqual(walls[0].group_id, "PG1")
        self.assertEqual(walls[1].group_id, "PG2")

    def test_custom_width_option(self) -> None:
        p1 = MasonryPanel(
            panel_id="P1",
            wall_id="W1",
            axis=Axis(Point2D(0.0, 0.0), Point2D(200.0, 0.0)),
            thickness=14.0,
            height=280.0,
        )
        p2 = MasonryPanel(
            panel_id="P2",
            wall_id="W2",
            axis=Axis(Point2D(200.0, 0.0), Point2D(200.0, 150.0)),
            thickness=14.0,
            height=280.0,
        )
        group = PanelGroup(group_id="PG_L", panels=(p1, p2))

        # Usando custom_width = 40.0 cm
        opts = BracingOptions(custom_width=40.0)
        walls = BracingWallService.derive_for_group(group, Vector2D(1.0, 0.0), options=opts)
        self.assertEqual(len(walls), 1)
        flange = walls[0].flanges[0]
        self.assertTrue(is_close(flange.length, 40.0))


if __name__ == "__main__":
    unittest.main()
