from __future__ import annotations

import unittest
from pymasondesign.sections import RectangularSection, PolygonSection
from pymasondesign.mechanics import (
    SectionForces,
    StressRegime,
    MechanicsService,
)


class TestMechanicsService(unittest.TestCase):
    def setUp(self):
        # Retângulo padrão: b = 14 cm, h = 39 cm (A = 546, Ixx = 69205.5, Iyy = 8918.0)
        self.rect = RectangularSection(width=14.0, height=39.0)
        self.props = self.rect.compute_properties()

    def test_calculate_normal_stress_plane(self):
        forces = SectionForces(
            normal=-546.0,
            moment_x=34602.75,
            moment_y=4459.0,
        )
        plane = MechanicsService.calculate_normal_stress_plane(forces, self.props)

        self.assertAlmostEqual(plane.c0, -1.0)
        self.assertAlmostEqual(plane.cx, 0.5)
        self.assertAlmostEqual(plane.cy, 0.5)

        # Tensão no canto (+7, +19.5): -1.0 + 3.5 + 9.75 = 12.25
        self.assertAlmostEqual(plane.stress_at(7.0, 19.5), 12.25)
        # Tensão no canto (-7, -19.5): -1.0 - 3.5 - 9.75 = -14.25
        self.assertAlmostEqual(plane.stress_at(-7.0, -19.5), -14.25)

    def test_calculate_eccentricities(self):
        forces = SectionForces(normal=-100.0, moment_x=200.0, moment_y=150.0)
        ex, ey = MechanicsService.calculate_eccentricities(forces)

        self.assertAlmostEqual(ex, 1.5)  # |150| / 100
        self.assertAlmostEqual(ey, 2.0)  # |200| / 100

        # Caso com esforço normal nulo
        forces_zero_n = SectionForces(normal=0.0, moment_x=100.0)
        ex_inf, ey_inf = MechanicsService.calculate_eccentricities(forces_zero_n)
        self.assertEqual(ex_inf, 0.0)
        self.assertEqual(ey_inf, float("inf"))

    def test_calculate_extreme_stresses(self):
        forces = SectionForces(
            normal=-546.0,
            moment_x=34602.75,
            moment_y=4459.0,
        )
        plane = MechanicsService.calculate_normal_stress_plane(forces, self.props)
        sigma_min, sigma_max = MechanicsService.calculate_extreme_stresses(plane, self.props)

        self.assertAlmostEqual(sigma_min, -14.25)
        self.assertAlmostEqual(sigma_max, 12.25)

    def test_classify_stress_regimes(self):
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces()),
            StressRegime.NO_LOAD,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(normal=-100.0)),
            StressRegime.PURE_COMPRESSION,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(normal=100.0)),
            StressRegime.PURE_TENSION,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(moment_x=50.0)),
            StressRegime.PURE_BENDING_X,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(moment_y=50.0)),
            StressRegime.PURE_BENDING_Y,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(moment_x=50.0, moment_y=50.0)),
            StressRegime.PURE_BENDING_XY,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(normal=-100.0, moment_x=50.0)),
            StressRegime.FLEXO_COMPRESSION_X,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(normal=-100.0, moment_y=50.0)),
            StressRegime.FLEXO_COMPRESSION_Y,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(normal=-100.0, moment_x=50.0, moment_y=50.0)),
            StressRegime.FLEXO_COMPRESSION_XY,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(normal=100.0, moment_x=50.0)),
            StressRegime.FLEXO_TENSION_X,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(normal=100.0, moment_y=50.0)),
            StressRegime.FLEXO_TENSION_Y,
        )
        self.assertEqual(
            MechanicsService.classify_stress_regime(SectionForces(normal=100.0, moment_x=50.0, moment_y=50.0)),
            StressRegime.FLEXO_TENSION_XY,
        )

    def test_integrate_normal_stress_on_polygon(self):
        from pymasondesign.geometry import Point2D
        from pymasondesign.sections import PolygonSection
        from pymasondesign.mechanics import NormalStressPlane

        # Triângulo (0,0), (6,0), (0,4) -> Área = 12, Cg = (2.0, 1.3333333333333333)
        triangle = PolygonSection.from_vertices([
            Point2D(0.0, 0.0),
            Point2D(6.0, 0.0),
            Point2D(0.0, 4.0),
        ])

        # Plano de tensões: σ(x, y) = 10.0 + 2.0*x + 3.0*y
        plane = NormalStressPlane(c0=10.0, cx=2.0, cy=3.0)

        # Tensão no CG do triângulo: σ(2, 4/3) = 10.0 + 2.0*2.0 + 3.0*(4/3) = 10 + 4 + 4 = 18.0
        # Força acumulada N = Área * σ(Cg) = 12 * 18.0 = 216.0
        force = MechanicsService.integrate_normal_stress(plane, triangle)
        self.assertAlmostEqual(force, 216.0)

        # Teste com alias calculate_accumulated_force
        force_alias = MechanicsService.calculate_accumulated_force(plane, triangle)
        self.assertAlmostEqual(force_alias, 216.0)


if __name__ == "__main__":
    unittest.main()
