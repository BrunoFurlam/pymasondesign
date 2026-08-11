from __future__ import annotations

import unittest
from pymasondesign.geometry.point import Point2D
from pymasondesign.geometry.vector import Vector2D
from pymasondesign.geometry.axis import Axis
from pymasondesign.geometry.tolerances import is_close, is_zero
from pymasondesign.materials.block import BlockSpecification
from pymasondesign.materials.mortar import MortarSpecification
from pymasondesign.materials.grout import GroutSpecification
from pymasondesign.materials.masonry import MasonrySpecification
from pymasondesign.mechanics.forces import SectionForces
from pymasondesign.structure.panel import MasonryPanel
from pymasondesign.structure.group import PanelGroup
from pymasondesign.design.service import ResistantSectionService
from pymasondesign.design.grouting import SectionGroutDemand
from pymasondesign.design.compression import (
    CompressionDesignOptions,
    CompressionDesignResult,
    CompressionVerificationResult,
    CompressionDesignService,
)


class TestDesignCompression(unittest.TestCase):
    """Testes unitários para o serviço de dimensionamento e verificação à flexo-compressão (NBR 16868-1)."""

    def setUp(self) -> None:
        # Especificação padrão de alvenaria: fpk = 8 MPa, fpgk = 14 MPa
        # fk_hollow = 0.70 * 1.0 * 8.0 = 5.6 MPa -> fd_hollow (gamma_m=2.0) = 2.8 MPa
        # fk_grouted = 0.70 * 1.0 * 14.0 = 9.8 MPa -> fd_grouted (gamma_m=2.0) = 4.9 MPa
        self.block = BlockSpecification.concrete(fbk=10.0)
        self.mortar = MortarSpecification(fa=6.0)
        self.grout = GroutSpecification(fg=20.0)
        self.masonry_spec = MasonrySpecification(
            block=self.block,
            mortar=self.mortar,
            grout=self.grout,
            fpk=8.0,
            fpgk=14.0,
            transverse_joints_filled=True,
        )

        # Parede padrão de 300 cm x 14 cm x 280 cm (A = 4200 cm², Ixx = 68600, Iyy = 31500000)
        axis = Axis(Point2D(0.0, 0.0), Point2D(300.0, 0.0))
        panel = MasonryPanel("P1_P1", "P1", axis, thickness=14.0, height=280.0)
        group = PanelGroup("PG1", panels=(panel,))
        self.section = ResistantSectionService.derive_for_group(group, Vector2D(1.0, 0.0))[0]

    def test_slenderness_and_reduction_factor(self) -> None:
        """Cálculo e limites normativos do índice de esbeltez (lambda) e do fator redutor R."""
        # lambda = 280 / 14 = 20.0 <= 24.0
        # R = 1 - (20/40)^3 = 1 - 0.125 = 0.875
        slenderness = CompressionDesignService.calculate_slenderness(height=280.0, thickness=14.0)
        self.assertTrue(is_close(slenderness, 20.0))

        r_factor = CompressionDesignService.calculate_reduction_factor(height=280.0, thickness=14.0)
        self.assertTrue(is_close(r_factor, 0.875))

        # Parede muito esbelta (lambda = 350 / 14 = 25.0 > 24.0)
        slenderness_high = CompressionDesignService.calculate_slenderness(height=350.0, thickness=14.0)
        self.assertTrue(is_close(slenderness_high, 25.0))

        # Validações de erro
        with self.assertRaises(ValueError):
            CompressionDesignService.calculate_slenderness(height=-280.0, thickness=14.0)
        with self.assertRaises(ValueError):
            CompressionDesignService.calculate_slenderness(height=280.0, thickness=0.0)

    def test_pure_compression_low_load_ungrouted(self) -> None:
        """Compressão pura com tensão inferior a fd_hollow não requer grauteamento (ratio = 0.0)."""
        # A = 4200, R = 0.875
        # N = -4200 * 0.875 * 1.5 = -5512.5 -> sigma_eq = (N / A) / R = (-5512.5 / 4200) / 0.875 = -1.5 MPa
        # Como |-1.5| <= fd_hollow (2.8 MPa), ratio deve ser 0.0 em todo o segmento.
        forces = SectionForces(normal=-5512.5)

        result = CompressionDesignService.design_grouting_demand(
            section=self.section,
            forces=forces,
            masonry_spec=self.masonry_spec,
        )

        self.assertTrue(result.is_feasible)
        self.assertTrue(result.is_slenderness_ok)
        self.assertTrue(result.grout_demand.is_ungrouted)
        self.assertTrue(is_close(result.max_equivalent_compressive_stress, 1.5))
        self.assertTrue(is_zero(result.grout_demand.weighted_average_ratio))
        self.assertTrue(is_close(result.utilization_ratio, 1.5 / 4.9))

    def test_pure_compression_moderate_load_requires_grouting(self) -> None:
        """Compressão pura com tensão entre fd_hollow e fd_grouted calcula a taxa exata de graute."""
        # Tensão desejada sigma_eq = 3.5 MPa (entre fd_hollow=2.8 e fd_grouted=4.9)
        # N = -4200 * 0.875 * 3.5 = -12862.5
        # ratio esperado = (3.5 - 2.8) / (4.9 - 2.8) = 0.7 / 2.1 = 1/3 ~ 0.333333
        forces = SectionForces(normal=-12862.5)

        result = CompressionDesignService.design_grouting_demand(
            section=self.section,
            forces=forces,
            masonry_spec=self.masonry_spec,
        )

        self.assertTrue(result.is_feasible)
        self.assertFalse(result.grout_demand.is_ungrouted)
        self.assertFalse(result.grout_demand.is_fully_grouted)
        self.assertTrue(is_close(result.max_equivalent_compressive_stress, 3.5))
        self.assertTrue(is_close(result.grout_demand.weighted_average_ratio, 1.0 / 3.0))

    def test_flexo_compression_in_plane_with_k_factor(self) -> None:
        """Flexo-compressão no plano da parede com atuação do fator K = 1.5."""
        # A = 4200, R = 0.875, Iyy = 31500000, Wx = 31500000 / 150 = 210000 cm³
        # N = -4200 * 0.875 * 1.0 = -3675 (produz c0/R = -1.0 MPa)
        # Bending My = 210000 * 1.5 * 1.5 = 472500 (produz My / (W * K) = 1.5 MPa na borda comprimida)
        # Na borda esquerda x = -150: sigma_eq = -1.0 - 1.5 = -2.5 MPa (compressão)
        # Na borda direita x = +150: sigma_eq = -1.0 + 1.5 = +0.5 MPa (tração)
        # Linha neutra em x: -1.0 + 1.5 * (x / 150) = 0 -> x = +100 cm
        # Segmento vai de x = -150 (s=0) a x = +150 (s=300).
        # x = +100 corresponde a s = 250 cm.
        # Região comprimida: s in [0, 250] com pico de 2.5 MPa em s=0.
        # Região tracionada: s in [250, 300].
        forces = SectionForces(normal=-3675.0, moment_y=472500.0)

        options = CompressionDesignOptions(k_flexure=1.5, gamma_m=2.0)
        result = CompressionDesignService.design_grouting_demand(
            section=self.section,
            forces=forces,
            masonry_spec=self.masonry_spec,
            options=options,
        )

        self.assertTrue(result.is_feasible)
        self.assertTrue(is_close(result.max_equivalent_compressive_stress, 2.5))
        self.assertTrue(is_close(result.max_equivalent_tensile_stress, 0.5))

        seg_demand = result.grout_demand.segment_demands[0]
        self.assertEqual(len(seg_demand.intervals), 2)

        # Intervalo 1: comprimido [0, 250] cm. Como pico = 2.5 <= fd_hollow (2.8), ratio = 0.0
        inv_comp = seg_demand.intervals[0]
        self.assertTrue(is_close(inv_comp.start_offset, 0.0))
        self.assertTrue(is_close(inv_comp.end_offset, 250.0))
        self.assertTrue(is_close(inv_comp.ratio, 0.0))

        # Intervalo 2: tracionado [250, 300] cm, ratio = 0.0
        inv_tens = seg_demand.intervals[1]
        self.assertTrue(is_close(inv_tens.start_offset, 250.0))
        self.assertTrue(is_close(inv_tens.end_offset, 300.0))
        self.assertTrue(is_close(inv_tens.ratio, 0.0))

    def test_flexo_compression_with_max_interval_length(self) -> None:
        """Subdivisão de trecho comprimido por max_interval_length e gradiente de grauteamento."""
        # Flexo-compressão mais intensa:
        # N = -4200 * 0.875 * 2.0 = -7350 (c0/R = -2.0 MPa)
        # My = 210000 * 1.5 * 2.0 = 630000 (My/(W*K) = 2.0 MPa nas bordas)
        # Borda esquerda (s=0, x=-150): sigma_eq = -2.0 - 2.0 = -4.0 MPa (compressão alta > fd_hollow=2.8)
        # Borda direita (s=300, x=+150): sigma_eq = -2.0 + 2.0 = 0.0 MPa (linha neutra exatamente em s=300)
        # Trecho comprimido: s in [0, 300].
        # Com max_interval_length = 100.0 cm, deve gerar 3 subintervalos de 100 cm:
        # [0, 100], [100, 200], [200, 300].
        forces = SectionForces(normal=-7350.0, moment_y=630000.0)

        options = CompressionDesignOptions(
            k_flexure=1.5,
            gamma_m=2.0,
            max_interval_length=100.0,
        )

        result = CompressionDesignService.design_grouting_demand(
            section=self.section,
            forces=forces,
            masonry_spec=self.masonry_spec,
            options=options,
        )

        self.assertTrue(result.is_feasible)
        seg_demand = result.grout_demand.segment_demands[0]
        self.assertEqual(len(seg_demand.intervals), 3)

        inv1, inv2, inv3 = seg_demand.intervals
        # Subintervalo 1 [0, 100]: sigma varia de -4.0 a -2.6667. Pico = 4.0 MPa > 2.8.
        # ratio1 = (4.0 - 2.8) / 2.1 = 1.2 / 2.1 = 4/7 ~ 0.5714
        self.assertTrue(is_close(inv1.length, 100.0))
        self.assertTrue(is_close(inv1.ratio, 1.2 / 2.1))

        # Subintervalo 2 [100, 200]: sigma varia de -2.6667 a -1.3333. Pico = 2.6667 <= 2.8.
        # ratio2 = 0.0
        self.assertTrue(is_close(inv2.length, 100.0))
        self.assertTrue(is_zero(inv2.ratio))

        # Subintervalo 3 [200, 300]: sigma varia de -1.3333 a 0.0. Pico = 1.3333 <= 2.8.
        # ratio3 = 0.0
        self.assertTrue(is_close(inv3.length, 100.0))
        self.assertTrue(is_zero(inv3.ratio))

    def test_infeasible_when_stress_exceeds_grouted_capacity(self) -> None:
        """Esforço excessivo que supera a capacidade máxima totalmente grauteada (sigma > fd_grouted)."""
        # fd_grouted = 4.9 MPa. Tensão atuante = 6.0 MPa
        # N = -4200 * 0.875 * 6.0 = -22050.0
        forces = SectionForces(normal=-22050.0)

        result = CompressionDesignService.design_grouting_demand(
            section=self.section,
            forces=forces,
            masonry_spec=self.masonry_spec,
        )

        self.assertFalse(result.is_feasible)
        self.assertTrue(result.utilization_ratio > 1.0)
        self.assertTrue(result.grout_demand.is_fully_grouted)

    def test_verify_section_conformance(self) -> None:
        """Verificação de conformidade com SectionGroutDemand fornecida."""
        # Esforço com pico de 3.5 MPa
        forces = SectionForces(normal=-12862.5)

        # 1. Demanda insuficiente (0% de graute): deve reprovar
        demand_empty = SectionGroutDemand.uniform(self.section, ratio=0.0)
        verif_fail = CompressionDesignService.verify_section(
            section=self.section,
            forces=forces,
            masonry_spec=self.masonry_spec,
            grout_demand=demand_empty,
        )
        self.assertFalse(verif_fail.is_verified)
        self.assertFalse(verif_fail.stress_ok)
        self.assertTrue(verif_fail.slenderness_ok)

        # 2. Demanda adequada (100% ou 50% de graute): deve aprovar
        demand_ok = SectionGroutDemand.uniform(self.section, ratio=0.50)
        verif_pass = CompressionDesignService.verify_section(
            section=self.section,
            forces=forces,
            masonry_spec=self.masonry_spec,
            grout_demand=demand_ok,
        )
        self.assertTrue(verif_pass.is_verified)
        self.assertTrue(verif_pass.stress_ok)
        self.assertTrue(verif_pass.slenderness_ok)

    def test_options_validations(self) -> None:
        """Validações de consistência em CompressionDesignOptions."""
        with self.assertRaises(ValueError):
            CompressionDesignOptions(gamma_m=0.0)
        with self.assertRaises(ValueError):
            CompressionDesignOptions(k_flexure=-1.0)
        with self.assertRaises(ValueError):
            CompressionDesignOptions(max_slenderness=0.0)
        with self.assertRaises(ValueError):
            CompressionDesignOptions(max_interval_length=-10.0)


if __name__ == "__main__":
    unittest.main()
