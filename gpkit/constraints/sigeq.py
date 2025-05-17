"Implements SignomialEquality"

from ..nomials import SingleSignomialEquality as SSE
from ..nomials.array import array_constraint as arrify
from .set import ConstraintSet


class SignomialEquality(ConstraintSet):
    "A constraint of the general form posynomial == posynomial"

    def __init__(self, left, right):
        if hasattr(left, "shape") or hasattr(right, "shape"):
            ConstraintSet.__init__(self, arrify("=", SSE)(left, right))
        else:
            ConstraintSet.__init__(self, [SSE(left, right)])
