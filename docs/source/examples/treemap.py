"Treemap example"

# import plotly
from performance_modeling import M  # pylint: disable=import-error

from gpkit.interactive.plotting import treemap

fig = treemap(M)
# plotly.offline.plot(fig, filename="treemap.html")  # uncomment to show

fig = treemap(M, itemize="constraints", sizebycount=True)
# plotly.offline.plot(fig, filename="sizedtreemap.html")  # uncomment to show
