"""
Qt widget that shows the plot.

.. autosummary::

    ~auto_color
    ~auto_symbol
    ~ChartView
    ~PLOT_COLORS
    ~PLOT_SYMBOLS
    ~TIMESTAMP_LIMIT

:see: https://matplotlib.org/stable/users/index.html

..  note:: To see the full list of plot symbols from
    MatPlotLib (https://matplotlib.org/stable/gallery/lines_bars_and_markers/marker_reference.html)::

        from matplotlib.lines import Line2D
        print(Line2D.markers)

"""

import datetime
import logging
from itertools import cycle

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5 import QtCore
from PyQt5 import QtWidgets

logger = logging.getLogger(__name__)

TIMESTAMP_LIMIT = datetime.datetime.fromisoformat("1990-01-01").timestamp()
"""Earliest date for a run in any Bluesky catalog (1990-01-01)."""

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
    gold
    cornflowerblue
    forestgreen
    salmon
""".split()
"""
Select subset of the MatPlotLib named colors.

Do **NOT** sort these colors alphabetically!  There should be obvious
contrast between adjacent colors.

* :see: https://matplotlib.org/stable/gallery/color/named_colors.html
* :see: https://developer.mozilla.org/en-US/docs/Web/CSS/named-color
"""

PLOT_SYMBOLS = """o + x * s d ^ v""".split()
"""
Select subset of the MatPlotLib marker symbols.

To print the full dictionary of symbols available::

    from matplotlib.lines import Line2D
    print(Line2D.markers)

