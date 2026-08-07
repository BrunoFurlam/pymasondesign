from __future__ import annotations

import math
import unittest
from pymasondesign.geometry import Point2D
from pymasondesign.mechanics import NormalStressPlane


class TestNormalStressPlane(unittest.TestCase):
    def test_direct_coefficients(self):
        # Plano de tensões: σ(x, y) = 10.0 + 2.0*x + 3.0*y
        plane = NormalStressPlane(c0=10.0, cx=2.0, cy=3.0)

        self.assertAlmostEqual(plane.c0, 10.0)
        self.assertAlmostEqual(plane.cx, 2.0)
        self.assertAlmostEqual(plane.cy, 3.0)

        # No CG (0, 0)
        self.assertAlmostEqual(plane.stress_at(0.0, 0.0), 10.0)

        # Em um ponto qualquer (x=1.0, y=2.0)
        self.assertAlmostEqual(plane.stress_at(1.0, 2.0), 10.0 + 2.0 * 1.0 + 3.0 * 2.0)

        # Usando Point2D
        p = Point2D(1.0, 2.0)
        self.assertAlmostEqual(plane.stress_at_point(p), 18.0)

    def test_pure_axial_compression(self):
        # Tensão uniforme de compressão: c0 = -1.0, cx = 0, cy = 0
        plane = NormalStressPlane(c0=-1.0, cx=0.0, cy=0.0)

        self.assertAlmostEqual(plane.stress_at(0.0, 0.0), -1.0)
        self.assertAlmostEqual(plane.stress_at(7.0, 19.5), -1.0)
        self.assertAlmostEqual(plane.stress_at(-7.0, -19.5), -1.0)
        self.assertEqual(plane.neutral_axis_distance, float("inf"))

    def test_pure_bending(self):
        # Gradiente puro em Y: c0 = 0, cx = 0, cy = 1.0
        plane = NormalStressPlane(c0=0.0, cx=0.0, cy=1.0)

        self.assertAlmostEqual(plane.stress_at(0.0, 19.5), 19.5)
        self.assertAlmostEqual(plane.stress_at(0.0, -19.5), -19.5)
        self.assertAlmostEqual(plane.stress_at(0.0, 0.0), 0.0)
        self.assertAlmostEqual(plane.neutral_axis_distance, 0.0)
        self.assertAlmostEqual(plane.neutral_axis_angle, 0.0)

    def test_biaxial_bending_neutral_axis(self):
        # c0 = -2.0, cx = 1.0, cy = 2.0
        plane = NormalStressPlane(c0=-2.0, cx=1.0, cy=2.0)

        # Distância da LN: |-2.0| / sqrt(1^2 + 2^2) = 2 / sqrt(5)
        expected_dist = 2.0 / math.sqrt(5.0)
        self.assertAlmostEqual(plane.neutral_axis_distance, expected_dist)

        # Ângulo da LN: atan2(-1.0, 2.0)
        self.assertAlmostEqual(plane.neutral_axis_angle, math.atan2(-1.0, 2.0))


if __name__ == "__main__":
    unittest.main()
