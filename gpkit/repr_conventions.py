"Repository for representation standards"

import re
import sys

import numpy as np

from .small_classes import Numbers, Quantity
from .small_scripts import try_str_without

INSIDE_PARENS = re.compile(r"\(.*\)")

if sys.platform[:3] == "win":  # pragma: no cover
    MUL = "*"
    PI_STR = "PI"
    UNICODE_EXPONENTS = False
    UNIT_FORMATTING = ":~"
else:  # pragma: no cover
    MUL = "·"
    PI_STR = "π"
    UNICODE_EXPONENTS = True
    UNIT_FORMATTING = ":P~"


def lineagestr(lineage, modelnums=True):
    "Returns properly formatted lineage string"
    if not isinstance(lineage, tuple):
        lineage = getattr(lineage, "lineage", None)
    return (
        ".".join(
            [f"{name}{num}" if (num and modelnums) else name for name, num in lineage]
        )
        if lineage
        else ""
    )


def unitstr(units, into="%s", options=UNIT_FORMATTING, dimless=""):
    "Returns the string corresponding to an object's units."
    if hasattr(units, "units") and isinstance(units.units, Quantity):
        units = units.units
    if not isinstance(units, Quantity):
        return dimless
    if options == ":~" and "ohm" in str(units.units):  # pragma: no cover
        rawstr = str(units.units)  # otherwise it'll be a capital Omega
    else:
        rawstr = ("{%s}" % options).format(units.units)
    units = rawstr.replace(" ", "").replace("dimensionless", dimless)
    return into % units or dimless


def latex_unitstr(units):
    "Returns latex unitstr"
    us = unitstr(units, r"~\mathrm{%s}", ":L~")
    utf = us.replace("frac", "tfrac").replace(r"\cdot", r"\cdot ")
    return utf if utf != r"~\mathrm{-}" else ""


def strify(val, excluded):
    "Turns a value into as pretty a string as possible."
    if isinstance(val, Numbers):
        isqty = hasattr(val, "magnitude")
        if isqty:
            units = val
            val = val.magnitude
        if np.pi / 12 < val < 100 * np.pi and abs(12 * val / np.pi % 1) <= 1e-2:
            # val is in bounds and a clean multiple of PI!
            if val > 3.1:  # product of PI
                val = f"{val/np.pi:.3g}{PI_STR}"
                if val == f"1{PI_STR}":
                    val = PI_STR
            else:  # division of PI
                val = f"({PI_STR}/{np.pi/val:.3g})"
        else:
            val = f"{val:.3g}"
        if isqty:
            val += unitstr(units, " [%s]")
    else:
        val = try_str_without(val, excluded)
    return val


def parenthesize(string, addi=True, mult=True):
    "Parenthesizes a string if it needs it and isn't already."
    parensless = string if "(" not in string else INSIDE_PARENS.sub("", string)
    bare_addi = " + " in parensless or " - " in parensless
    bare_mult = "·" in parensless or "/" in parensless
    if parensless and (addi and bare_addi) or (mult and bare_mult):
        return f"({string})"
    return string


class ReprMixin:
    "This class combines various printing methods for easier adoption."

    lineagestr = lineagestr
    unitstr = unitstr
    latex_unitstr = latex_unitstr

    cached_strs = None
    ast = None

    # pylint: disable=too-many-branches, too-many-statements
    def parse_ast(self, excluded=()):
        "Turns the AST of this object's construction into a faithful string"
        excluded = frozenset({"units"}.union(excluded))
        if self.cached_strs is None:
            self.cached_strs = {}
        elif excluded in self.cached_strs:
            return self.cached_strs[excluded]
        oper, values = self.ast  # pylint: disable=unpacking-non-sequence

        if oper == "add":
            left = strify(values[0], excluded)
            right = strify(values[1], excluded)
            if right[0] == "-":
                aststr = f"{left} - {right[1:]}"
            else:
                aststr = f"{left} + {right}"
        elif oper == "mul":
            left = parenthesize(strify(values[0], excluded), mult=False)
            right = parenthesize(strify(values[1], excluded), mult=False)
            if left == "1":
                aststr = right
            elif right == "1":
                aststr = left
            else:
                aststr = f"{left}{MUL}{right}"
        elif oper == "div":
            left = parenthesize(strify(values[0], excluded), mult=False)
            right = parenthesize(strify(values[1], excluded))
            if right == "1":
                aststr = left
            else:
                aststr = f"{left}/{right}"
        elif oper == "neg":
            val = parenthesize(strify(values, excluded), mult=False)
            aststr = f"-{val}"
        elif oper == "pow":
            left = parenthesize(strify(values[0], excluded))
            x = values[1]
            if left == "1":
                aststr = "1"
            elif (
                UNICODE_EXPONENTS
                and not getattr(x, "shape", None)
                and int(x) == x
                and 2 <= x <= 9
            ):
                x = int(x)
                if x in (2, 3):
                    aststr = f"{left}{chr(176 + x)}"
                elif x in (4, 5, 6, 7, 8, 9):
                    aststr = f"{left}{chr(8304 + x)}"
            else:
                aststr = f"{left}^{x}"
        # pylint: disable=fixme
        elif oper == "prod":  # TODO: only do if it makes a shorter string
            val = parenthesize(strify(values[0], excluded))
            aststr = f"{val}.prod()"
        elif oper == "sum":  # TODO: only do if it makes a shorter string
            val = parenthesize(strify(values[0], excluded))
            aststr = f"{val}.sum()"
        elif oper == "index":  # TODO: label vectorization idxs
            left = parenthesize(strify(values[0], excluded))
            idx = values[1]
            if left[-3:] == "[:]":  # pure variable access
                left = left[:-3]
            if isinstance(idx, tuple):
                elstrs = []
                for el in idx:
                    if isinstance(el, slice):
                        start = el.start or ""
                        stop = el.stop if el.stop and el.stop < sys.maxsize else ""
                        step = f":{el.step}" if el.step is not None else ""
                        elstrs.append(f"{start}:{stop}{step}")
                    elif isinstance(el, Numbers):
                        elstrs.append(str(el))
                idx = ",".join(elstrs)
            elif isinstance(idx, slice):
                start = idx.start or ""
                stop = idx.stop if idx.stop and idx.stop < 1e6 else ""
                step = f":{idx.step}" if idx.step is not None else ""
                idx = f"{start}:{stop}{step}"
            aststr = f"{left}[{idx}]"
        else:
            raise ValueError(oper)
        # pylint: disable=possibly-used-before-assignment
        self.cached_strs[excluded] = aststr
        return aststr

    def __repr__(self):
        "Returns namespaced string."
        return f"gpkit.{self.__class__.__name__}({self})"

    def __str__(self):
        "Returns default string."
        return self.str_without()  # pylint: disable=no-member

    def _repr_latex_(self):
        "Returns default latex for automatic iPython Notebook rendering."
        return "$$" + self.latex() + "$$"  # pylint: disable=no-member
