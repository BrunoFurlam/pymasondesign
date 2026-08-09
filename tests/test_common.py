from __future__ import annotations

import unittest
from pymasondesign.common import to_tuple


class TestCommonConverters(unittest.TestCase):
    def test_to_tuple_with_none(self):
        result = to_tuple(None)
        self.assertEqual(result, ())
        self.assertIsInstance(result, tuple)

    def test_to_tuple_with_empty_iterable(self):
        self.assertEqual(to_tuple([]), ())
        self.assertEqual(to_tuple(()), ())
        self.assertEqual(to_tuple(set()), ())

    def test_to_tuple_with_list(self):
        items = [1, 2, 3]
        result = to_tuple(items)
        self.assertEqual(result, (1, 2, 3))
        self.assertIsInstance(result, tuple)

    def test_to_tuple_with_tuple(self):
        items = ("a", "b", "c")
        result = to_tuple(items)
        self.assertEqual(result, ("a", "b", "c"))
        self.assertIsInstance(result, tuple)

    def test_to_tuple_with_generator(self):
        gen = (x * 2 for x in range(3))
        result = to_tuple(gen)
        self.assertEqual(result, (0, 2, 4))
        self.assertIsInstance(result, tuple)


if __name__ == "__main__":
    unittest.main()
