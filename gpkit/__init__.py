"GP and SP modeling package"

# pylint:disable=wrong-import-position
__version__ = "0.1.0"
GPCOLORS = ["#59ade4", "#FA3333"]
GPBLU, GPRED = GPCOLORS

from .build import build
from .constraints.gp import GeometricProgram
from .constraints.model import Model
from .constraints.set import ConstraintSet
from .constraints.sgp import SequentialGeometricProgram
from .constraints.sigeq import SignomialEquality
from .globals import NamedVariables, SignomialsEnabled, Vectorize, settings

# NOTE above: the Variable the user sees is not the Variable used internally
from .nomials import ArrayVariable, Monomial, NomialArray, Posynomial, Signomial
from .nomials import VectorizableVariable as Variable
from .nomials import VectorVariable
from .solution_array import SolutionArray
from .tests.run_tests import run as run_unit_tests
from .tools.docstring import parse_variables
from .units import DimensionalityError, units, ureg
from .varkey import VarKey

if "just built!" in settings:  # pragma: no cover
    run_unit_tests(verbosity=1)
    print(
        """
GPkit is now installed with solver(s) %s
To incorporate new solvers at a later date, run `gpkit.build()`.

If any tests didn't pass, please post the output above
(starting from "Found no installed solvers, beginning a build.")
to gpkit@mit.edu or https://github.com/convexengineering/gpkit/issues/new
so we can prevent others from having these errors.

The same goes for any other bugs you encounter with GPkit:
send 'em our way, along with any interesting models, speculative features,
comments, discussions, or clarifications you feel like sharing.

Finally, we hope you find our documentation (https://gpkit.readthedocs.io/)
and engineering-design models (https://github.com/convexengineering/gplibrary/)
to be useful resources for your own applications.

Enjoy!
"""
        % settings["installed_solvers"]
    )
