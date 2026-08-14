from __future__ import annotations

import math
import unittest
from pymasondesign.geometry import Point2D, Vector2D


class TestVector2D(unittest.TestCase):
    def test_magnitude_and_normalization(self):
        v = Vector2D(3.0, 4.0)
        self.assertAlmostEqual(v.magnitude, 5.0)
        self.assertAlmostEqual(v.magnitude_squared, 25.0)

        u = v.normalized()
        self.assertAlmostEqual(u.x, 0.6)
        self.assertAlmostEqual(u.y, 0.8)
        self.assertAlmostEqual(u.magnitude, 1.0)

        with self.assertRaises(ZeroDivisionError):
            Vector2D(0.0, 0.0).normalized()

    def test_dot_and_cross(self):
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(0.0, 1.0)

        # Vetores ortogonais
        self.assertAlmostEqual(v1.dot(v2), 0.0)
        self.assertAlmostEqual(v1.cross(v2), 1.0)
        self.assertAlmostEqual(v2.cross(v1), -1.0)

    def test_perpendicular_and_rotation(self):
        v = Vector2D(2.0, 0.0)
        perp = v.perpendicular()
        self.assertAlmostEqual(perp.x, 0.0)
        self.assertAlmostEqual(perp.y, 2.0)

        rot45 = v.rotated(math.pi / 4.0)
        self.assertAlmostEqual(rot45.x, math.sqrt(2.0))
        self.assertAlmostEqual(rot45.y, math.sqrt(2.0))

    def test_reflection(self):
        # Vetor incide a 45 graus (1, -1) e reflete na normal vertical (0, 1) -> (1, 1)
        ray = Vector2D(1.0, -1.0)
        normal = Vector2D(0.0, 1.0)
        reflected = ray.reflected(normal)
        self.assertAlmostEqual(reflected.x, 1.0)
        self.assertAlmostEqual(reflected.y, 1.0)

    def test_arithmetic(self):
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, -1.0)

        v_sum = v1 + v2
        self.assertAlmostEqual(v_sum.x, 4.0)
        self.assertAlmostEqual(v_sum.y, 1.0)

        v_sub = v1 - v2
        self.assertAlmostEqual(v_sub.x, -2.0)
        self.assertAlmostEqual(v_sub.y, 3.0)

        v_mul = v1 * 2.5
        self.assertAlmostEqual(v_mul.x, 2.5)
        self.assertAlmostEqual(v_mul.y, 5.0)

        v_neg = -v1
        self.assertAlmostEqual(v_neg.x, -1.0)
        self.assertAlmostEqual(v_neg.y, -2.0)

    def test_point_from_coords(self):
        p = Point2D.from_coords((3.5, -4.2))
        self.assertIsInstance(p, Point2D)
        self.assertAlmostEqual(p.x, 3.5)
        self.assertAlmostEqual(p.y, -4.2)

    def test_point_vector_to(self):
        p1 = Point2D(2.0, 3.0)
        p2 = Point2D(5.0, 7.0)
        v = p1.vector_to(p2)
        self.assertIsInstance(v, Vector2D)
        self.assertAlmostEqual(v.x, 3.0)
        self.assertAlmostEqual(v.y, 4.0)
        self.assertAlmostEqual(v.magnitude, 5.0)

        # Vetor nulo entre pontos iguais
        v_null = p1.vector_to(Point2D(2.0, 3.0))
        self.assertAlmostEqual(v_null.x, 0.0)
        self.assertAlmostEqual(v_null.y, 0.0)

    def test_point_moved_by(self):
        p = Point2D(2.0, 3.0)
        v = Vector2D(4.0, -1.0)

        # moved_by
        p_moved = p.moved_by(v)
        self.assertAlmostEqual(p_moved.x, 6.0)
        self.assertAlmostEqual(p_moved.y, 2.0)

        # Operador + (Point2D + Vector2D)
        p_add = p + v
        self.assertAlmostEqual(p_add.x, 6.0)
        self.assertAlmostEqual(p_add.y, 2.0)

        # Operador - (Point2D - Vector2D)
        p_sub_v = p - v
        self.assertAlmostEqual(p_sub_v.x, -2.0)
        self.assertAlmostEqual(p_sub_v.y, 4.0)

        # Operador - (Point2D - Point2D -> Vector2D)
        p_sub_p = p_moved - p
        self.assertIsInstance(p_sub_p, Vector2D)
        self.assertAlmostEqual(p_sub_p.x, 4.0)
        self.assertAlmostEqual(p_sub_p.y, -1.0)


if __name__ == "__main__":
    unittest.main()


