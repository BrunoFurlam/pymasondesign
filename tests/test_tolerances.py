from __future__ import annotations

import unittest
from pymasondesign.geometry.tolerances import (
    GEOMETRIC_TOLERANCE,
    JUNCTION_TOLERANCE,
    OVERLAP_TOLERANCE,
    DIVISION_GUARD,
    is_zero,
    is_not_zero,
    is_close,
    is_not_close,
    is_greater,
    is_greater_or_equal,
    is_less,
    is_less_or_equal,
    is_positive,
    is_negative,
    is_non_negative,
    is_non_positive,
    is_between,
    is_strictly_between,
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

    def test_is_not_zero(self):
        self.assertFalse(is_not_zero(0.0))
        self.assertFalse(is_not_zero(1e-10))
        self.assertFalse(is_not_zero(-1e-10))
        self.assertTrue(is_not_zero(1e-8))
        self.assertTrue(is_not_zero(-1e-8))
        self.assertFalse(is_not_zero(1e-5, tolerance=1e-4))

    def test_is_close(self):
        self.assertTrue(is_close(1.0, 1.0 + 1e-10))
        self.assertTrue(is_close(2.5, 2.5 - 1e-10))
        self.assertFalse(is_close(1.0, 1.0 + 1e-8))
        self.assertTrue(is_close(1.0, 1.00005, tolerance=1e-4))

    def test_is_not_close(self):
        self.assertFalse(is_not_close(1.0, 1.0 + 1e-10))
        self.assertFalse(is_not_close(2.5, 2.5 - 1e-10))
        self.assertTrue(is_not_close(1.0, 1.0 + 1e-8))
        self.assertTrue(is_not_close(1.0, 1.0002, tolerance=1e-4))

    def test_is_greater(self):
        self.assertTrue(is_greater(5.0 + 1e-8, 5.0))
        self.assertFalse(is_greater(5.0 + 1e-10, 5.0))
        self.assertFalse(is_greater(5.0, 5.0))
        self.assertFalse(is_greater(4.9, 5.0))
        self.assertTrue(is_greater(2.0002, 2.0, tolerance=1e-4))
        self.assertFalse(is_greater(2.00005, 2.0, tolerance=1e-4))

    def test_is_greater_or_equal(self):
        self.assertTrue(is_greater_or_equal(5.0, 5.0))
        self.assertTrue(is_greater_or_equal(5.0 - 1e-10, 5.0))
        self.assertTrue(is_greater_or_equal(5.1, 5.0))
        self.assertFalse(is_greater_or_equal(5.0 - 1e-8, 5.0))
        self.assertTrue(is_greater_or_equal(1.99995, 2.0, tolerance=1e-4))
        self.assertFalse(is_greater_or_equal(1.999, 2.0, tolerance=1e-4))

    def test_is_less(self):
        self.assertTrue(is_less(5.0 - 1e-8, 5.0))
        self.assertFalse(is_less(5.0 - 1e-10, 5.0))
        self.assertFalse(is_less(5.0, 5.0))
        self.assertFalse(is_less(5.1, 5.0))
        self.assertTrue(is_less(1.999, 2.0, tolerance=1e-4))
        self.assertFalse(is_less(1.99995, 2.0, tolerance=1e-4))

    def test_is_less_or_equal(self):
        self.assertTrue(is_less_or_equal(5.0, 5.0))
        self.assertTrue(is_less_or_equal(5.0 + 1e-10, 5.0))
        self.assertTrue(is_less_or_equal(4.9, 5.0))
        self.assertFalse(is_less_or_equal(5.0 + 1e-8, 5.0))
        self.assertTrue(is_less_or_equal(2.00005, 2.0, tolerance=1e-4))
        self.assertFalse(is_less_or_equal(2.0002, 2.0, tolerance=1e-4))

    def test_is_positive(self):
        self.assertTrue(is_positive(1e-8))
        self.assertFalse(is_positive(1e-10))
        self.assertFalse(is_positive(0.0))
        self.assertFalse(is_positive(-1e-8))
        self.assertTrue(is_positive(0.001, tolerance=1e-4))
        self.assertFalse(is_positive(0.00005, tolerance=1e-4))

    def test_is_negative(self):
        self.assertTrue(is_negative(-1e-8))
        self.assertFalse(is_negative(-1e-10))
        self.assertFalse(is_negative(0.0))
        self.assertFalse(is_negative(1e-8))
        self.assertTrue(is_negative(-0.001, tolerance=1e-4))
        self.assertFalse(is_negative(-0.00005, tolerance=1e-4))

    def test_is_non_negative(self):
        self.assertTrue(is_non_negative(0.0))
        self.assertTrue(is_non_negative(1.0))
        self.assertTrue(is_non_negative(-1e-10))
        self.assertFalse(is_non_negative(-1e-8))
        self.assertTrue(is_non_negative(-0.00005, tolerance=1e-4))
        self.assertFalse(is_non_negative(-0.001, tolerance=1e-4))

    def test_is_non_positive(self):
        self.assertTrue(is_non_positive(0.0))
        self.assertTrue(is_non_positive(-1.0))
        self.assertTrue(is_non_positive(1e-10))
        self.assertFalse(is_non_positive(1e-8))
        self.assertTrue(is_non_positive(0.00005, tolerance=1e-4))
        self.assertFalse(is_non_positive(0.001, tolerance=1e-4))

    def test_is_between(self):
        # Inclusive
        self.assertTrue(is_between(2.0, 1.0, 3.0, inclusive=True))
        self.assertTrue(is_between(1.0, 1.0, 3.0, inclusive=True))
        self.assertTrue(is_between(3.0, 1.0, 3.0, inclusive=True))
        self.assertTrue(is_between(1.0 - 1e-10, 1.0, 3.0, inclusive=True))
        self.assertTrue(is_between(3.0 + 1e-10, 1.0, 3.0, inclusive=True))
        self.assertFalse(is_between(0.9, 1.0, 3.0, inclusive=True))
        self.assertFalse(is_between(3.1, 1.0, 3.0, inclusive=True))

        # Exclusive (inclusive=False)
        self.assertTrue(is_between(2.0, 1.0, 3.0, inclusive=False))
        self.assertFalse(is_between(1.0, 1.0, 3.0, inclusive=False))
        self.assertFalse(is_between(3.0, 1.0, 3.0, inclusive=False))
        self.assertFalse(is_between(1.0 + 1e-10, 1.0, 3.0, inclusive=False))
        self.assertFalse(is_between(3.0 - 1e-10, 1.0, 3.0, inclusive=False))
        self.assertTrue(is_between(1.0 + 1e-8, 1.0, 3.0, inclusive=False))
        self.assertTrue(is_between(3.0 - 1e-8, 1.0, 3.0, inclusive=False))

    def test_is_strictly_between(self):
        self.assertTrue(is_strictly_between(2.0, 1.0, 3.0))
        self.assertFalse(is_strictly_between(1.0, 1.0, 3.0))
        self.assertFalse(is_strictly_between(3.0, 1.0, 3.0))
        self.assertFalse(is_strictly_between(1.0 + 1e-10, 1.0, 3.0))
        self.assertFalse(is_strictly_between(3.0 - 1e-10, 1.0, 3.0))
        self.assertTrue(is_strictly_between(1.0 + 1e-8, 1.0, 3.0))
        self.assertTrue(is_strictly_between(3.0 - 1e-8, 1.0, 3.0))

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
