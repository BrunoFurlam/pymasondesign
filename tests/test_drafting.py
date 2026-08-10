from __future__ import annotations

import unittest
from pymasondesign.geometry import Point2D, Vector2D, Transform2D, Axis, AxisRelation
from pymasondesign.materials import MasonrySpecification
from pymasondesign.drafting import (
    OpeningType,
    BondType,
    WallEnd,
    Opening,
    Wall,
    PassingWall,
    ArrivingWall,
    Junction,
    FloorPlan,
    Story,
    Building,
)


class TestDrafting(unittest.TestCase):
    def test_point2d_methods(self):
        p1 = Point2D(10.0, 20.0)
        p2 = Point2D(10.0, 20.0)
        p3 = Point2D(10.000001, 20.000001)
        p4 = Point2D(15.0, 30.0)

        self.assertTrue(p1.is_same(p2))
        self.assertTrue(p1.is_same(p3, tolerance=1e-4))
        self.assertFalse(p1.is_same(p3, tolerance=1e-9))
        self.assertFalse(p1.is_same(p4))

    def test_axis_properties_and_transformations(self):
        p1 = Point2D(0.0, 0.0)
        p2 = Point2D(4.0, 3.0)
        axis = Axis(start=p1, end=p2)

        self.assertAlmostEqual(axis.length, 5.0)
        self.assertAlmostEqual(axis.dx, 4.0)
        self.assertAlmostEqual(axis.dy, 3.0)
        self.assertAlmostEqual(axis.direction.x, 4.0 / 5.0)
        self.assertAlmostEqual(axis.direction.y, 3.0 / 5.0)
        self.assertAlmostEqual(axis.normal.x, -3.0 / 5.0)
        self.assertAlmostEqual(axis.normal.y, 4.0 / 5.0)
        self.assertEqual(axis.midpoint, Point2D(2.0, 1.5))

        # point_at
        self.assertEqual(axis.point_at(0.0), p1)
        self.assertEqual(axis.point_at(5.0), p2)
        self.assertEqual(axis.point_at(2.5), Point2D(2.0, 1.5))

        # projected_offset
        self.assertAlmostEqual(axis.projected_offset(p1), 0.0)
        self.assertAlmostEqual(axis.projected_offset(p2), 5.0)
        self.assertAlmostEqual(axis.projected_offset(Point2D(2.0, 1.5)), 2.5)
        # Ponto fora do eixo mas projetado no meio (ex.: deslocado perpendicularmente por normal)
        self.assertAlmostEqual(axis.projected_offset(Point2D(2.0 - 3.0, 1.5 + 4.0)), 2.5)

        # distance_to_point
        self.assertAlmostEqual(axis.distance_to_point(p1), 0.0)
        self.assertAlmostEqual(axis.distance_to_point(p2), 0.0)
        self.assertAlmostEqual(axis.distance_to_point(Point2D(2.0, 1.5)), 0.0)
        # Ponto perpendicular a 5.0 unidades do meio (2.0, 1.5) com normal n = (-0.6, 0.8)
        self.assertAlmostEqual(axis.distance_to_point(Point2D(2.0 - 3.0, 1.5 + 4.0)), 5.0)
        # Ponto antes de start (-3.0, -4.0) a 5.0 unidades de p1(0, 0)
        self.assertAlmostEqual(axis.distance_to_point(Point2D(-3.0, -4.0)), 5.0)
        # Ponto além de end (7.0, 7.0) a 5.0 unidades de p2(4, 3)
        self.assertAlmostEqual(axis.distance_to_point(Point2D(7.0, 7.0)), 5.0)

        # reversed
        rev = axis.reversed()
        self.assertEqual(rev.start, p2)
        self.assertEqual(rev.end, p1)

        # translated
        trans = axis.translated(Vector2D(10.0, 20.0))
        self.assertEqual(trans.start, Point2D(10.0, 20.0))
        self.assertEqual(trans.end, Point2D(14.0, 23.0))

        # transformed
        t = Transform2D.translation(1.0, 1.0)
        transformed_axis = axis.transformed(t)
        self.assertEqual(transformed_axis.start, Point2D(1.0, 1.0))
        self.assertEqual(transformed_axis.end, Point2D(5.0, 4.0))

        # Zero length validation
        with self.assertRaises(ValueError):
            Axis(start=p1, end=p1)

    def test_axis_intersections_and_relations(self):
        # 1. Cruzamento no interior (POINT_INTERSECT)
        a1 = Axis(start=Point2D(0.0, 0.0), end=Point2D(10.0, 0.0))
        a2 = Axis(start=Point2D(5.0, -5.0), end=Point2D(5.0, 5.0))

        res1 = a1.intersect(a2)
        self.assertEqual(res1.relation, AxisRelation.POINT_INTERSECT)
        self.assertIsNotNone(res1.point)
        self.assertAlmostEqual(res1.point.x, 5.0)
        self.assertAlmostEqual(res1.point.y, 0.0)
        self.assertTrue(a1.intersects(a2))
        self.assertFalse(a1.overlaps(a2))

        # 2. Encontro em L / T em vértice (TOUCHING_VERTEX)
        a_t1 = Axis(start=Point2D(0.0, 0.0), end=Point2D(5.0, 0.0))
        a_t2 = Axis(start=Point2D(5.0, 0.0), end=Point2D(5.0, 5.0))
        res_t = a_t1.intersect(a_t2)
        self.assertEqual(res_t.relation, AxisRelation.TOUCHING_VERTEX)
        self.assertEqual(res_t.point, Point2D(5.0, 0.0))
        self.assertTrue(a_t1.intersects(a_t2))

        # 3. Paralelos disjuntos
        a_p1 = Axis(start=Point2D(0.0, 0.0), end=Point2D(10.0, 0.0))
        a_p2 = Axis(start=Point2D(0.0, 2.0), end=Point2D(10.0, 2.0))
        self.assertTrue(a_p1.is_parallel(a_p2))
        self.assertFalse(a_p1.is_collinear(a_p2))
        res_p = a_p1.intersect(a_p2)
        self.assertEqual(res_p.relation, AxisRelation.DISJOINT)
        self.assertFalse(a_p1.intersects(a_p2))

        # 4. Colineares sobrepostos (OVERLAPPING)
        a_o1 = Axis(start=Point2D(0.0, 0.0), end=Point2D(10.0, 0.0))
        a_o2 = Axis(start=Point2D(4.0, 0.0), end=Point2D(14.0, 0.0))
        self.assertTrue(a_o1.is_collinear(a_o2))
        self.assertTrue(a_o1.overlaps(a_o2))
        res_o = a_o1.intersect(a_o2)
        self.assertEqual(res_o.relation, AxisRelation.OVERLAPPING)
        self.assertIsNotNone(res_o.overlap_segment)
        self.assertEqual(res_o.overlap_segment.start, Point2D(4.0, 0.0))
        self.assertEqual(res_o.overlap_segment.end, Point2D(10.0, 0.0))

        # 5. Colineares tocando-se no extremo
        a_c1 = Axis(start=Point2D(0.0, 0.0), end=Point2D(5.0, 0.0))
        a_c2 = Axis(start=Point2D(5.0, 0.0), end=Point2D(10.0, 0.0))
        self.assertTrue(a_c1.is_collinear(a_c2))
        res_c = a_c1.intersect(a_c2)
        self.assertEqual(res_c.relation, AxisRelation.TOUCHING_VERTEX)
        self.assertEqual(res_c.point, Point2D(5.0, 0.0))

        # 6. Colineares disjuntos (sem contato)
        a_d1 = Axis(start=Point2D(0.0, 0.0), end=Point2D(5.0, 0.0))
        a_d2 = Axis(start=Point2D(7.0, 0.0), end=Point2D(12.0, 0.0))
        self.assertTrue(a_d1.is_collinear(a_d2))
        res_d = a_d1.intersect(a_d2)
        self.assertEqual(res_d.relation, AxisRelation.DISJOINT)

    def test_opening_and_wall(self):
        door = Opening.door(opening_id="P1", offset_along_wall=1.0, width=0.90, height=2.10)
        self.assertEqual(door.opening_type, OpeningType.DOOR)
        self.assertAlmostEqual(door.sill_height, 0.0)

        window = Opening.window(opening_id="J1", offset_along_wall=3.0, width=1.50, height=1.20, sill_height=1.00)
        self.assertEqual(window.opening_type, OpeningType.WINDOW)
        self.assertAlmostEqual(window.sill_height, 1.00)

        axis = Axis(start=Point2D(0.0, 0.0), end=Point2D(6.0, 0.0))
        wall = Wall(
            wall_id="W1",
            axis=axis,
            thickness=0.14,
            openings=(door, window),
        )

        self.assertEqual(wall.wall_id, "W1")
        self.assertAlmostEqual(wall.length, 6.0)
        self.assertEqual(len(wall.openings), 2)

        # Métodos fluentes de adição de aberturas
        empty_wall = Wall(wall_id="W2", axis=axis, thickness=0.14)
        self.assertEqual(len(empty_wall.openings), 0)

        wall_with_door = empty_wall.add_door(opening_id="P1", offset_along_wall=1.0, width=0.9, height=2.1)
        self.assertEqual(len(wall_with_door.openings), 1)

        wall_with_both = wall_with_door.add_window(opening_id="J1", offset_along_wall=3.0, width=1.5, height=1.2, sill_height=1.0)
        self.assertEqual(len(wall_with_both.openings), 2)
        self.assertEqual(wall_with_both.openings[1].opening_type, OpeningType.WINDOW)

        # Validação: abertura excedendo comprimento da parede
        with self.assertRaises(ValueError):
            Wall(
                wall_id="W_ERR",
                axis=axis,
                thickness=0.14,
                openings=(Opening.door(opening_id="P_ERR", offset_along_wall=5.5, width=1.0, height=2.1),),
            )

        # Validação: aberturas sobrepostas
        with self.assertRaises(ValueError):
            Wall(
                wall_id="W_ERR2",
                axis=axis,
                thickness=0.14,
                openings=(
                    Opening.door(opening_id="P1", offset_along_wall=1.0, width=1.0, height=2.1),
                    Opening.window(opening_id="J1", offset_along_wall=1.5, width=1.0, height=1.2, sill_height=1.0),
                ),
            )

    def test_floor_plan_and_story(self):
        w1 = Wall(
            wall_id="P1",
            axis=Axis(start=Point2D(0.0, 0.0), end=Point2D(5.0, 0.0)),
            thickness=0.14,
        )
        w2 = Wall(
            wall_id="P2",
            axis=Axis(start=Point2D(5.0, 0.0), end=Point2D(5.0, 4.0)),
            thickness=0.14,
        )

        floor_plan = FloorPlan(plan_id="PLAN_TIPO", height=2.80, walls=(w1, w2))
        self.assertEqual(floor_plan.plan_id, "PLAN_TIPO")
        self.assertAlmostEqual(floor_plan.height, 2.80)
        self.assertAlmostEqual(floor_plan.total_wall_length, 9.0)
        self.assertEqual(floor_plan.find_wall("P1"), w1)
        self.assertEqual(floor_plan.find_wall("P2"), w2)
        self.assertIsNone(floor_plan.find_wall("P99"))

        # Adicionar porta e janela via FloorPlan
        plan_with_door = floor_plan.add_door(wall_id="P1", opening_id="P_P1", offset_along_wall=1.0, width=0.9, height=2.1)
        self.assertEqual(len(plan_with_door.find_wall("P1").openings), 1)
        self.assertEqual(len(plan_with_door.find_wall("P2").openings), 0)

        plan_with_both = plan_with_door.add_window(wall_id="P2", opening_id="J_P2", offset_along_wall=1.0, width=1.2, height=1.2, sill_height=1.0)
        # Testar add_wall
        w3 = Wall(wall_id="P3", axis=Axis(Point2D(0, 4), Point2D(5, 4)), thickness=0.14)
        plan_expanded = floor_plan.add_wall(w3)
        self.assertEqual(len(plan_expanded.walls), 3)
        self.assertEqual(plan_expanded.find_wall("P3"), w3)

        # Adicionar em parede inexistente
        with self.assertRaises(KeyError):
            floor_plan.add_door(wall_id="P_NAO_EXISTE", opening_id="P", offset_along_wall=0, width=1, height=2)

        # Validação: IDs duplicados de paredes na planta
        with self.assertRaises(ValueError):
            FloorPlan(plan_id="PLAN_ERR", height=2.80, walls=(w1, w1))

        # Story referenciando a planta por ID
        masonry = MasonrySpecification.from_nbr16868(fbk=14.0)

        story1 = Story(
            story_id="PAV_01",
            elevation=0.0,
            story_height=3.00,
            masonry_spec=masonry,
            plan_id="PLAN_TIPO",
        )

        story2 = Story(
            story_id="PAV_02",
            elevation=3.00,
            story_height=3.00,
            masonry_spec=masonry,
            plan_id="PLAN_TIPO",
        )

        self.assertEqual(story1.story_id, "PAV_01")
        self.assertEqual(story1.plan_id, "PLAN_TIPO")
        self.assertAlmostEqual(story1.elevation, 0.0)
        self.assertAlmostEqual(story1.story_height, 3.00)
        self.assertEqual(story2.story_id, "PAV_02")
        self.assertEqual(story2.plan_id, "PLAN_TIPO")

        # Validação de story_height <= 0
        with self.assertRaises(ValueError):
            Story(story_id="ERR", elevation=0.0, story_height=0.0, masonry_spec=masonry, plan_id="PLAN_TIPO")

    def test_building_creation_properties_and_validations(self):
        masonry = MasonrySpecification.from_nbr16868(fbk=14.0)
        w1 = Wall(wall_id="P1", axis=Axis(Point2D(0, 0), Point2D(5, 0)), thickness=0.14)
        plan_tipo = FloorPlan(plan_id="PLAN_TIPO", height=2.80, walls=(w1,))

        w2 = Wall(wall_id="P2", axis=Axis(Point2D(0, 0), Point2D(8, 0)), thickness=0.19)
        plan_terreo = FloorPlan(plan_id="PLAN_TERREO", height=3.00, walls=(w2,))

        st_cob = Story(story_id="COBERTURA", elevation=9.0, story_height=3.00, masonry_spec=masonry, plan_id="PLAN_TIPO")
        st_p2 = Story(story_id="PAV_02", elevation=6.0, story_height=3.00, masonry_spec=masonry, plan_id="PLAN_TIPO")
        st_p1 = Story(story_id="PAV_01", elevation=3.0, story_height=3.00, masonry_spec=masonry, plan_id="PLAN_TIPO")
        st_ter = Story(story_id="TERREO", elevation=0.0, story_height=3.00, masonry_spec=masonry, plan_id="PLAN_TERREO")

        building = Building(
            building_id="EDIF_AURORA",
            floor_plans=(plan_tipo, plan_terreo),
            stories=(st_cob, st_p2, st_p1, st_ter),
        )

        self.assertEqual(building.building_id, "EDIF_AURORA")
        self.assertEqual(building.num_stories, 4)
        self.assertEqual(building.top_story.story_id, "COBERTURA")
        self.assertEqual(building.bottom_story.story_id, "TERREO")
        # Altura total: (9.0 + 3.0) - 0.0 = 12.0
        self.assertAlmostEqual(building.total_height, 12.0)

        # Consultas de catálogo
        self.assertIs(building.get_floor_plan("PLAN_TIPO"), plan_tipo)
        self.assertIs(building.get_floor_plan("PLAN_TERREO"), plan_terreo)
        self.assertIsNone(building.get_floor_plan("PLAN_UNKNOWN"))

        # Consultas de pavimentos
        self.assertIs(building.find_story("PAV_01"), st_p1)
        self.assertIsNone(building.find_story("PAV_UNKNOWN"))
        self.assertEqual(len(building.find_stories_by_plan("PLAN_TIPO")), 3)
        self.assertEqual(len(building.find_stories_by_plan("PLAN_TERREO")), 1)

        # get_story_floor_plan
        self.assertIs(building.get_story_floor_plan(st_p1), plan_tipo)
        self.assertIs(building.get_story_floor_plan("TERREO"), plan_terreo)
        with self.assertRaises(KeyError):
            building.get_story_floor_plan("NONEXISTENT")

        # Validações de Building:
        # 1. ID de pavimento duplicado
        with self.assertRaises(ValueError):
            Building("ERR", floor_plans=(plan_tipo,), stories=(st_p1, st_p1))

        # 2. ID de planta duplicado no catálogo
        with self.assertRaises(ValueError):
            Building("ERR", floor_plans=(plan_tipo, plan_tipo), stories=(st_p1,))

        # 3. Integridade referencial
        st_missing = Story("ERR", elevation=0.0, story_height=3.0, masonry_spec=masonry, plan_id="PLAN_MISSING")
        with self.assertRaises(ValueError):
            Building("ERR", floor_plans=(plan_tipo,), stories=(st_missing,))

        # 4. Ordenação Z não decrescente
        with self.assertRaises(ValueError):
            Building("ERR", floor_plans=(plan_tipo,), stories=(st_p1, st_p2))

        # Métodos funcionais add_floor_plan e add_story
        b_init = Building("EDIF_MUT", floor_plans=(plan_tipo,))
        self.assertEqual(b_init.total_height, 0.0)
        self.assertIsNone(b_init.top_story)

        b_with_plan = b_init.add_floor_plan(plan_terreo)
        self.assertEqual(len(b_with_plan.floor_plans), 2)

        # Adicionar pavimentos fora de ordem que são auto-ordenados por Z decrescente
        b_with_st1 = b_with_plan.add_story(st_p1)
        b_with_st2 = b_with_st1.add_story(st_cob)
        self.assertEqual([s.story_id for s in b_with_st2.stories], ["COBERTURA", "PAV_01"])

    def test_wall_bond_and_junction_detection(self):
        # 1. Default é BondType.NONE (extremidade livre / sem encontro)
        w = Wall(wall_id="W1", axis=Axis(Point2D(0, 0), Point2D(5, 0)), thickness=0.14)
        self.assertEqual(w.start_bond, BondType.NONE)
        self.assertEqual(w.end_bond, BondType.NONE)

        # Alterar para DIRECT (quando há junção real)
        w_dir = w.set_start_bond(BondType.DIRECT)
        self.assertEqual(w_dir.start_bond, BondType.DIRECT)
        self.assertEqual(w_dir.end_bond, BondType.NONE)

        # Alterar para INDIRECT
        w_ind = w.set_bond(WallEnd.END, BondType.INDIRECT)
        self.assertEqual(w_ind.start_bond, BondType.NONE)
        self.assertEqual(w_ind.end_bond, BondType.INDIRECT)

        # Passando None → converte para BondType.NONE
        w_none = Wall(
            wall_id="W_NONE",
            axis=Axis(Point2D(0, 0), Point2D(5, 0)),
            thickness=0.14,
            start_bond=None,
            end_bond=None,
        )
        self.assertEqual(w_none.start_bond, BondType.NONE)
        self.assertEqual(w_none.end_bond, BondType.NONE)

        w_set_none = w_dir.set_bond(WallEnd.START, None)
        self.assertEqual(w_set_none.start_bond, BondType.NONE)

        # 2. Encontro em X com 3 paredes (1 passando, 2 chegando com amarrações distintas)
        w_h = Wall(wall_id="W_H", axis=Axis(Point2D(0, 0), Point2D(10, 0)), thickness=0.14)
        # Parede vertical superior: chega em (5, 0) pelo start com DIRECT
        w_v_top = Wall(
            wall_id="W_VT",
            axis=Axis(Point2D(5, 0), Point2D(5, 5)),
            thickness=0.14,
            start_bond=BondType.DIRECT,
        )
        # Parede vertical inferior: chega em (5, 0) pelo end com INDIRECT
        w_v_bot = Wall(
            wall_id="W_VB",
            axis=Axis(Point2D(5, -5), Point2D(5, 0)),
            thickness=0.14,
            end_bond=BondType.INDIRECT,
        )

        plan_x = FloorPlan(plan_id="PLAN_X", height=2.80, walls=(w_h, w_v_top, w_v_bot))
        junctions_x = plan_x.find_junctions()

        self.assertEqual(len(junctions_x), 1)
        j_x = junctions_x[0]
        self.assertEqual(j_x.point, Point2D(5.0, 0.0))
        self.assertEqual(j_x.total_incident_walls, 3)
        self.assertEqual(len(j_x.passing_walls), 1)
        self.assertIsInstance(j_x.passing_walls[0], PassingWall)
        self.assertEqual(j_x.passing_walls[0].wall_id, "W_H")
        self.assertAlmostEqual(w_h.axis.projected_offset(j_x.point), 5.0)  # junção no meio da parede de 10m
        self.assertEqual(len(j_x.arriving_walls), 2)
        self.assertTrue(j_x.has_indirect_bonds)

        # Verificação dos métodos de consulta em Junction
        self.assertTrue(j_x.has_wall("W_H"))
        self.assertTrue(j_x.has_wall("W_VT"))
        self.assertTrue(j_x.has_wall("W_VB"))
        self.assertFalse(j_x.has_wall("W_UNKNOWN"))

        self.assertTrue(j_x.is_passing("W_H"))
        self.assertFalse(j_x.is_passing("W_VT"))
        self.assertFalse(j_x.is_passing("W_UNKNOWN"))

        self.assertTrue(j_x.is_arriving("W_VT"))
        self.assertTrue(j_x.is_arriving("W_VB"))
        self.assertFalse(j_x.is_arriving("W_H"))

        part_h = j_x.get_participation("W_H")
        self.assertIsInstance(part_h, PassingWall)
        self.assertEqual(part_h.wall_id, "W_H")

        part_vt = j_x.get_participation("W_VT")
        self.assertIsInstance(part_vt, ArrivingWall)
        self.assertEqual(part_vt.wall_id, "W_VT")

        self.assertIsNone(j_x.get_participation("W_UNKNOWN"))

        arriving_map = {aw.wall_id: aw for aw in j_x.arriving_walls}
        self.assertEqual(arriving_map["W_VT"].wall_end, WallEnd.START)
        self.assertEqual(arriving_map["W_VT"].bond, BondType.DIRECT)
        self.assertEqual(arriving_map["W_VB"].wall_end, WallEnd.END)
        self.assertEqual(arriving_map["W_VB"].bond, BondType.INDIRECT)

        # 3. Encontro em T com 3 paredes (todas chegando em (5, 5))
        w_t1 = Wall(wall_id="T1", axis=Axis(Point2D(0, 5), Point2D(5, 5)), thickness=0.14, end_bond=BondType.DIRECT)
        w_t2 = Wall(wall_id="T2", axis=Axis(Point2D(10, 5), Point2D(5, 5)), thickness=0.14, end_bond=BondType.DIRECT)
        w_t3 = Wall(wall_id="T3", axis=Axis(Point2D(5, 0), Point2D(5, 5)), thickness=0.14, end_bond=BondType.DIRECT)

        plan_t3 = FloorPlan(plan_id="PLAN_T3", height=2.80, walls=(w_t1, w_t2, w_t3))
        junctions_t3 = plan_t3.find_junctions()
        self.assertEqual(len(junctions_t3), 1)
        j_t3 = junctions_t3[0]
        self.assertEqual(j_t3.point, Point2D(5.0, 5.0))
        self.assertEqual(len(j_t3.passing_walls), 0)
        self.assertEqual(len(j_t3.arriving_walls), 3)

        # 4. Encontro em T com 2 paredes (1 passando, 1 chegando com alteração na planta)
        w_pass = Wall(wall_id="P_PASS", axis=Axis(Point2D(0, 0), Point2D(10, 0)), thickness=0.14)
        w_arr = Wall(wall_id="P_ARR", axis=Axis(Point2D(5, 0), Point2D(5, 4)), thickness=0.14)

        plan_t2 = FloorPlan(plan_id="PLAN_T2", height=2.80, walls=(w_pass, w_arr))
        plan_t2_ind = plan_t2.set_wall_bond("P_ARR", WallEnd.START, BondType.INDIRECT)

        j_t2 = plan_t2_ind.find_junctions()[0]
        self.assertEqual(j_t2.point, Point2D(5.0, 0.0))
        self.assertEqual(len(j_t2.passing_walls), 1)
        self.assertEqual(j_t2.passing_walls[0].wall_id, "P_PASS")
        self.assertAlmostEqual(w_pass.axis.projected_offset(j_t2.point), 5.0)
        self.assertEqual(len(j_t2.arriving_walls), 1)
        self.assertEqual(j_t2.arriving_walls[0].bond, BondType.INDIRECT)
        self.assertTrue(j_t2.has_indirect_bonds)

    def test_opening_validation_against_junction_crossing(self):
        # Parede 1 (horizontal): (0,0) -> (10,0), espessura 0.14m
        w1 = Wall(wall_id="W1", axis=Axis(Point2D(0, 0), Point2D(10, 0)), thickness=0.14)
        # Parede 2 (vertical): (5,0) -> (5,5), espessura 0.20m
        w2 = Wall(wall_id="W2", axis=Axis(Point2D(5, 0), Point2D(5, 5)), thickness=0.20)

        plan = FloorPlan(plan_id="PLAN_CROSS", height=2.80, walls=(w1, w2))

        # Zonas de exclusão:
        # Em W1: [5.0 - 0.10, 5.0 + 0.10] = [4.90, 5.10]
        # Em W2: [0.0, 0.07]
        intervals_w1 = plan.get_junction_exclusion_intervals("W1")
        self.assertEqual(len(intervals_w1), 1)
        self.assertAlmostEqual(intervals_w1[0][0], 4.90)
        self.assertAlmostEqual(intervals_w1[0][1], 5.10)
        self.assertEqual(intervals_w1[0][2], "W2")

        intervals_w2 = plan.get_junction_exclusion_intervals("W2")
        self.assertEqual(len(intervals_w2), 1)
        self.assertAlmostEqual(intervals_w2[0][0], 0.0)
        self.assertAlmostEqual(intervals_w2[0][1], 0.07)
        self.assertEqual(intervals_w2[0][2], "W1")

        # 1. Abertura válida longe do cruzamento em W1 ([1.0, 2.0])
        plan_valid = plan.add_door(
            wall_id="W1",
            opening_id="D1",
            offset_along_wall=1.0,
            width=1.0,
            height=2.10,
        )
        self.assertEqual(len(plan_valid.find_wall("W1").openings), 1)

        # 2. Abertura que intercepta o cruzamento em W1 ([4.5, 5.5] sobrepõe [4.90, 5.10])
        with self.assertRaises(ValueError) as ctx:
            plan.add_door(
                wall_id="W1",
                opening_id="D_BAD",
                offset_along_wall=4.5,
                width=1.0,
                height=2.10,
            )
        self.assertIn("intercepta a zona de cruzamento", str(ctx.exception))

        # 3. Abertura que intercepta o encontro no início de W2 ([0.05, 0.85] sobrepõe [0.0, 0.07])
        with self.assertRaises(ValueError) as ctx:
            plan.add_door(
                wall_id="W2",
                opening_id="D_BAD_W2",
                offset_along_wall=0.05,
                width=0.80,
                height=2.10,
            )
        self.assertIn("intercepta a zona de cruzamento", str(ctx.exception))

        # 4. Abertura válida em W2 após a zona de encontro ([0.10, 0.90])
        plan_valid_w2 = plan.add_door(
            wall_id="W2",
            opening_id="D_OK_W2",
            offset_along_wall=0.10,
            width=0.80,
            height=2.10,
        )
        self.assertEqual(len(plan_valid_w2.find_wall("W2").openings), 1)

    def test_bond_validation_requires_junction(self):
        # Parede isolada (sem encontros com outras paredes)
        w_iso = Wall(wall_id="ISO", axis=Axis(Point2D(0, 0), Point2D(5, 0)), thickness=0.14)
        plan = FloorPlan(plan_id="PLAN_ISO", height=2.80, walls=(w_iso,))

        # Tentativa de definir DIRECT em extremidade livre -> erro
        with self.assertRaises(ValueError) as ctx:
            plan.set_wall_bond("ISO", WallEnd.START, BondType.DIRECT)
        self.assertIn("não há junção com outra parede neste ponto", str(ctx.exception))

        # Tentativa de definir INDIRECT em extremidade livre -> erro
        with self.assertRaises(ValueError) as ctx:
            plan.set_wall_bond("ISO", WallEnd.END, BondType.INDIRECT)
        self.assertIn("não há junção com outra parede neste ponto", str(ctx.exception))

        # Definir NONE ou None em extremidade livre -> sucesso
        plan_none = plan.set_wall_bond("ISO", WallEnd.START, BondType.NONE)
        self.assertEqual(plan_none.find_wall("ISO").start_bond, BondType.NONE)

        # Inicializar FloorPlan com parede contendo bond != NONE sem junção -> erro
        w_invalid = Wall(
            wall_id="INV",
            axis=Axis(Point2D(0, 0), Point2D(5, 0)),
            thickness=0.14,
            start_bond=BondType.DIRECT,
        )
        with self.assertRaises(ValueError) as ctx:
            FloorPlan(plan_id="PLAN_INV", height=2.80, walls=(w_invalid,))
        self.assertIn("não há junção com outra parede neste ponto", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()


