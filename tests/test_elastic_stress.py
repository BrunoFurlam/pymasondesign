from __future__ import annotations

import math
import unittest
from pymasondesign.geometry import (
    Point2D,
    RectangularSection,
)
from pymasondesign.mechanics import ElasticStressState


class TestElasticStressState(unittest.TestCase):
    def test_direct_coefficients_initialization(self):
        # Inicialização direta com parâmetros do plano c0, cx, cy
        # sigma(x, y) = 10.0 + 2.0*x + 3.0*y
        stress_state = ElasticStressState(c0=10.0, cx=2.0, cy=3.0)

        self.assertAlmostEqual(stress_state.c0, 10.0)
        self.assertAlmostEqual(stress_state.cx, 2.0)
        self.assertAlmostEqual(stress_state.cy, 3.0)

        # No CG (0, 0)
        self.assertAlmostEqual(stress_state.stress_at(0.0, 0.0), 10.0)
        # No ponto (x=1.0, y=2.0)
        self.assertAlmostEqual(stress_state.stress_at(1.0, 2.0), 10.0 + 2.0*1.0 + 3.0*2.0)
        # Usando Point2D
        p = Point2D(1.0, 2.0)
        self.assertAlmostEqual(stress_state.stress_at_point(p), 18.0)

    def test_from_forces_pure_normal(self):
        # Compressão pura: N = -546 kN, A = 546 cm² -> c0 = -1.0
        stress_state = ElasticStressState.from_forces(
            normal_force=-546.0,
            area=546.0,
            ixx=69205.5,
            iyy=8918.0,
        )

        self.assertAlmostEqual(stress_state.c0, -1.0)
        self.assertAlmostEqual(stress_state.cx, 0.0)
        self.assertAlmostEqual(stress_state.cy, 0.0)
        self.assertAlmostEqual(stress_state.stress_at(0.0, 0.0), -1.0)
        self.assertAlmostEqual(stress_state.stress_at(7.0, 19.5), -1.0)

    def test_from_forces_pure_bending(self):
        # Mx = 69205.5 kN.cm, Ixx = 69205.5 cm4 -> cy = 1.0
        stress_state = ElasticStressState.from_forces(
            moment_x=69205.5,
            area=546.0,
            ixx=69205.5,
            iyy=8918.0,
        )

        self.assertAlmostEqual(stress_state.c0, 0.0)
        self.assertAlmostEqual(stress_state.cy, 1.0)
        self.assertAlmostEqual(stress_state.cx, 0.0)

        # No topo (y = +19.5) e na base (y = -19.5)
        self.assertAlmostEqual(stress_state.stress_at(0.0, 19.5), 19.5)
        self.assertAlmostEqual(stress_state.stress_at(0.0, -19.5), -19.5)
        self.assertAlmostEqual(stress_state.neutral_axis_distance, 0.0)

    def test_from_forces_combined_biaxial(self):
        stress_state = ElasticStressState.from_forces(
            normal_force=-546.0,
            moment_x=34602.75,
            moment_y=4459.0,
            area=546.0,
            ixx=69205.5,
            iyy=8918.0,
        )

        # c0 = -1.0, cx = 0.5, cy = 0.5
        # sigma(7, 19.5) = -1.0 + 3.5 + 9.75 = 12.25
        self.assertAlmostEqual(stress_state.stress_at(7.0, 19.5), 12.25)
        self.assertAlmostEqual(stress_state.stress_at(-7.0, -19.5), -14.25)

    def test_from_forces_unsymmetric_ixy(self):
        stress_state = ElasticStressState.from_forces(
            normal_force=100.0,
            moment_x=4600.0,
            moment_y=0.0,
            area=100.0,
            ixx=1000.0,
            iyy=500.0,
            ixy=200.0,
        )
        self.assertAlmostEqual(stress_state.c0, 1.0)
        self.assertAlmostEqual(stress_state.cx, -2.0)
        self.assertAlmostEqual(stress_state.cy, 5.0)
        self.assertAlmostEqual(stress_state.stress_at(1.0, 2.0), 9.0)


if __name__ == "__main__":
    unittest.main()
