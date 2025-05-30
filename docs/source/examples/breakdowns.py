"An example to show off Breakdowns"

import os
import pickle
import sys

import pint
from packaging import version

from gpkit.breakdowns import Breakdowns

dirpath = os.path.dirname(os.path.realpath(__file__)) + os.sep
if version.parse(pint.__version__) >= version.parse("0.13"):
    with open(dirpath + "solar_13.p", "rb") as fil:
        sol = pickle.load(fil)
elif version.parse(pint.__version__) >= version.parse("0.12"):
    with open(dirpath + "solar_12.p", "rb") as fil:
        sol = pickle.load(fil)
elif version.parse(pint.__version__) >= version.parse("0.10"):
    with open(dirpath + "solar_10.p", "rb") as fil:
        sol = pickle.load(fil)
elif version.parse(pint.__version__) == version.parse("0.9"):
    with open(dirpath + "solar.p", "rb") as fil:
        sol = pickle.load(fil)
else:
    sol = None

# our Miniconda windows test platform can't print unicode
if sys.platform[:3] != "win" and sol is not None:
    # the code to create solar.p is in ./breakdowns/solartest.py
    bds = Breakdowns(sol)

    print("Cost breakdown (as seen in solution tables)")
    print("==============")
    bds.plot("cost")

    print("Variable breakdowns (note the two methods of access)")
    print("===================")
    (varkey,) = sol["variables"].keymap[
        ("Mission.FlightSegment.AircraftPerf" ".AircraftDrag.Poper")
    ]
    bds.plot(varkey)
    bds.plot("AircraftPerf.AircraftDrag.MotorPerf.Q")

    print("Combining the two above by increasing maxwidth")
    print("----------------------------------------------")
    bds.plot("AircraftPerf.AircraftDrag.Poper", maxwidth=105)

    print("Model sensitivity breakdowns (note the two methods of access)")
    print("============================")
    bds.plot("model sensitivities")
    bds.plot("Aircraft")

    print("Exhaustive variable breakdown traces (and configuration arguments)")
    print("====================================")
    # often useful as a reference point when reading traces
    bds.plot("AircraftPerf.AircraftDrag.Poper", height=12)
    # includes factors, can be useful for reading traces as well
    bds.plot("AircraftPerf.AircraftDrag.Poper", showlegend=True)
    print("\nPermissivity = 2 (the default)")
    print("----------------")
    bds.trace("AircraftPerf.AircraftDrag.Poper")
    print("\nPermissivity = 1 (stops at Pelec = v·i)")
    print("----------------")
    bds.trace("AircraftPerf.AircraftDrag.Poper", permissivity=1)

    # you can also produce Plotly treemaps/icicle plots of your breakdowns
    fig = bds.treemap("model sensitivities", returnfig=True)
    fig = bds.icicle("cost", returnfig=True)
    # uncommenting any of the below makes and shows the plot directly
    # bds.icicle("model sensitivities")
    # bds.treemap("cost")
