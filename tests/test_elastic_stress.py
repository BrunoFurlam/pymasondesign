from __future__ import annotations

import math
import unittest
from pymasondesign.geometry import (
    Point2D,
    RectangularSection,
    CompositeSection,
    SectionProperties,
    BoundingBox,
)
from pymasondesign.mechanics import ElasticStressState


class TestElasticStressState(unittest.TestCase):
    def setUp(self):
        # Seção retangular de 14x39 cm (largura b = 14 cm, altura h = 39 cm)
        self.rect = RectangularSection(width=14.0, height=39.0)
        self.props = self.rect.compute_properties()

    def test_pure_normal_stress(self):
        # Esforço normal de compressão N = -546 kN em seção de área A = 546 cm²
        # Tensão esperada em qualquer ponto: -546 / 546 = -1.0 kN/cm²
        stress_state = self.props.create_elastic_stress(normal_force=-546.0)

        self.assertAlmostEqual(stress_state.c0, -1.0)
        self.assertAlmostEqual(stress_state.cx, 0.0)
        self.assertAlmostEqual(stress_state.cy, 0.0)

        # Em qualquer coordenada relativa ao CG (0, 0)
        self.assertAlmostEqual(stress_state.stress_at(0.0, 0.0), -1.0)
        self.assertAlmostEqual(stress_state.stress_at(7.0, 19.5), -1.0)
        self.assertAlmostEqual(stress_state.stress_at(-7.0, -19.5), -1.0)

    def test_pure_bending_x(self):
        # Momento Mx = 69205.5 kN.cm, Ixx = 69205.5 cm4
        # Gradiente cy = Mx / Ixx = 1.0 kN/cm3
        stress_state = self.props.create_elastic_stress(moment_x=69205.5)

        self.assertAlmostEqual(stress_state.c0, 0.0)
        self.assertAlmostEqual(stress_state.cy, 1.0)
        self.assertAlmostEqual(stress_state.cx, 0.0)

        # No topo (y = +19.5) e na base (y = -19.5) em relação ao CG (0, 0)
        self.assertAlmostEqual(stress_state.stress_at(0.0, 19.5), 19.5)
        self.assertAlmostEqual(stress_state.stress_at(0.0, -19.5), -19.5)
        self.assertAlmostEqual(stress_state.stress_at(0.0, 0.0), 0.0)

        # Linha neutra deve estar no baricentro (distância = 0)
        self.assertAlmostEqual(stress_state.neutral_axis_distance, 0.0)
        self.assertAlmostEqual(stress_state.neutral_axis_angle, 0.0)

    def test_pure_bending_y(self):
        # Momento My = 8918.0 kN.cm, Iyy = 8918.0 cm4
        # Gradiente cx = My / Iyy = 1.0 kN/cm3
        stress_state = self.props.create_elastic_stress(moment_y=8918.0)

        self.assertAlmostEqual(stress_state.c0, 0.0)
        self.assertAlmostEqual(stress_state.cx, 1.0)
        self.assertAlmostEqual(stress_state.cy, 0.0)

        # Na borda direita (x = +7.0) e borda esquerda (x = -7.0)
        self.assertAlmostEqual(stress_state.stress_at(7.0, 0.0), 7.0)
        self.assertAlmostEqual(stress_state.stress_at(-7.0, 0.0), -7.0)

    def test_combined_biaxial_flexocompression(self):
        # N = -546 kN (sigma_N = -1.0)
        # Mx = 34602.75 kN.cm (sigma_Mx no topo y=19.5: 34602.75 * 19.5 / 69205.5 = +9.75)
        # My = 4459.0 kN.cm (sigma_My na borda direita x=7.0: 4459.0 * 7.0 / 8918.0 = +3.5)
        stress_state = self.props.create_elastic_stress(
            normal_force=-546.0,
            moment_x=34602.75,
            moment_y=4459.0,
        )

        # Ponto (x=+7.0, y=+19.5) em relação ao CG (0, 0):
        # sigma = -1.0 + (0.5 * 7.0) + (0.5 * 19.5) = -1.0 + 3.5 + 9.75 = 12.25
        self.assertAlmostEqual(stress_state.stress_at(7.0, 19.5), 12.25)

        # Ponto (x=-7.0, y=-19.5):
        # sigma = -1.0 - 3.5 - 9.75 = -14.25
        self.assertAlmostEqual(stress_state.stress_at(-7.0, -19.5), -14.25)

        # Ponto usando Point2D
        p = Point2D(7.0, 19.5)
        self.assertAlmostEqual(stress_state.stress_at_point(p), 12.25)

    def test_unsymmetric_section_with_ixy(self):
        # Seção com produto de inércia Ixy != 0
        props = SectionProperties(
            area=100.0,
            ixx=1000.0,
            iyy=500.0,
            ixy=200.0,
            cg=Point2D(0.0, 0.0),
            bounds=BoundingBox(-10.0, 10.0, -10.0, 10.0),
        )
        # D = 1000 * 500 - 200^2 = 500000 - 40000 = 460000
        # N = 100 -> c0 = 1.0
        # Mx = 4600, My = 0
        # cx = (-4600 * 200) / 460000 = -2.0
        # cy = (4600 * 500) / 460000 = +5.0
        stress_state = props.create_elastic_stress(normal_force=100.0, moment_x=4600.0, moment_y=0.0)

        self.assertAlmostEqual(stress_state.c0, 1.0)
        self.assertAlmostEqual(stress_state.cx, -2.0)
        self.assertAlmostEqual(stress_state.cy, 5.0)

        # sigma(x=1.0, y=2.0) = 1.0 - 2.0*(1.0) + 5.0*(2.0) = 9.0
        self.assertAlmostEqual(stress_state.stress_at(1.0, 2.0), 9.0)


if __name__ == "__main__":
    unittest.main()
