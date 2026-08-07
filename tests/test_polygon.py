from __future__ import annotations

import math
import unittest
from pymasondesign.geometry import Point2D, Polygon, Transform2D
from pymasondesign.sections import PolygonSection, RectangularSection


class TestPolygonAndPolygonSection(unittest.TestCase):
    def test_polygon_pure_geometry(self):
        poly = Polygon.from_coords([(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)])
        self.assertAlmostEqual(poly.area, 12.0)
        self.assertAlmostEqual(poly.perimeter, 14.0)
        self.assertAlmostEqual(poly.centroid.x, 2.0)
        self.assertAlmostEqual(poly.centroid.y, 1.5)
        self.assertTrue(poly.contains_point(Point2D(2.0, 1.5)))
        self.assertFalse(poly.contains_point(Point2D(5.0, 1.5)))

        # Translação do polígono
        translated = poly.translated(dx=10.0, dy=5.0)
        self.assertAlmostEqual(translated.centroid.x, 12.0)
        self.assertAlmostEqual(translated.centroid.y, 6.5)

    def test_triangle_properties(self):
        # Triângulo retângulo: (0,0), (6,0), (0,4)
        # Base b = 6, Altura h = 4
        # Área = 6*4 / 2 = 12
        # Cg = (b/3, h/3) = (2.0, 4/3)
        # Ixx_cg = b*h^3 / 36 = 6 * 64 / 36 = 10.666666666666666
        # Iyy_cg = h*b^3 / 36 = 4 * 216 / 36 = 24.0
        # Ixy_cg = - b^2 * h^2 / 72 = - 36 * 16 / 72 = -8.0
        vertices = [
            Point2D(0.0, 0.0),
            Point2D(6.0, 0.0),
            Point2D(0.0, 4.0),
        ]
        poly_sec = PolygonSection.from_vertices(vertices)
        props = poly_sec.compute_properties()

        self.assertAlmostEqual(props.area, 12.0)
        self.assertAlmostEqual(props.cg.x, 2.0)
        self.assertAlmostEqual(props.cg.y, 4.0 / 3.0)
        self.assertAlmostEqual(props.ixx, 6.0 * (4.0**3) / 36.0)
        self.assertAlmostEqual(props.iyy, 4.0 * (6.0**3) / 36.0)
        self.assertAlmostEqual(props.ixy, - (6.0**2 * 4.0**2) / 72.0)

    def test_polygon_rectangle_matches_analytical(self):
        b, h = 14.0, 39.0
        coords = [(0.0, 0.0), (b, 0.0), (b, h), (0.0, h)]
        poly_sec = PolygonSection.from_coords(coords)
        rect = RectangularSection(width=b, height=h)

        props_poly = poly_sec.compute_properties()
        props_rect = rect.compute_properties()

        self.assertAlmostEqual(props_poly.area, props_rect.area)
        self.assertAlmostEqual(props_poly.cg.x, props_rect.cg.x)
        self.assertAlmostEqual(props_poly.cg.y, props_rect.cg.y)
        self.assertAlmostEqual(props_poly.ixx, props_rect.ixx)
        self.assertAlmostEqual(props_poly.iyy, props_rect.iyy)
        self.assertAlmostEqual(props_poly.ixy, props_rect.ixy)

    def test_invalid_polygon(self):
        with self.assertRaises(ValueError):
            Polygon([Point2D(0, 0), Point2D(1, 1)])

        with self.assertRaises(ValueError):
            Polygon.from_coords([(0, 0), (1, 1), (2, 2)]).area


if __name__ == "__main__":
    unittest.main()
