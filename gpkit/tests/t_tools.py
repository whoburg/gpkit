"""Tests for tools module"""

import unittest

import numpy as np
from numpy import log

from gpkit import Model, NomialArray, Variable, VectorVariable, parse_variables
from gpkit.small_scripts import mag
from gpkit.tools.autosweep import BinarySweepTree
from gpkit.tools.tools import te_exp_minus1, te_secant, te_tangent


def assert_logtol(first, second, logtol=1e-6):
    "Asserts that the logs of two arrays have a given abstol"
    np.testing.assert_allclose(log(mag(first)), log(mag(second)), atol=logtol, rtol=0)


class OnlyVectorParse(Model):
    """
    Variables of length 3
    ---------------------
    x    [-]    just another variable
    """

    @parse_variables(__doc__, globals())
    def setup(self):
        pass


class Fuselage(Model):
    """The thing that carries the fuel, engine, and payload

    Variables
    ---------
    f                [-]             Fineness
    g          9.81  [m/s^2]         Standard gravity
    k                [-]             Form factor
    l                [ft]            Length
    mfac       2.0   [-]             Weight margin factor
    R                [ft]            Radius
    rhocfrp    1.6   [g/cm^3]        Density of CFRP
    rhofuel    6.01  [lbf/gallon]    Density of 100LL fuel
    S                [ft^2]          Wetted area
    t          0.024 [in]            Minimum skin thickness
    Vol              [ft^3]          Volume
    W                [lbf]           Weight

    Upper Unbounded
    ---------------
    k, W

    """

    # pylint: disable=undefined-variable, invalid-name
    @parse_variables(__doc__, globals())
    def setup(self, Wfueltot):
        return [
            f == l / R / 2,
            k >= 1 + 60 / f**3 + f / 400,
            3 * (S / np.pi) ** 1.6075
            >= 2 * (l * R * 2) ** 1.6075 + (2 * R) ** (2 * 1.6075),
            Vol <= 4 * np.pi / 3 * (l / 2) * R**2,
            Vol >= Wfueltot / rhofuel,
            W / mfac >= S * rhocfrp * t * g,
        ]


class TestTools(unittest.TestCase):
    """TestCase for math models"""

    def test_vector_only_parse(self):
        # pylint: disable=no-member
        m = OnlyVectorParse()
        self.assertTrue(hasattr(m, "x"))
        self.assertIsInstance(m.x, NomialArray)
        self.assertEqual(len(m.x), 3)

    def test_parse_variables(self):
        Fuselage(Variable("Wfueltot", 5, "lbf"))

    def test_binary_sweep_tree(self):
        bst0 = BinarySweepTree([1, 2], [{"cost": 1}, {"cost": 8}], None, None)
        assert_logtol(bst0.sample_at([1, 1.5, 2])["cost"], [1, 3.375, 8], 1e-3)
        bst0.add_split(1.5, {"cost": 4})
        assert_logtol(
            bst0.sample_at([1, 1.25, 1.5, 1.75, 2])["cost"],
            [1, 2.144, 4, 5.799, 8],
            1e-3,
        )

    def test_dual_objective(self):
        x = Variable("x")
        y = Variable("y")
        eqns = [x >= 1, y >= 1, x * y == 10]
        n = 4
        ws = Variable("w_{CO}", ("sweep", np.linspace(1 / n, 1 - 1 / n, n)), "-")
        w_s = Variable("v_{CO}", lambda c: 1 - c[ws], "-")
        obj = ws * (x + y) + w_s * (y**-1 * x**-3)
        m = Model(obj, eqns)
        sol = m.solve(verbosity=0)
        a = sol["cost"]
        b = np.array([1.58856898, 2.6410391, 3.69348122, 4.74591386])
        self.assertTrue((abs(a - b) / (a + b + 1e-7) < 1e-7).all())

    def test_te_exp_minus1(self):
        """Test Taylor expansion of e^x - 1"""
        x = Variable("x")
        self.assertEqual(te_exp_minus1(x, 1), x)
        self.assertEqual(te_exp_minus1(x, 3), x + x**2 / 2 + x**3 / 6)
        self.assertEqual(te_exp_minus1(x, 0), 0)
        # make sure x was not modified
        self.assertEqual(x, Variable("x"))
        # try for VectorVariable too
        y = VectorVariable(3, "y")
        self.assertEqual(te_exp_minus1(y, 1), y)
        self.assertEqual(te_exp_minus1(y, 3), y + y**2 / 2 + y**3 / 6)
        self.assertEqual(te_exp_minus1(y, 0), 0)
        # make sure y was not modified
        self.assertEqual(y, VectorVariable(3, "y"))

    def test_te_secant(self):
        "Test Taylor expansion of secant(var)"
        x = Variable("x")
        self.assertEqual(te_secant(x, 1), 1 + x**2 / 2)
        a = te_secant(x, 2)
        b = 1 + x**2 / 2 + 5 * x**4 / 24
        self.assertTrue(
            all((abs(val) <= 1e-10 for val in (a.hmap - b.hmap).values()))
        )  # pylint:disable=no-member
        self.assertEqual(te_secant(x, 0), 1)
        # make sure x was not modified
        self.assertEqual(x, Variable("x"))
        # try for VectorVariable too
        y = VectorVariable(3, "y")
        self.assertTrue(te_secant(y, 0) == 1)  # truthy bc monomial constraint
        self.assertTrue(all(te_secant(y, 1) == 1 + y**2 / 2))
        self.assertTrue(all(te_secant(y, 2) == 1 + y**2 / 2 + 5 * y**4 / 24))
        # make sure y was not modified
        self.assertEqual(y, VectorVariable(3, "y"))
        _ = te_secant(x, 13)  # to trigger the extension

    def test_te_tangent(self):
        "Test Taylor expansion of tangent(var)"
        x = Variable("x")
        self.assertEqual(te_tangent(x, 1), x)
        self.assertEqual(te_tangent(x, 3), x + x**3 / 3 + 2 * x**5 / 15)
        self.assertEqual(te_tangent(x, 0), 0)
        # make sure x was not modified
        self.assertEqual(x, Variable("x"))
        # try for VectorVariable too
        y = VectorVariable(3, "y")
        self.assertEqual(te_tangent(y, 1), y)
        self.assertEqual(te_tangent(y, 3), y + y**3 / 3 + 2 * y**5 / 15)
        self.assertEqual(te_tangent(y, 0), 0)
        # make sure y was not modified
        self.assertEqual(y, VectorVariable(3, "y"))
        with self.assertRaises(NotImplementedError):
            _ = te_tangent(x, 16)


TESTS = [TestTools]


if __name__ == "__main__":  # pragma: no cover
    # pylint: disable=wrong-import-position
    from gpkit.tests.helpers import run_tests

    run_tests(TESTS)
