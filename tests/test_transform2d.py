from __future__ import annotations

import math
import unittest
from pymasondesign.geometry import Point2D, Vector2D, Transform2D
from pymasondesign.mechanics import NormalStressPlane


class TestTransform2D(unittest.TestCase):
    def test_identity(self):
        t = Transform2D.identity()
        p = Point2D(3.0, 4.0)
        transformed = t.apply_point(p)
        self.assertAlmostEqual(transformed.x, 3.0)
        self.assertAlmostEqual(transformed.y, 4.0)
        self.assertFalse(t.is_reflection)
        self.assertTrue(t.is_orthogonal)

    def test_translation(self):
        t = Transform2D.translation(dx=10.0, dy=-5.0)
        p_local = Point2D(2.0, 3.0)
        p_global = t.apply_point(p_local)
        self.assertAlmostEqual(p_global.x, 12.0)
        self.assertAlmostEqual(p_global.y, -2.0)

        # Inversa
        p_back = t.apply_inverse_point(p_global)
        self.assertAlmostEqual(p_back.x, 2.0)
        self.assertAlmostEqual(p_back.y, 3.0)

    def test_rotation_90_degrees(self):
        angle = math.pi / 2.0  # 90 graus
        t = Transform2D.rotation(angle)
        p_local = Point2D(1.0, 0.0)
        p_global = t.apply_point(p_local)
        self.assertAlmostEqual(p_global.x, 0.0)
        self.assertAlmostEqual(p_global.y, 1.0)
        self.assertFalse(t.is_reflection)

    def test_mirror_x(self):
        # Espelhamento em relação à reta horizontal y = 0 (inverte eixo Y)
        t = Transform2D.mirror_x(origin_y=0.0)
        self.assertTrue(t.is_reflection)
        self.assertAlmostEqual(t.determinant, -1.0)

        p_local = Point2D(3.0, 4.0)
        p_global = t.apply_point(p_local)
        self.assertAlmostEqual(p_global.x, 3.0)
        self.assertAlmostEqual(p_global.y, -4.0)

        p_back = t.apply_inverse_point(p_global)
        self.assertAlmostEqual(p_back.x, 3.0)
        self.assertAlmostEqual(p_back.y, 4.0)

    def test_mirror_y(self):
        # Espelhamento em relação à reta vertical x = 0 (inverte eixo X)
        t = Transform2D.mirror_y(origin_x=0.0)
        self.assertTrue(t.is_reflection)
        self.assertAlmostEqual(t.determinant, -1.0)

        p_local = Point2D(3.0, 4.0)
        p_global = t.apply_point(p_local)
        self.assertAlmostEqual(p_global.x, -3.0)
        self.assertAlmostEqual(p_global.y, 4.0)

    def test_stress_plane_translation(self):
        # Plano em S1: σ(x1, y1) = 10.0 + 2.0*x1 + 3.0*y1
        plane1 = NormalStressPlane(c0=10.0, cx=2.0, cy=3.0)

        # Nova base S2 com origem em (5.0, 2.0) em S1
        plane2 = plane1.transform(Transform2D.translation(dx=5.0, dy=2.0))

        # Tensão na nova origem (0, 0) de S2: 10.0 + 2.0*5.0 + 3.0*2.0 = 26.0
        self.assertAlmostEqual(plane2.c0, 26.0)
        self.assertAlmostEqual(plane2.cx, 2.0)
        self.assertAlmostEqual(plane2.cy, 3.0)

        # Ponto P em S2 com coordenadas (1.0, 1.0) -> em S1 é (6.0, 3.0)
        self.assertAlmostEqual(plane2.stress_at(1.0, 1.0), plane1.stress_at(6.0, 3.0))

    def test_stress_plane_rotation(self):
        # Plano em S1: σ(x1, y1) = 0.0 + 2.0*x1 + 0.0*y1 (gradiente puro em X1)
        plane1 = NormalStressPlane(c0=0.0, cx=2.0, cy=0.0)

        # Rotaciona o sistema S2 em 90 graus (theta = pi/2)
        plane2 = plane1.transform(Transform2D.rotation(math.pi / 2.0))

        self.assertAlmostEqual(plane2.c0, 0.0)
        self.assertAlmostEqual(plane2.cx, 0.0)
        self.assertAlmostEqual(plane2.cy, -2.0)

        # Ponto (x2=0, y2=1) em S2 corresponde a (x1=-1, y1=0) em S1
        self.assertAlmostEqual(plane2.stress_at(0.0, 1.0), -2.0)
        self.assertAlmostEqual(plane1.stress_at(-1.0, 0.0), -2.0)

    def test_stress_plane_mirroring(self):
        # Plano original: σ(x, y) = 15.0 + 4.0*x - 6.0*y
        plane = NormalStressPlane(c0=15.0, cx=4.0, cy=-6.0)

        # Espelhamento no eixo X (inverte Y)
        mirrored_x = plane.transform(Transform2D.mirror_x())
        self.assertAlmostEqual(mirrored_x.c0, 15.0)
        self.assertAlmostEqual(mirrored_x.cx, 4.0)
        self.assertAlmostEqual(mirrored_x.cy, 6.0)

        # Ponto local (2, 3) no sistema espelhado corresponde ao ponto global (2, -3)
        self.assertAlmostEqual(mirrored_x.stress_at(2.0, 3.0), plane.stress_at(2.0, -3.0))

        # Espelhamento no eixo Y (inverte X)
        mirrored_y = plane.transform(Transform2D.mirror_y())
        self.assertAlmostEqual(mirrored_y.c0, 15.0)
        self.assertAlmostEqual(mirrored_y.cx, -4.0)
        self.assertAlmostEqual(mirrored_y.cy, -6.0)

        # Ponto local (2, 3) no sistema espelhado corresponde ao ponto global (-2, 3)
        self.assertAlmostEqual(mirrored_y.stress_at(2.0, 3.0), plane.stress_at(-2.0, 3.0))


if __name__ == "__main__":
    unittest.main()