:see: https://matplotlib.org/stable/gallery/lines_bars_and_markers/marker_reference.html
"""

# iterators for colors & symbols
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
    MatPlotLib Figure

    .. autosummary::

        ~plot
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

        # Remember these Matplotlib figure, canvas, and axes objects.
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.main_axes = self.figure.add_subplot(111)

        # Adjust margins
        self.figure.subplots_adjust(bottom=0.1, top=0.9, right=0.92)
        self.setOptions()

        config = {
            "title": self.setPlotTitle,
            "subtitle": self.setPlotSubtitle,
            "y": self.setLeftAxisText,
            "x": self.setBottomAxisText,
            "x_units": self.setBottomAxisUnits,
            "y_units": self.setLeftAxisUnits,
            "x_datetime": self.setAxisDateTime,
        }
        for k, func in config.items():
            func(kwargs.get(k))

        # QWidget Layout
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        # Add directly unless we plan to use the toolbar later.
        layout.addWidget(NavigationToolbar(self.canvas, self))
        layout.addWidget(self.canvas)

        # plot
        size.setHorizontalStretch(4)

        self.curves = {}  # all the curves on the graph, key = label

        # Live plotting support
        self.live_mode = False
        self.live_timer = None
        self.live_run = None
        self.live_stream_name = None
        self.live_data_fields = {}  # Maps label -> (x_field, y_field)
        self.update_interval = 2000  # milliseconds (2 seconds)

    def addCurve(self, *args, title="plot title", **kwargs):
        """Add to graph."""
        plot_obj = self.main_axes.plot(*args, **kwargs)
        self.updatePlot(title)
        # Add to the dictionary
        label = kwargs.get("label")
        if label is None:
            raise KeyError("This curve has no label.")
        self.curves[label] = plot_obj[0], *args

    def option(self, key, default=None):
        return self.plotOptions().get(key, default)

    def plot(self, *args, title="plot title", **kwargs):
        """
        Plot from the supplied (x, y) or (y) data.

        PARAMETERS

        - args tuple: x & y xarray.DataArrays.  When only y is supplied, x will
          be the index.
        - kwargs (dict): dict(str, obj)
        """
        self.setOptions(**kwargs.get("plot_options", {}))
        ds_options = kwargs.get("ds_options", kwargs)
        self.main_axes.axis("on")

        label = ds_options.get("label")
        if label is None:
            raise KeyError("This curve has no label.")
        if label not in self.curves:
            self.addCurve(*args, title=title, **ds_options)

    def plotOptions(self):
        return self._plot_options

    def setAxisDateTime(self, choice):
        pass  # data provided in datetime objects

    def setAxisLabel(self, axis, text):
        set_axis_label_method = {
            "bottom": self.main_axes.set_xlabel,
            "left": self.main_axes.set_ylabel,
        }[axis]
        set_axis_label_method(text)

    def setAxisUnits(self, axis, text):
        pass  # TODO: not implemented yet

    def setBottomAxisText(self, text):
        self.setAxisLabel("bottom", text)

    def setBottomAxisUnits(self, text):
        self.setAxisUnits("bottom", text)

    def setConfigPlot(self, grid=True):
        self.setLeftAxisText(self.ylabel())
        self.setBottomAxisText(self.xlabel())
        self.setPlotTitle(self.title())
        if grid:
            self.main_axes.grid(True, color="#cccccc", linestyle="-", linewidth=0.5)
        else:
            self.main_axes.grid(False)
        self.canvas.draw()

    def setLeftAxisText(self, text):
        self.setAxisLabel("left", text)

    def setLeftAxisUnits(self, text):
        self.setAxisUnits("left", text)

    def setOption(self, key, value):
        self._plot_options[key] = value

    def setOptions(self, **options):
        self._plot_options = options

    def setPlotTitle(self, text):
        if text is not None:
            self.figure.suptitle(text)

    def setPlotSubtitle(self, text):
        if text is not None:
            self.main_axes.set_title(text, size=7, x=1, ha="right", color="lightgrey")

    def setSubtitle(self, text):
        self.setOption("subtitle", text)

    def setTitle(self, text):
        self.setOption("title", text)

    def setXLabel(self, text):
        self.setOption("xlabel", text)

    def setYLabel(self, text):
        self.setOption("ylabel", text)

    def subtitle(self):
        return self.option("subtitle")

    def title(self):
        return self.option("title")

    def updateLegend(self):
        labels = self.main_axes.get_legend_handles_labels()[1]
        valid_labels = [label for label in labels if not label.startswith("_")]
        if valid_labels:
            self.main_axes.legend()

    def updatePlot(self, title):
        """Update annotations (titles & axis labels)."""
        self.setPlotTitle(title)

        iso8601 = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        subtitle = f"plotted: {iso8601}"
        if self.parent is not None:
            cat_name = self.parent.catalogName() or ""
            subtitle = f"catalog={cat_name!r}  {subtitle}"
        self.setPlotSubtitle(subtitle)

        self.setBottomAxisText(self.xlabel())
        self.setLeftAxisText(self.ylabel())

        # Recompute the axes limits and autoscale:
        self.main_axes.relim()
        self.main_axes.autoscale_view()
        self.updateLegend()
        self.setConfigPlot()
        self.canvas.draw()

    def xlabel(self):
        return self.option("xlabel")

    def ylabel(self):
        return self.option("ylabel")

    # ========== Live Plotting Methods ==========

    def enableLiveMode(self, run, stream_name, data_fields):
        """
        Enable live plotting for an active run.

        Parameters
        ----------
        run : RunMetadata
            The active run to monitor
        stream_name : str
            Name of the data stream to plot
        data_fields : dict
            Maps curve label -> (x_field_name, y_field_name)
        """
        # Use is_active property for reliable check
        if not run.is_active:
            logger.info(
                f"Run {run.uid[:7]} is not active (is_active={run.is_active}), live mode not enabled"
            )
            return

        self.live_run = run
        self.live_stream_name = stream_name
        self.live_data_fields = data_fields
        self.live_mode = True

        logger.info(f"Live mode enabled for run {run.uid[:7]}")
        logger.info(f"Live data fields: {data_fields}")
        logger.info(f"Starting live updates with interval {self.update_interval}ms")
        self.startLiveUpdates()

    def startLiveUpdates(self):
        """Start the timer for periodic updates."""
        logger.info(f"startLiveUpdates called with interval: {self.update_interval}ms")

        if self.live_timer is None:
            logger.info("Creating new QTimer for live updates")
            self.live_timer = QtCore.QTimer(self)
            self.live_timer.timeout.connect(self.refreshPlot)
        else:
            logger.info("Reusing existing QTimer")

        self.live_timer.start(self.update_interval)
        logger.info(f"Live updates started (interval: {self.update_interval}ms)")
        logger.info(f"Timer active: {self.live_timer.isActive()}")

    def stopLiveUpdates(self):
        """Stop the live update timer."""
        if self.live_timer:
            self.live_timer.stop()

        self.live_mode = False
        logger.info("Live updates stopped")

    def refreshPlot(self):
        """Refresh the plot with latest data from the active run."""
        logger.debug(
            f"refreshPlot called: live_run={self.live_run is not None}, live_mode={self.live_mode}"
        )

        if not self.live_run or not self.live_mode:
            logger.debug(
                "refreshPlot: returning early - no live_run or live_mode disabled"
            )
            return

        try:
            logger.info("Refreshing plot data...")
            # Re-fetch metadata to check if still active
            self.live_run.request_from_tiled_server()

            if not self.live_run.is_active:
                logger.info("Run completed, stopping live updates")
                self.stopLiveUpdates()
                self.setPlotSubtitle("Run completed")
                return

            # Force refresh stream data to get latest
            stream_data = self.live_run.force_refresh_stream_data(self.live_stream_name)
            logger.info(
                f"Got fresh stream data with shape: {stream_data.shape if hasattr(stream_data, 'shape') else 'unknown'}"
            )

            # Also refresh field selection data if it exists
            if hasattr(self, "field_widget") and self.field_widget:
                self.field_widget.refreshFieldData()

            # Update each curve
            for label, (x_field, y_field) in self.live_data_fields.items():
                if label not in self.curves:
                    continue

                plot_obj = self.curves[label][0]

                # Get new data
                x_data = stream_data["data"][x_field]
                y_data = stream_data["data"][y_field]

                # Check if data shapes have changed
                try:
                    # Try to update the existing plot object
                    plot_obj.set_data(x_data, y_data)
                except ValueError as e:
                    if "shape" in str(e).lower():
                        logger.info(f"Data shape changed for {label}, recreating plot")
                        # Data shape changed, need to recreate the plot
                        # Clear the old plot
                        plot_obj.remove()

                        # Create new plot with same style
                        style = self.curves[label][1]  # Get the original style
                        new_plot = self.main_axes.plot(x_data, y_data, **style)[0]
                        self.curves[label] = (new_plot, style)
                    else:
                        raise

            # Refresh display
            self.main_axes.relim()
            self.main_axes.autoscale_view()
            self.updateLegend()
            self.canvas.draw()

            # Update timestamp with LIVE indicator
            iso8601 = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
            subtitle = f"🔴 LIVE - updated: {iso8601}"
            if self.parent is not None:
                cat_name = self.parent.catalogName() or ""
                subtitle = f"catalog={cat_name!r}  {subtitle}"
            self.setPlotSubtitle(subtitle)

            logger.debug(f"Plot refreshed: {len(x_data)} points")

        except Exception as exc:
            logger.error(f"Live update failed: {exc}", exc_info=True)
            self.stopLiveUpdates()
            self.setPlotSubtitle(f"Live update error: {exc}")


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
