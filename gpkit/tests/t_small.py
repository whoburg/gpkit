"""Tests for small_classes.py and small_scripts.py"""

import unittest

import gpkit
from gpkit.repr_conventions import unitstr
from gpkit.small_classes import HashVector


class TestHashVector(unittest.TestCase):
    """TestCase for the HashVector class"""

    def test_init(self):
        """Make sure HashVector acts like a dict"""
        # args and kwargs
        hv = HashVector([(2, 3), (1, 10)], dog="woof")
        self.assertTrue(isinstance(hv, dict))
        self.assertEqual(hv, {2: 3, 1: 10, "dog": "woof"})
        # no args
        self.assertEqual(HashVector(), {})
        # creation from dict
        self.assertEqual(HashVector({"x": 7}), {"x": 7})

    def test_neg(self):
        """Test negation"""
        hv = HashVector(x=7, y=0, z=-1)
        self.assertEqual(-hv, {"x": -7, "y": 0, "z": 1})

    def test_pow(self):
        """Test exponentiation"""
        hv = HashVector(x=4, y=0, z=1)
        self.assertEqual(hv**0.5, {"x": 2, "y": 0, "z": 1})
        with self.assertRaises(TypeError):
            _ = hv**hv
        with self.assertRaises(TypeError):
            _ = hv ** "a"

    def test_mul_add(self):
        """Test multiplication and addition"""
        a = HashVector(x=1, y=7)
        b = HashVector()
        c = HashVector(x=3, z=4)
        # nonsense multiplication
        with self.assertRaises(TypeError):
            _ = a * set()
        # multiplication and addition by scalars
        r = a * 0
        self.assertEqual(r, HashVector(x=0, y=0))
        self.assertTrue(isinstance(r, HashVector))
        r = a - 2
        self.assertEqual(r, HashVector(x=-1, y=5))
        self.assertTrue(isinstance(r, HashVector))
        with self.assertRaises(TypeError):
            _ = r + "a"
        # multiplication and addition by dicts
        self.assertEqual(a + b, a)
        self.assertEqual(a + b + c, HashVector(x=4, y=7, z=4))


class TestSmallScripts(unittest.TestCase):
    """TestCase for gpkit.small_scripts"""

    def test_unitstr(self):
        x = gpkit.Variable("x", "ft")
        # pint issue 356
        footstrings = ("ft", "foot")  # backwards compatibility with pint 0.6
        if gpkit.units:
            self.assertEqual(unitstr(gpkit.Variable("n", "count")), "count")
            self.assertIn(unitstr(x), footstrings)
            self.assertIn(unitstr(x.key), footstrings)
        self.assertEqual(unitstr(gpkit.Variable("y"), dimless="---"), "---")
        self.assertEqual(unitstr(None, dimless="--"), "--")

    def test_pint_366(self):
        # test for https://github.com/hgrecco/pint/issues/366
        if gpkit.units:
            self.assertIn(
                unitstr(gpkit.units("nautical_mile")), ("nmi", "nautical_mile")
            )
            self.assertEqual(gpkit.units("nautical_mile"), gpkit.units("nmi"))


TESTS = [TestHashVector, TestSmallScripts]


if __name__ == "__main__":  # pragma: no cover
    # pylint: disable=wrong-import-position
    from gpkit.tests.helpers import run_tests

    run_tests(TESTS)
