from __future__ import annotations

import math
import unittest
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.tolerances import is_close, is_zero
from pymasondesign.drafting.enums import BondType
from pymasondesign.drafting.wall import Wall
from pymasondesign.drafting.floor_plan import FloorPlan
from pymasondesign.structure.panel import MasonryPanel
from pymasondesign.structure.group import PanelGroup
from pymasondesign.structure.service import MasonryPanelService
from pymasondesign.design.enums import SegmentRole
from pymasondesign.design.options import FlangeOptions
from pymasondesign.design.segment import ResistantSegment
from pymasondesign.design.section import ResistantSection
from pymasondesign.design.service import ResistantSectionService, create_rectangle_polygon


class TestResistantSection(unittest.TestCase):
    """Testes unitários para o modelo de Seção Resistente e derivação de almas e abas colaborantes."""

    def test_isolated_rectangular_wall(self) -> None:
        """Parede retangular isolada (1 alma, 0 abas)."""
        axis = Axis(Point2D(0.0, 0.0), Point2D(300.0, 0.0))
        panel = MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=axis, thickness=14.0, height=280.0)
        group = PanelGroup(group_id="PG1", panels=(panel,))

        sections = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))
        self.assertEqual(len(sections), 1)

        sec = sections[0]
        self.assertEqual(sec.group_id, "PG1")
        self.assertEqual(sec.num_webs, 1)
        self.assertEqual(sec.num_flanges, 0)
        self.assertEqual(sec.web_panel_ids, ("P1_P1",))

        # Geometria e inércia retangular em coordenadas locais
        # A = 300 * 14 = 4200
        self.assertTrue(is_close(sec.total_area, 4200.0))
        # Ixx local = 300 * 14^3 / 12 = 68600.0
        self.assertTrue(is_close(sec.properties.ixx, 300.0 * (14.0**3) / 12.0))
        # Iyy local = 14 * 300^3 / 12 = 31500000.0
        self.assertTrue(is_close(sec.properties.iyy, 14.0 * (300.0**3) / 12.0))
        # Centróide local é exatamente (0, 0)
        self.assertTrue(is_zero(sec.properties.cg.x))
        self.assertTrue(is_zero(sec.properties.cg.y))

        # Transformação local para global
        # Centróide local (0, 0) deve mapear para o centróide global (150, 0)
        cg_global = sec.local_to_global.apply_point(Point2D(0.0, 0.0))
        self.assertTrue(is_close(cg_global.x, 150.0))
        self.assertTrue(is_close(cg_global.y, 0.0))

    def test_t_section_direct_bond(self) -> None:
        """Seção em T com amarração direta (2 painéis de alma colineares + 2 ramos de aba simétricos discretizados)."""
        # Alma longitudinal em X dividida no nó de encontro (x = 150)
        w1 = MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=Axis(Point2D(0.0, 0.0), Point2D(150.0, 0.0)), thickness=14.0, height=280.0)
        w2 = MasonryPanel(panel_id="P1_P2", wall_id="P1", axis=Axis(Point2D(150.0, 0.0), Point2D(300.0, 0.0)), thickness=14.0, height=280.0)

        # Flange transversal em Y dividida no nó de encontro (x = 150)
        f_pos = MasonryPanel(panel_id="P2_P1", wall_id="P2", axis=Axis(Point2D(150.0, 0.0), Point2D(150.0, 100.0)), thickness=14.0, height=280.0)
        f_neg = MasonryPanel(panel_id="P2_P2", wall_id="P2", axis=Axis(Point2D(150.0, -100.0), Point2D(150.0, 0.0)), thickness=14.0, height=280.0)

        group = PanelGroup(group_id="PG1", panels=(w1, w2, f_pos, f_neg))

        # Análise na direção X
        sections = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))
        self.assertEqual(len(sections), 1)

        sec = sections[0]
        self.assertEqual(sec.num_webs, 2)
        self.assertEqual(sec.num_flanges, 2)  # 2 ramos de aba (positivo e negativo)

        # Alma: L = 150 + 150 = 300, t = 14, Área = 4200
        # Abas: cada ramo tem L_disp = 100, L_disp_ext = 100 - 7 = 93.
        # Limite NBR 6 * t_web = 6 * 14 = 84.
        # Largura efetiva bf = min(93, 84) = 84.
        # Área total = 4200 + 2 * (84 * 14) = 4200 + 2352 = 6552
        self.assertTrue(is_close(sec.total_area, 6552.0))

        # Almas mantêm precedência integral
        self.assertTrue(is_close(sum(w.area for w in sec.webs), 4200.0))

        # Abas
        for f_seg in sec.flanges:
            self.assertTrue(is_close(f_seg.effective_length, 84.0))
            self.assertTrue(is_close(f_seg.area, 84.0 * 14.0))

        # Centróide local (0, 0)
        self.assertTrue(is_zero(sec.properties.cg.x))
        self.assertTrue(is_zero(sec.properties.cg.y))

        # Centróide global é (150, 0) devido à simetria em T duplo / Cruz
        cg_global = sec.local_to_global.apply_point(Point2D(0.0, 0.0))
        self.assertTrue(is_close(cg_global.x, 150.0))
        self.assertTrue(is_close(cg_global.y, 0.0))

    def test_l_section_direct_bond(self) -> None:
        """Seção em L assimétrica com amarração direta."""
        # Alma longitudinal em X: de (0, 0) a (200, 0)
        web_axis = Axis(Point2D(0.0, 0.0), Point2D(200.0, 0.0))
        web_panel = MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=web_axis, thickness=14.0, height=280.0)

        # Flange transversal em Y: de (0, 0) a (0, 100)
        flange_axis = Axis(Point2D(0.0, 0.0), Point2D(0.0, 100.0))
        flange_panel = MasonryPanel(panel_id="P2_P1", wall_id="P2", axis=flange_axis, thickness=14.0, height=280.0)

        group = PanelGroup(group_id="PG1", panels=(web_panel, flange_panel))

        sections = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))
        self.assertEqual(len(sections), 1)

        sec = sections[0]
        self.assertEqual(sec.num_webs, 1)
        self.assertEqual(sec.num_flanges, 1)

        # Alma: 200 * 14 = 2800
        # Aba: L_disp = 100, L_disp_ext = 100 - 7 = 93. Limite = 6 * 14 = 84. bf = 84.
        # Área aba = 84 * 14 = 1176
        # Área total = 2800 + 1176 = 3976
        self.assertTrue(is_close(sec.total_area, 3976.0))
        self.assertEqual(sec.webs[0].effective_length, 200.0)
        self.assertEqual(sec.flanges[0].effective_length, 84.0)

    def test_l_section_bidirectional_analysis(self) -> None:
        """Inversão de papéis (alma vs aba) no mesmo grupo em L nas direções X e Y."""
        w1_axis = Axis(Point2D(0.0, 0.0), Point2D(200.0, 0.0))
        w1 = MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=w1_axis, thickness=14.0, height=280.0)

        w2_axis = Axis(Point2D(0.0, 0.0), Point2D(0.0, 150.0))
        w2 = MasonryPanel(panel_id="P2_P1", wall_id="P2", axis=w2_axis, thickness=14.0, height=280.0)

        group = PanelGroup(group_id="PG_L", panels=(w1, w2))

        # 1. Análise na direção X: P1 é WEB, P2 é FLANGE
        sec_x = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))[0]
        self.assertEqual(sec_x.web_panel_ids, ("P1_P1",))
        self.assertEqual(sec_x.flange_panel_ids, ("P2_P1",))
        self.assertTrue(is_close(sec_x.webs[0].effective_length, 200.0))
        self.assertTrue(is_close(sec_x.flanges[0].effective_length, 84.0))

        # 2. Análise na direção Y: P2 é WEB, P1 é FLANGE
        sec_y = ResistantSectionService.derive_for_group(group, Vector2D(0.0, 1.0))[0]
        self.assertEqual(sec_y.web_panel_ids, ("P2_P1",))
        self.assertEqual(sec_y.flange_panel_ids, ("P1_P1",))
        self.assertTrue(is_close(sec_y.webs[0].effective_length, 150.0))
        self.assertTrue(is_close(sec_y.flanges[0].effective_length, 84.0))

    def test_u_section_multi_web(self) -> None:
        """Seção em U com múltiplas almas paralelas conectadas por flange comum."""
        # Duas almas paralelas em X
        w1 = MasonryPanel(panel_id="W1", wall_id="P1", axis=Axis(Point2D(0.0, 0.0), Point2D(200.0, 0.0)), thickness=14.0, height=280.0)
        w2 = MasonryPanel(panel_id="W2", wall_id="P2", axis=Axis(Point2D(0.0, 100.0), Point2D(200.0, 100.0)), thickness=14.0, height=280.0)

        # Flange de fundo em Y conectando as duas almas em x = 0
        flange = MasonryPanel(panel_id="F1", wall_id="P3", axis=Axis(Point2D(0.0, 0.0), Point2D(0.0, 100.0)), thickness=14.0, height=280.0)

        group = PanelGroup(group_id="PG_U", panels=(w1, w2, flange))

        sections = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))
        self.assertEqual(len(sections), 1)

        sec = sections[0]
        self.assertEqual(sec.num_webs, 2)
        self.assertEqual(set(sec.web_panel_ids), {"W1", "W2"})
        self.assertEqual(sec.flange_panel_ids, ("F1",))

        # Distância entre eixos das almas = 100. Vão livre = 100 - 14 = 86.
        # Metade do vão livre por alma = 86 / 2 = 43.
        # Cada alma gera um segmento de aba de 43 cm no vão interno.
        # Área = 2 * (200 * 14) + 2 * (43 * 14) = 5600 + 1204 = 6804.
        self.assertTrue(is_close(sec.total_area, 6804.0))

    def test_u_section_large_span_separate_sections(self) -> None:
        """Seção em U com vão transversal grande (L_transversal >= 6*t1 + 6*t2) desacopla em 2 seções distintas."""
        # Duas almas paralelas em X distantes 300 cm
        w1 = MasonryPanel(panel_id="W1", wall_id="P1", axis=Axis(Point2D(0.0, 0.0), Point2D(200.0, 0.0)), thickness=14.0, height=280.0)
        w2 = MasonryPanel(panel_id="W2", wall_id="P2", axis=Axis(Point2D(0.0, 300.0), Point2D(200.0, 300.0)), thickness=14.0, height=280.0)

        # Flange de fundo em Y com L = 300 cm (> 6*14 + 6*14 = 168 cm)
        flange = MasonryPanel(panel_id="F1", wall_id="P3", axis=Axis(Point2D(0.0, 0.0), Point2D(0.0, 300.0)), thickness=14.0, height=280.0)

        group = PanelGroup(group_id="PG_U_LARGE", panels=(w1, w2, flange))

        sections = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))
        # Deve desacoplar em 2 seções em L separadas
        self.assertEqual(len(sections), 2)

        for sec in sections:
            self.assertEqual(sec.num_webs, 1)
            self.assertEqual(sec.num_flanges, 1)
            # Cada seção tem aba de comprimento integral máximo 6 * 14 = 84 cm
            self.assertTrue(is_close(sec.flanges[0].effective_length, 84.0))
            # Área de cada seção = 200*14 + 84*14 = 2800 + 1176 = 3976
            self.assertTrue(is_close(sec.total_area, 3976.0))

    def test_flange_options_custom_width_and_max(self) -> None:
        """Validação das opções FlangeOptions: custom_width e max_multiplier."""
        w1 = MasonryPanel(panel_id="W1", wall_id="P1", axis=Axis(Point2D(0.0, 0.0), Point2D(150.0, 0.0)), thickness=14.0, height=280.0)
        w2 = MasonryPanel(panel_id="W2", wall_id="P1", axis=Axis(Point2D(150.0, 0.0), Point2D(300.0, 0.0)), thickness=14.0, height=280.0)
        flange = MasonryPanel(panel_id="F1", wall_id="P2", axis=Axis(Point2D(150.0, 0.0), Point2D(150.0, 200.0)), thickness=14.0, height=280.0)
        group = PanelGroup(group_id="PG1", panels=(w1, w2, flange))

        # 1. Custom width = 50.0
        opt_custom = FlangeOptions(custom_width=50.0)
        sec_custom = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0), opt_custom)[0]
        self.assertEqual(sec_custom.num_flanges, 1)
        self.assertTrue(is_close(sec_custom.flanges[0].effective_length, 50.0))

        # 2. Max multiplier = 3.0 (3 * 14 = 42.0)
        opt_max3 = FlangeOptions(max_multiplier=3.0)
        sec_max3 = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0), opt_max3)[0]
        self.assertEqual(sec_max3.num_flanges, 1)
        self.assertTrue(is_close(sec_max3.flanges[0].effective_length, 42.0))

    def test_derive_for_floor_plan(self) -> None:
        """Derivação completa de seções resistentes para um FloorPlan estrutural."""
        w1 = Wall(wall_id="P1", axis=Axis(Point2D(0.0, 0.0), Point2D(300.0, 0.0)), thickness=14.0, height=280.0, start_bond=BondType.DIRECT, end_bond=BondType.NONE)
        w2 = Wall(wall_id="P2", axis=Axis(Point2D(0.0, 0.0), Point2D(0.0, 200.0)), thickness=14.0, height=280.0, start_bond=BondType.DIRECT, end_bond=BondType.NONE)
        w3 = Wall(wall_id="P3", axis=Axis(Point2D(500.0, 0.0), Point2D(800.0, 0.0)), thickness=14.0, height=280.0)

        fp = FloorPlan(plan_id="TIPO", height=280.0, walls=(w1, w2, w3))
        fp_model = MasonryPanelService.derive_floor_plan_model(fp)

        # Análise na direção X
        sections_x = ResistantSectionService.derive_for_floor_plan(fp_model, Vector2D(1.0, 0.0))
        # Deve encontrar 2 seções em X (o grupo L com P1 e o grupo isolado P3)
        self.assertEqual(len(sections_x), 2)

        # Análise na direção Y
        sections_y = ResistantSectionService.derive_for_floor_plan(fp_model, Vector2D(0.0, 1.0))
        # Deve encontrar 1 seção em Y (o grupo L com P2)
        self.assertEqual(len(sections_y), 1)

    def test_validation_and_errors(self) -> None:
        """Validações de argumentos inválidos em FlangeOptions, ResistantSegment e ResistantSection."""
        with self.assertRaises(ValueError):
            FlangeOptions(max_multiplier=-1.0)

        with self.assertRaises(ValueError):
            FlangeOptions(custom_width=0.0)

        axis = Axis(Point2D(0.0, 0.0), Point2D(100.0, 0.0))
        poly = create_rectangle_polygon(axis, 14.0)

        with self.assertRaises(ValueError):
            ResistantSegment(
                segment_id="SEG1",
                source_panel_id="P1",
                role=SegmentRole.WEB,
                local_axis=axis,
                global_axis=axis,
                thickness=0.0,
                effective_length=100.0,
                local_polygon=poly,
                global_polygon=poly,
            )

        with self.assertRaises(ValueError):
            ResistantSegment(
                segment_id="SEG1",
                source_panel_id="P1",
                role=SegmentRole.WEB,
                local_axis=axis,
                global_axis=axis,
                thickness=14.0,
                effective_length=-10.0,
                local_polygon=poly,
                global_polygon=poly,
            )

        # Vetor nulo no serviço
        panel = MasonryPanel(panel_id="P1_P1", wall_id="P1", axis=axis, thickness=14.0, height=280.0)
        group = PanelGroup(group_id="PG1", panels=(panel,))
        with self.assertRaises(ValueError):
            ResistantSectionService.derive_for_group(group, Vector2D(0.0, 0.0))

        # Busca de segmento
        sec = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))[0]
        self.assertIsNotNone(sec.find_segment("RS_PG1_X_01_WEB_P1_P1"))
        self.assertIsNone(sec.find_segment("NON_EXISTENT"))

    def test_segment_touches(self) -> None:
        """Verifica o método touches entre ResistantSegments."""
        axis1 = Axis(Point2D(0.0, 0.0), Point2D(100.0, 0.0))
        poly1 = create_rectangle_polygon(axis1, 14.0)
        seg1 = ResistantSegment("S1", "P1", SegmentRole.WEB, axis1, axis1, 14.0, 100.0, poly1, poly1)

        axis2 = Axis(Point2D(100.0, 0.0), Point2D(100.0, 80.0))
        poly2 = create_rectangle_polygon(axis2, 14.0)
        seg2 = ResistantSegment("S2", "P2", SegmentRole.FLANGE, axis2, axis2, 14.0, 80.0, poly2, poly2)

        axis3 = Axis(Point2D(500.0, 0.0), Point2D(600.0, 0.0))
        poly3 = create_rectangle_polygon(axis3, 14.0)
        seg3 = ResistantSegment("S3", "P3", SegmentRole.WEB, axis3, axis3, 14.0, 100.0, poly3, poly3)

        self.assertTrue(seg1.touches(seg2))
        self.assertTrue(seg2.touches(seg1))
        self.assertFalse(seg1.touches(seg3))
        self.assertFalse(seg2.touches(seg3))


if __name__ == "__main__":
    unittest.main()
