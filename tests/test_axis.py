from __future__ import annotations

import math
import unittest
from pymasondesign.geometry import (
    Point2D,
    Vector2D,
    Axis,
    AxisRelation,
    Transform2D,
    GEOMETRIC_TOLERANCE,
)


class TestAxis(unittest.TestCase):
    def test_zero_length_raises_value_error(self):
        with self.assertRaises(ValueError):
            Axis(Point2D(1.0, 2.0), Point2D(1.0, 2.0))

    def test_properties_and_as_vector(self):
        start = Point2D(1.0, 2.0)
        end = Point2D(4.0, 6.0)
        axis = Axis(start=start, end=end)

        self.assertAlmostEqual(axis.dx, 3.0)
        self.assertAlmostEqual(axis.dy, 4.0)
        self.assertAlmostEqual(axis.length, 5.0)

        vec = axis.as_vector
        self.assertIsInstance(vec, Vector2D)
        self.assertAlmostEqual(vec.x, 3.0)
        self.assertAlmostEqual(vec.y, 4.0)
        self.assertAlmostEqual(vec.magnitude, axis.length)

        direction = axis.direction
        self.assertAlmostEqual(direction.x, 0.6)
        self.assertAlmostEqual(direction.y, 0.8)
        self.assertAlmostEqual(direction.magnitude, 1.0)

        normal = axis.normal
        self.assertAlmostEqual(normal.x, -0.8)
        self.assertAlmostEqual(normal.y, 0.6)
        self.assertAlmostEqual(direction.dot(normal), 0.0)

        mid = axis.midpoint
        self.assertAlmostEqual(mid.x, 2.5)
        self.assertAlmostEqual(mid.y, 4.0)

        bounds = axis.bounds
        self.assertAlmostEqual(bounds.xmin, 1.0)
        self.assertAlmostEqual(bounds.xmax, 4.0)
        self.assertAlmostEqual(bounds.ymin, 2.0)
        self.assertAlmostEqual(bounds.ymax, 6.0)

    def test_point_at_and_projected_offset(self):
        axis = Axis(Point2D(0.0, 0.0), Point2D(10.0, 0.0))
        pt = axis.point_at(5.0)
        self.assertAlmostEqual(pt.x, 5.0)
        self.assertAlmostEqual(pt.y, 0.0)

        offset = axis.projected_offset(Point2D(7.0, 3.0))
        self.assertAlmostEqual(offset, 7.0)

    def test_distance_to_point(self):
        axis = Axis(Point2D(0.0, 0.0), Point2D(10.0, 0.0))

        # Ponto perpendicular ao segmento
        self.assertAlmostEqual(axis.distance_to_point(Point2D(5.0, 3.0)), 3.0)
        # Ponto antes de start
        self.assertAlmostEqual(axis.distance_to_point(Point2D(-4.0, 3.0)), 5.0)
        # Ponto após end
        self.assertAlmostEqual(axis.distance_to_point(Point2D(14.0, 3.0)), 5.0)

    def test_reversed_and_translated(self):
        axis = Axis(Point2D(1.0, 2.0), Point2D(4.0, 6.0))
        rev = axis.reversed()
        self.assertEqual(rev.start, axis.end)
        self.assertEqual(rev.end, axis.start)
        self.assertAlmostEqual(rev.as_vector.x, -3.0)
        self.assertAlmostEqual(rev.as_vector.y, -4.0)

        trans = axis.translated(Vector2D(10.0, 20.0))
        self.assertAlmostEqual(trans.start.x, 11.0)
        self.assertAlmostEqual(trans.start.y, 22.0)
        self.assertAlmostEqual(trans.end.x, 14.0)
        self.assertAlmostEqual(trans.end.y, 26.0)
        self.assertAlmostEqual(trans.as_vector.x, axis.as_vector.x)
        self.assertAlmostEqual(trans.as_vector.y, axis.as_vector.y)

    def test_transformed(self):
        axis = Axis(Point2D(1.0, 0.0), Point2D(3.0, 0.0))
        rot90 = Transform2D.rotation(math.pi / 2.0)
        transformed = axis.transformed(rot90)
        self.assertAlmostEqual(transformed.start.x, 0.0)
        self.assertAlmostEqual(transformed.start.y, 1.0)
        self.assertAlmostEqual(transformed.end.x, 0.0)
        self.assertAlmostEqual(transformed.end.y, 3.0)

    def test_parallel_and_collinear(self):
        a1 = Axis(Point2D(0.0, 0.0), Point2D(10.0, 0.0))
        a2 = Axis(Point2D(0.0, 5.0), Point2D(10.0, 5.0))
        a3 = Axis(Point2D(12.0, 0.0), Point2D(20.0, 0.0))
        a4 = Axis(Point2D(0.0, 0.0), Point2D(0.0, 10.0))

        self.assertTrue(a1.is_parallel(a2))
        self.assertFalse(a1.is_collinear(a2))

        self.assertTrue(a1.is_parallel(a3))
        self.assertTrue(a1.is_collinear(a3))

        self.assertFalse(a1.is_parallel(a4))

    def test_intersections(self):
        a1 = Axis(Point2D(0.0, 0.0), Point2D(10.0, 0.0))
        a2 = Axis(Point2D(5.0, -5.0), Point2D(5.0, 5.0))
        res_cross = a1.intersect(a2)
        self.assertEqual(res_cross.relation, AxisRelation.POINT_INTERSECT)
        self.assertIsNotNone(res_cross.point)
        self.assertAlmostEqual(res_cross.point.x, 5.0)
        self.assertAlmostEqual(res_cross.point.y, 0.0)

        # Touching vertex
        a3 = Axis(Point2D(10.0, 0.0), Point2D(10.0, 5.0))
        res_touch = a1.intersect(a3)
        self.assertEqual(res_touch.relation, AxisRelation.TOUCHING_VERTEX)
        self.assertIsNotNone(res_touch.point)
        self.assertAlmostEqual(res_touch.point.x, 10.0)
        self.assertAlmostEqual(res_touch.point.y, 0.0)

        # Overlapping
        a4 = Axis(Point2D(5.0, 0.0), Point2D(15.0, 0.0))
        res_overlap = a1.intersect(a4)
        self.assertEqual(res_overlap.relation, AxisRelation.OVERLAPPING)
        self.assertIsNotNone(res_overlap.overlap_segment)
        self.assertAlmostEqual(res_overlap.overlap_segment.start.x, 5.0)
        self.assertAlmostEqual(res_overlap.overlap_segment.end.x, 10.0)


if __name__ == "__main__":
    unittest.main()
