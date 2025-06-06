"Example Tight ConstraintSet usage"

from gpkit import Model, Variable
from gpkit.constraints.tight import Tight

Tight.reltol = 1e-2  # set the global tolerance of Tight
x = Variable("x")
x_min = Variable("x_{min}", 2)
m = Model(x, [Tight([x >= 1], reltol=1e-3), x >= x_min])  # set the specific tolerance
m.solve(verbosity=0)  # prints warning
