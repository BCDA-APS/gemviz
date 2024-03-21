"""
Charting widget

.. autosummary::

    ~auto_color
    ~auto_symbol
    ~ChartView
"""

import datetime
from itertools import cycle

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# import pyqtgraph as pg
from PyQt5 import QtWidgets

TIMESTAMP_LIMIT = datetime.datetime.fromisoformat("1990-01-01").timestamp()

# https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/scatterplotitem.html#pyqtgraph.ScatterPlotItem.setSymbol
# https://developer.mozilla.org/en-US/docs/Web/CSS/named-color
# Do NOT sort these colors alphabetically!  There should be obvious
# contrast between adjacent colors.
PLOT_COLORS = """
    r g b c m
    goldenrod
    lime
    orange
    blueviolet
    brown
    teal
    olive
    lightcoral
    cornflowerblue
    forestgreen
    salmon
""".split()
PLOT_SYMBOLS = """o + x star s d t t2 t3""".split()

# FIXME: this is pyqtgraph
# pg.setConfigOption("background", "w")
# pg.setConfigOption("foreground", "k")
GRID_OPACITY = 0.1

_AUTO_COLOR_CYCLE = cycle(PLOT_COLORS)
_AUTO_SYMBOL_CYCLE = cycle(PLOT_SYMBOLS)


def auto_color():
    """Returns next color for pens and brushes."""
    return next(_AUTO_COLOR_CYCLE)


def auto_symbol():
    """Returns next symbol for scatter plots."""
    return next(_AUTO_SYMBOL_CYCLE)


class ChartView(QtWidgets.QWidget):
    """
    MatPlotLib PlotWidget

    .. autosummary::

        ~plot
        ~setAxisDateTime
        ~setAxisLabel
        ~setAxisUnits
        ~setBottomAxisText
        ~setLeftAxisText
        ~setLeftAxisUnits
        ~setPlotTitle
    """

    def __init__(self, parent, **kwargs):
        self.parent = parent

        super().__init__()

        size = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )

        # Create a Matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.main_axes = self.figure.add_subplot(111)
        # Adjust margins
        self.figure.subplots_adjust(bottom=0.1, top=0.9, right=0.92)

        # FIXME: this is pyqtgraph
        # self.plot_widget = pg.PlotWidget()
        # self.plot_widget.addLegend()
        # self.plot_widget.plotItem.showAxes(True)
        # self.plot_widget.plotItem.showGrid(x=True, y=True, alpha=GRID_OPACITY)
        # # see: https://stackoverflow.com/a/70200326
        # label = pg.LabelItem(
        #     f"plot: {datetime.datetime.now()}", color="lightgrey", size="8pt"
        # )
        # label.setParentItem(self.plot_widget.plotItem)
        # label.anchor(itemPos=(0, 1), parentPos=(0, 1))

        # config = {
        #     "title": self.setPlotTitle,
        #     "y": self.setLeftAxisText,
        #     "x": self.setBottomAxisText,
        #     "x_units": self.setBottomAxisUnits,
        #     "y_units": self.setLeftAxisUnits,
        #     "x_datetime": self.setAxisDateTime,
        # }
        # for k, func in config.items():
        #     func(kwargs.get(k))

        # QWidget Layout
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        # Add directly unless we plan to use the toolbar later.
        layout.addWidget(NavigationToolbar(self.canvas, self))
        layout.addWidget(self.canvas)

        # plot
        size.setHorizontalStretch(4)
        # FIXME: this is pyqtgraph
        # self.plot_widget.setSizePolicy(size)
        # layout.addWidget(self.plot_widget)

    def plot(self, *args, **kwargs):
        # return self.plot_widget.plot(*args, **kwargs)
        pass  # FIXME: this is pyqtgraph

    def setAxisDateTime(self, choice):
        # if choice:
        #     item = pg.DateAxisItem(orientation="bottom")
        #     self.plot_widget.setAxisItems({"bottom": item})
        pass  # FIXME: this is pyqtgraph

    def setAxisLabel(self, axis, text):
        # self.plot_widget.plotItem.setLabel(axis, text)
        pass  # FIXME: this is pyqtgraph

    def setAxisUnits(self, axis, text):
        # self.plot_widget.plotItem.axes[axis]["item"].labelUnits = text
        pass  # FIXME: this is pyqtgraph

    def setBottomAxisText(self, text):
        self.setAxisLabel("bottom", text)

    def setBottomAxisUnits(self, text):
        self.setAxisUnits("bottom", text)

    def setLeftAxisText(self, text):
        self.setAxisLabel("left", text)

    def setLeftAxisUnits(self, text):
        self.setAxisUnits("left", text)

    def setPlotTitle(self, text):
        # self.plot_widget.plotItem.setTitle(text)
        pass  # FIXME: this is pyqtgraph


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2024, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
