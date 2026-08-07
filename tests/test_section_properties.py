from __future__ import annotations

import math
import unittest
from pymasondesign.geometry import (
    Point2D,
    BoundingBox,
    RectangularSection,
    CompositeSection,
)


class TestGeometryPointAndBounds(unittest.TestCase):
    def test_point_operations(self):
        p1 = Point2D(0.0, 0.0)
        p2 = Point2D(3.0, 4.0)
        self.assertAlmostEqual(p1.distance_to(p2), 5.0)

        p3 = p1.translated(2.5, -1.0)
        self.assertAlmostEqual(p3.x, 2.5)
        self.assertAlmostEqual(p3.y, -1.0)

    def test_bounding_box(self):
        box = BoundingBox(xmin=0.0, xmax=10.0, ymin=2.0, ymax=6.0)
        self.assertAlmostEqual(box.width, 10.0)
        self.assertAlmostEqual(box.height, 4.0)
        self.assertAlmostEqual(box.center.x, 5.0)
        self.assertAlmostEqual(box.center.y, 4.0)
        self.assertTrue(box.contains_point(Point2D(5.0, 3.0)))
        self.assertFalse(box.contains_point(Point2D(11.0, 3.0)))

        with self.assertRaises(ValueError):
            BoundingBox(xmin=10.0, xmax=2.0, ymin=0.0, ymax=1.0)


class TestRectangularSection(unittest.TestCase):
    def test_solid_rectangle_properties(self):
        # Dimensões de um elemento típico: largura b = 14 cm, altura h = 39 cm
        b = 14.0
        h = 39.0
        rect = RectangularSection(width=b, height=h)
        props = rect.compute_properties()

        # Área
        expected_area = b * h
        self.assertAlmostEqual(props.area, expected_area)

        # Centro de gravidade
        self.assertAlmostEqual(props.cg.x, b / 2.0)
        self.assertAlmostEqual(props.cg.y, h / 2.0)

        # Momentos de inércia
        expected_ixx = (b * (h**3)) / 12.0
        expected_iyy = (h * (b**3)) / 12.0
        self.assertAlmostEqual(props.ixx, expected_ixx)
        self.assertAlmostEqual(props.iyy, expected_iyy)
        self.assertAlmostEqual(props.ixy, 0.0)

        # Raios de giração (r = h / sqrt(12))
        self.assertAlmostEqual(props.rx, h / math.sqrt(12.0))
        self.assertAlmostEqual(props.ry, b / math.sqrt(12.0))

        # Módulos de resistência (W = b * h^2 / 6)
        expected_wx = (b * (h**2)) / 6.0
        expected_wy = (h * (b**2)) / 6.0
        self.assertAlmostEqual(props.wx_top, expected_wx)
        self.assertAlmostEqual(props.wx_bot, expected_wx)
        self.assertAlmostEqual(props.wx_min, expected_wx)
        self.assertAlmostEqual(props.wy_right, expected_wy)
        self.assertAlmostEqual(props.wy_left, expected_wy)
        self.assertAlmostEqual(props.wy_min, expected_wy)

        # Bounding box
        self.assertAlmostEqual(props.x_min, 0.0)
        self.assertAlmostEqual(props.x_max, b)
        self.assertAlmostEqual(props.y_min, 0.0)
        self.assertAlmostEqual(props.y_max, h)


class TestCompositeSection(unittest.TestCase):
    def test_hollow_block_section(self):
        # Bloco de 39x14 cm com 2 furos de 12x8 cm
        outer = RectangularSection(width=39.0, height=14.0)
        hole1 = RectangularSection(width=12.0, height=8.0, origin=Point2D(4.0, 3.0))
        hole2 = RectangularSection(width=12.0, height=8.0, origin=Point2D(23.0, 3.0))

        block = CompositeSection()
        block.add_solid(outer)
        block.add_void(hole1)
        block.add_void(hole2)

        props = block.compute_properties()

        # Área líquida: 39*14 - 2*(12*8) = 546 - 192 = 354 cm²
        self.assertAlmostEqual(props.area, 354.0)

        # Por simetria, CG deve ser no ponto médio (19.5, 7.0)
        self.assertAlmostEqual(props.cg.x, 19.5)
        self.assertAlmostEqual(props.cg.y, 7.0)

        # Inércia analítica Ixx = Ixx_ext - 2 * Ixx_furos (pois furos são simétricos no eixo Y)
        ixx_outer = (39.0 * (14.0**3)) / 12.0
        ixx_hole = (12.0 * (8.0**3)) / 12.0
        expected_ixx = ixx_outer - 2.0 * ixx_hole
        self.assertAlmostEqual(props.ixx, expected_ixx)

        # Bounds
        self.assertAlmostEqual(props.x_min, 0.0)
        self.assertAlmostEqual(props.x_max, 39.0)
        self.assertAlmostEqual(props.y_min, 0.0)
        self.assertAlmostEqual(props.y_max, 14.0)

    def test_l_shaped_wall_steiner(self):
        # Parede em L: Alma (14x100 cm) + Aba (100x14 cm)
        # Alma: x in [0, 14], y in [0, 100]
        # Aba:  x in [14, 114], y in [0, 14]
        web = RectangularSection(width=14.0, height=100.0, origin=Point2D(0.0, 0.0))
        flange = RectangularSection(width=100.0, height=14.0, origin=Point2D(14.0, 0.0))

        wall = CompositeSection()
        wall.add_solid(web)
        wall.add_solid(flange)

        props = wall.compute_properties()
        a_web = 14.0 * 100.0
        a_flange = 100.0 * 14.0
        total_a = a_web + a_flange
        self.assertAlmostEqual(props.area, total_a)

        # CG manual
        expected_xcg = (a_web * 7.0 + a_flange * (14.0 + 50.0)) / total_a
        expected_ycg = (a_web * 50.0 + a_flange * 7.0) / total_a
        self.assertAlmostEqual(props.cg.x, expected_xcg)
        self.assertAlmostEqual(props.cg.y, expected_ycg)

        # Bounds
        self.assertAlmostEqual(props.x_min, 0.0)
        self.assertAlmostEqual(props.x_max, 114.0)
        self.assertAlmostEqual(props.y_min, 0.0)
        self.assertAlmostEqual(props.y_max, 100.0)


if __name__ == "__main__":
    unittest.main()
