from __future__ import annotations

import unittest
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.tolerances import is_close, is_zero
from pymasondesign.structure.panel import MasonryPanel
from pymasondesign.structure.group import PanelGroup
from pymasondesign.design.service import ResistantSectionService
from pymasondesign.design.grouting import (
    GroutInterval,
    SegmentGroutDemand,
    SectionGroutDemand,
)


class TestDesignGrouting(unittest.TestCase):
    """Testes unitários para a modelagem da demanda de grauteamento na seção resistente."""

    def test_grout_interval_validations_and_properties(self) -> None:
        """Validação de criação, propriedades e restrições de GroutInterval."""
        inv = GroutInterval(start_offset=0.0, end_offset=100.0, ratio=1.0)
        self.assertTrue(is_close(inv.start_offset, 0.0))
        self.assertTrue(is_close(inv.end_offset, 100.0))
        self.assertTrue(is_close(inv.ratio, 1.0))
        self.assertTrue(is_close(inv.length, 100.0))
        self.assertTrue(inv.is_fully_grouted)
        self.assertFalse(inv.is_ungrouted)

        self.assertTrue(inv.contains(0.0))
        self.assertTrue(inv.contains(50.0))
        self.assertTrue(inv.contains(100.0))
        self.assertFalse(inv.contains(-1.0))
        self.assertFalse(inv.contains(101.0))

        # Intervalo não grauteado
        inv_zero = GroutInterval(start_offset=100.0, end_offset=200.0, ratio=0.0)
        self.assertTrue(inv_zero.is_ungrouted)
        self.assertFalse(inv_zero.is_fully_grouted)

        # Validações de erro
        with self.assertRaises(ValueError):
            GroutInterval(start_offset=-10.0, end_offset=50.0, ratio=1.0)

        with self.assertRaises(ValueError):
            GroutInterval(start_offset=50.0, end_offset=50.0, ratio=1.0)

        with self.assertRaises(ValueError):
            GroutInterval(start_offset=80.0, end_offset=50.0, ratio=1.0)

        with self.assertRaises(ValueError):
            GroutInterval(start_offset=0.0, end_offset=100.0, ratio=-0.1)

        with self.assertRaises(ValueError):
            GroutInterval(start_offset=0.0, end_offset=100.0, ratio=1.5)

    def test_segment_grout_demand_multi_intervals_and_lookup(self) -> None:
        """Demanda com múltiplos trechos percentuais ao longo de um segmento resistente."""
        # 100% de 0 a 100cm, 80% de 100 a 200cm, 0% de 200 a 300cm
        demand = SegmentGroutDemand.from_spans(
            segment_id="RS_P1_WEB_1",
            effective_length=300.0,
            spans=[
                (0.0, 100.0, 1.0),
                (100.0, 200.0, 0.8),
                (200.0, 300.0, 0.0),
            ],
        )

        self.assertEqual(demand.segment_id, "RS_P1_WEB_1")
        self.assertTrue(is_close(demand.effective_length, 300.0))
        self.assertEqual(len(demand.intervals), 3)

        # Média ponderada = (100*1.0 + 100*0.8 + 100*0.0) / 300 = 180 / 300 = 0.6
        self.assertTrue(is_close(demand.average_ratio, 0.6))
        self.assertTrue(is_close(demand.max_ratio, 1.0))
        self.assertTrue(is_close(demand.min_ratio, 0.0))
        self.assertFalse(demand.is_fully_grouted)
        self.assertFalse(demand.is_ungrouted)

        # Consultas pontuais por cota
        self.assertTrue(is_close(demand.ratio_at(0.0), 1.0))
        self.assertTrue(is_close(demand.ratio_at(50.0), 1.0))
        self.assertTrue(is_close(demand.ratio_at(150.0), 0.8))
        self.assertTrue(is_close(demand.ratio_at(250.0), 0.0))
        self.assertTrue(is_close(demand.ratio_at(300.0), 0.0))

        # Cota fora do domínio do segmento
        with self.assertRaises(ValueError):
            demand.ratio_at(-5.0)

        with self.assertRaises(ValueError):
            demand.ratio_at(350.0)

    def test_segment_grout_demand_continuity_validations(self) -> None:
        """Validação de ordenação, contiguidade e limites exatos nos trechos de graute."""
        # Comprimento efetivo inválido
        with self.assertRaises(ValueError):
            SegmentGroutDemand.uniform("SEG_1", effective_length=-100.0, ratio=1.0)

        # Sem intervalos
        with self.assertRaises(ValueError):
            SegmentGroutDemand(segment_id="SEG_1", effective_length=100.0, intervals=())

        # Não inicia em 0.0
        with self.assertRaises(ValueError):
            SegmentGroutDemand(
                segment_id="SEG_1",
                effective_length=200.0,
                intervals=(GroutInterval(10.0, 200.0, 1.0),),
            )

        # Não termina em effective_length
        with self.assertRaises(ValueError):
            SegmentGroutDemand(
                segment_id="SEG_1",
                effective_length=200.0,
                intervals=(GroutInterval(0.0, 150.0, 1.0),),
            )

        # Lacuna (buraco) entre intervalos consecutivos
        with self.assertRaises(ValueError):
            SegmentGroutDemand(
                segment_id="SEG_1",
                effective_length=300.0,
                intervals=(
                    GroutInterval(0.0, 100.0, 1.0),
                    GroutInterval(120.0, 300.0, 0.5),
                ),
            )

        # Sobreposição entre intervalos consecutivos
        with self.assertRaises(ValueError):
            SegmentGroutDemand(
                segment_id="SEG_1",
                effective_length=300.0,
                intervals=(
                    GroutInterval(0.0, 150.0, 1.0),
                    GroutInterval(100.0, 300.0, 0.5),
                ),
            )

    def test_segment_grout_demand_uniform_helpers(self) -> None:
        """Validação dos métodos de fábrica para demandas uniformes."""
        d_full = SegmentGroutDemand.uniform("SEG_1", 200.0, 1.0)
        self.assertTrue(d_full.is_fully_grouted)
        self.assertFalse(d_full.is_ungrouted)
        self.assertTrue(is_close(d_full.average_ratio, 1.0))

        d_empty = SegmentGroutDemand.uniform("SEG_2", 200.0, 0.0)
        self.assertTrue(d_empty.is_ungrouted)
        self.assertFalse(d_empty.is_fully_grouted)
        self.assertTrue(is_zero(d_empty.average_ratio))

    def test_section_grout_demand_consolidation(self) -> None:
        """Consolidação da demanda de grauteamento para múltiplos segmentos de uma ResistantSection."""
        sd_web = SegmentGroutDemand.from_spans(
            segment_id="RS_1_WEB",
            effective_length=200.0,
            spans=[(0.0, 200.0, 1.0)],  # 100% em 200cm
        )
        sd_flange = SegmentGroutDemand.from_spans(
            segment_id="RS_1_FLANGE",
            effective_length=100.0,
            spans=[(0.0, 50.0, 1.0), (50.0, 100.0, 0.0)],  # 50% média em 100cm
        )

        sec_demand = SectionGroutDemand(
            section_id="RS_1",
            segment_demands=(sd_web, sd_flange),
        )

        self.assertEqual(sec_demand.section_id, "RS_1")
        self.assertTrue(is_close(sec_demand.total_length, 300.0))

        # Média ponderada = (200*1.0 + 100*0.5) / 300 = 250 / 300 = 0.8333333333333334
        self.assertTrue(is_close(sec_demand.weighted_average_ratio, 250.0 / 300.0))
        self.assertFalse(sec_demand.is_fully_grouted)
        self.assertFalse(sec_demand.is_ungrouted)

        self.assertEqual(sec_demand.find_segment_demand("RS_1_WEB"), sd_web)
        self.assertEqual(sec_demand.find_segment_demand("RS_1_FLANGE"), sd_flange)
        self.assertIsNone(sec_demand.find_segment_demand("NON_EXISTENT"))

        # Validação de IDs duplicados
        with self.assertRaises(ValueError):
            SectionGroutDemand(
                section_id="RS_1",
                segment_demands=(sd_web, sd_web),
            )

        # Sem demandas de segmento
        with self.assertRaises(ValueError):
            SectionGroutDemand(section_id="RS_1", segment_demands=())

    def test_section_grout_demand_uniform_from_section(self) -> None:
        """Criação de SectionGroutDemand uniforme a partir de uma ResistantSection real."""
        axis = Axis(Point2D(0.0, 0.0), Point2D(300.0, 0.0))
        panel = MasonryPanel("P1_P1", "P1", axis, thickness=14.0, height=280.0)
        group = PanelGroup("PG1", panels=(panel,))

        section = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))[0]

        sec_demand = SectionGroutDemand.uniform(section, ratio=1.0)
        self.assertEqual(sec_demand.section_id, section.section_id)
        self.assertEqual(len(sec_demand.segment_demands), 1)
        self.assertTrue(sec_demand.is_fully_grouted)
        self.assertTrue(is_close(sec_demand.weighted_average_ratio, 1.0))


if __name__ == "__main__":
    unittest.main()
