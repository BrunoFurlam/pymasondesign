from __future__ import annotations

import unittest
from pymasondesign.geometry.tolerances import (
    GEOMETRIC_TOLERANCE,
    JUNCTION_TOLERANCE,
    OVERLAP_TOLERANCE,
    DIVISION_GUARD,
    is_zero,
    is_close,
    is_within_unit,
    is_at_start,
    is_at_end,
    is_at_vertex,
    is_interior,
)


class TestTolerances(unittest.TestCase):
    def test_constants_definitions(self):
        self.assertAlmostEqual(GEOMETRIC_TOLERANCE, 1e-9)
        self.assertAlmostEqual(JUNCTION_TOLERANCE, 1e-4)
        self.assertAlmostEqual(OVERLAP_TOLERANCE, 1e-9)
        self.assertAlmostEqual(DIVISION_GUARD, 1e-15)

    def test_is_zero(self):
        self.assertTrue(is_zero(0.0))
        self.assertTrue(is_zero(1e-10))
        self.assertTrue(is_zero(-1e-10))
        self.assertFalse(is_zero(1e-8))
        self.assertTrue(is_zero(1e-5, tolerance=1e-4))

    def test_is_close(self):
        self.assertTrue(is_close(1.0, 1.0 + 1e-10))
        self.assertTrue(is_close(2.5, 2.5 - 1e-10))
        self.assertFalse(is_close(1.0, 1.0 + 1e-8))
        self.assertTrue(is_close(1.0, 1.00005, tolerance=1e-4))

    def test_is_within_unit(self):
        self.assertTrue(is_within_unit(0.0))
        self.assertTrue(is_within_unit(1.0))
        self.assertTrue(is_within_unit(0.5))
        self.assertTrue(is_within_unit(-1e-10))
        self.assertTrue(is_within_unit(1.0 + 1e-10))
        self.assertFalse(is_within_unit(-1e-8))
        self.assertFalse(is_within_unit(1.0 + 1e-8))

    def test_is_at_start(self):
        self.assertTrue(is_at_start(0.0))
        self.assertTrue(is_at_start(1e-10))
        self.assertTrue(is_at_start(-1e-10))
        self.assertFalse(is_at_start(1e-8))
        self.assertFalse(is_at_start(1.0))

    def test_is_at_end(self):
        self.assertTrue(is_at_end(1.0))
        self.assertTrue(is_at_end(1.0 + 1e-10))
        self.assertTrue(is_at_end(1.0 - 1e-10))
        self.assertFalse(is_at_end(1.0 + 1e-8))
        self.assertFalse(is_at_end(0.0))

    def test_is_at_vertex(self):
        self.assertTrue(is_at_vertex(0.0))
        self.assertTrue(is_at_vertex(1.0))
        self.assertTrue(is_at_vertex(1e-10))
        self.assertTrue(is_at_vertex(1.0 - 1e-10))
        self.assertFalse(is_at_vertex(0.5))
        self.assertFalse(is_at_vertex(-0.1))

    def test_is_interior(self):
        self.assertTrue(is_interior(0.5))
        self.assertTrue(is_interior(0.1))
        self.assertTrue(is_interior(0.99))
        self.assertFalse(is_interior(0.0))
        self.assertFalse(is_interior(1.0))
        self.assertFalse(is_interior(1e-10))
        self.assertFalse(is_interior(1.0 - 1e-10))
        self.assertFalse(is_interior(-0.1))
        self.assertFalse(is_interior(1.1))


if __name__ == "__main__":
    unittest.main()
