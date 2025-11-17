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

import numpy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from . import utils
from .curve_manager import CurveManager

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
        self._legacy_curve_styles = {}  # original style kwargs, keyed by label
        self.curveManager = CurveManager(self)
        self.clearBasicMath()

        # Live plotting support
        self.live_mode = False
        self.live_timer = None
        self.live_run = None
        self.live_stream_name = None
        self.live_data_fields = {}  # Maps label -> (x_field, y_field)
        self.field_widget = None
        self.update_interval = 2000  # milliseconds (2 seconds)

    # ==========================================
    #   Curves management
    # ==========================================

    def addCurve(self, *args, title="plot title", **kwargs):
        """Add to graph."""
        # Filter out metadata kwargs before passing to matplotlib
        # matplotlib doesn't recognize run_uid, y_field, stream_name
        metadata_keys = {"run_uid", "y_field", "stream_name"}
        matplotlib_kwargs = {k: v for k, v in kwargs.items() if k not in metadata_keys}

        plot_obj = self.main_axes.plot(*args, **matplotlib_kwargs)
        self.updatePlot(title)
        # Add to the dictionary
        label = kwargs.get("label")
        if label is None:
            raise KeyError("This curve has no label.")
        # Capture the style kwargs separately and cache the plotted data by label
        plot_kwargs = {k: v for k, v in kwargs.items() if k not in ["label"]}
        self._legacy_curve_styles[label] = plot_kwargs

        # Store the Matplotlib line together with the data arrays for reuse
        if len(args) == 1:
            self.curves[label] = (plot_obj[0], args[0])
        elif len(args) >= 2:
            self.curves[label] = (plot_obj[0], args[0], args[1])
        else:
            self.curves[label] = (plot_obj[0],)

        # Also add to CurveManager if we have the required info
        run_uid = kwargs.get("run_uid")
        y_field = kwargs.get("y_field")
        stream_name = kwargs.get("stream_name")

        if run_uid is not None and y_field is not None:
            # Generate curveID and add to CurveManager
            curveID = self.curveManager.generateCurveID(run_uid, stream_name, y_field)

            # Prepare data for CurveManager
            x_data = args[0] if len(args) >= 2 else None
            y_data = args[1] if len(args) >= 2 else args[0] if len(args) >= 1 else None

            # Extract only style kwargs (exclude metadata that's passed separately)
            style_kwargs = {
                k: v
                for k, v in plot_kwargs.items()
                if k not in ["run_uid", "y_field", "stream_name"]
            }

            self.curveManager.addCurve(
                curveID=curveID,
                plot_obj=plot_obj[0],
                x_data=x_data,
                y_data=y_data,
                label=label,
                style_kwargs=style_kwargs,
                run_uid=run_uid,
                y_field=y_field,
                stream_name=stream_name,
            )
            logger.debug(
                f"Added curve to CurveManager: curveID={curveID}, curves_count={len(self.curveManager.curves())}"
            )

    def _getCurveIDFromLabel(self, label):
        """
        Find the curveID for a given display label.

        Parameters:
            label (str): The display label (e.g., "scan_id (uid[:7]) - y_field")

        Returns:
            str or None: The curveID if found, None otherwise
        """
        if not hasattr(self, "curveManager"):
            return None

        # Search through CurveManager curves to find matching label
        for curveID, curve_info in self.curveManager.curves().items():
            if curve_info.get("label") == label:
                return curveID
        return None

    # ==========================================
    #   Plot management
    # ==========================================

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
            self.updateBasicMathInfo(label)

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

    # ==========================================
    #   Live Plotting Methods
    # ==========================================

    def enableLiveMode(self, run, stream_name, data_fields, field_widget=None):
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
        self.field_widget = field_widget

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
            self.live_timer.setSingleShot(False)  # Make it repeating
            self.live_timer.timeout.connect(self.refreshPlot)
        else:
            logger.info("Reusing existing QTimer")
            if self.live_timer.isActive():
                logger.info("Stopping existing timer before restarting")
                self.live_timer.stop()

        self.live_timer.start(self.update_interval)
        logger.info(f"Live updates started (interval: {self.update_interval}ms)")
        logger.info(
            f"Timer active: {self.live_timer.isActive()}, singleShot: {self.live_timer.isSingleShot()}"
        )

    def stopLiveUpdates(self):
        """Stop the live update timer."""
        if self.live_timer:
            self.live_timer.stop()

        self.live_mode = False
        logger.info("Live updates stopped")

    def refreshPlot(self):
        """Refresh the plot with latest data from the active run."""
        logger.info(
            f"refreshPlot called: live_run={self.live_run is not None}, live_mode={self.live_mode}"
        )

        if not self.live_run or not self.live_mode:
            logger.info(
                "refreshPlot: returning early - no live_run or live_mode disabled"
            )
            return

        try:
            logger.info("Refreshing plot data...")
            # Re-fetch metadata to check if still active
            if not self.live_run.is_active:
                logger.info("Run completed, stopping live updates")
                self.stopLiveUpdates()
                self.setPlotSubtitle("Run completed")
                return

            # Force refresh stream data to get latest
            try:
                stream_data = self.live_run.force_refresh_stream_data(
                    self.live_stream_name, raw=True
                )
                if stream_data is None:
                    logger.debug(
                        "Live stream data not yet aligned; skipping this refresh cycle"
                    )
                    return
            except ValueError as e:
                if "conflicting sizes" in str(e).lower():
                    # This happens when data is being acquired and fields have different lengths
                    # Just skip this update - the next one should work when data is consistent
                    logger.warning(
                        f"Data fields have inconsistent sizes during acquisition, skipping this update: {e}"
                    )
                    return
                else:
                    raise

            # Also refresh field selection data if it exists
            if hasattr(self, "field_widget") and self.field_widget:
                try:
                    self.field_widget.refreshFieldData()
                except RuntimeError:
                    # Widget was deleted, clear reference
                    logger.debug("field_widget was deleted, clearing reference")
                    self.field_widget = None

            # Update each curve
            for label, (x_field, y_field) in self.live_data_fields.items():
                # Get curveID from label
                curveID = self._getCurveIDFromLabel(label)
                if not curveID:
                    logger.warning(f"Label {label} not found in CurveManager")
                    continue

                curve_info = self.curveManager.getCurveData(curveID)
                if not curve_info:
                    logger.warning(f"Curve {curveID} not found in CurveManager")
                    continue

                plot_obj = self.curveManager.getCurvePlotObj(curveID)
                style_kwargs = curve_info.get("style_kwargs", {})

                # Get new data - stream_data is already the data dict (not wrapped in "data")
                try:
                    if x_field not in stream_data or y_field not in stream_data:
                        logger.debug(
                            f"Missing fields for live update: {x_field=} {y_field=}"
                        )
                        continue

                    x_data = numpy.asarray(stream_data[x_field])
                    y_data = numpy.asarray(stream_data[y_field])

                    if (
                        x_data.ndim != 0
                        and y_data.ndim != 0
                        and len(x_data) != len(y_data)
                    ):
                        min_len = min(len(x_data), len(y_data))
                        logger.debug(
                            f"Trimming live data for {label}: x={len(x_data)} points, y={len(y_data)} points -> {min_len}"
                        )
                        x_data = x_data[:min_len]
                        y_data = y_data[:min_len]

                except KeyError as e:
                    logger.error(
                        f"Field {e} not found in stream data. Available keys: {list(stream_data.keys()) if hasattr(stream_data, 'keys') else 'unknown'}"
                    )
                    continue

                # Check if data shapes have changed
                try:
                    # Try to update the existing plot object
                    # set_data expects (x, y) as two separate arguments
                    plot_obj.set_data(x_data, y_data)
                    # Update CurveManager with new data
                    self.curveManager.updateCurve(
                        curveID=curveID, plot_obj=plot_obj, x_data=x_data, y_data=y_data
                    )
                    self.updateBasicMathInfo(curveID)
                except (ValueError, TypeError) as e:
                    if "shape" in str(e).lower() or "dimension" in str(e).lower():
                        logger.info(
                            f"Data shape changed for {label}, recreating plot: {e}"
                        )
                        # Data shape changed, need to recreate the plot
                        # Clear the old plot
                        plot_obj.remove()

                        # Create new plot with same style
                        new_plot = self.main_axes.plot(
                            x_data, y_data, label=label, **style_kwargs
                        )[0]

                        # Update CurveManager with new plot object and data
                        self.curveManager.updateCurve(
                            curveID=curveID,
                            plot_obj=new_plot,
                            x_data=x_data,
                            y_data=y_data,
                        )
                        self.updateBasicMathInfo(curveID)
                    else:
                        logger.error(f"Error updating plot data for {label}: {e}")
                        raise

            # Refresh display
            self.main_axes.relim()
            self.main_axes.autoscale_view()
            self.updateLegend()
            self.canvas.draw()

            # Update timestamp with LIVE indicator
            iso8601 = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
            subtitle = f"LIVE - updated: {iso8601}"
            if self.parent is not None:
                cat_name = self.parent.catalogName() or ""
                subtitle = f"catalog={cat_name!r}  {subtitle}"
            self.setPlotSubtitle(subtitle)

            logger.info(f"Plot refreshed: {len(x_data)} points")

        except Exception as exc:
            # Check if this is a transient error (data inconsistency during acquisition)
            error_str = str(exc).lower()
            if "conflicting sizes" in error_str or (
                "replacement data" in error_str and "shape" in error_str
            ):
                logger.debug(
                    f"Data inconsistency during live update (will retry next cycle): {exc}"
                )
                # Don't stop live updates for this - it's a transient issue
                return
            # Check if this is a deleted widget error - treat as transient
            if "wrapped c/c++ object" in error_str and "has been deleted" in error_str:
                logger.warning(
                    f"Widget was deleted during live update (will retry next cycle): {exc}"
                )
                # Clear invalid references but don't stop - it might be recreated
                if hasattr(self, "field_widget") and self.field_widget:
                    try:
                        # Try to access to see if it's deleted
                        _ = self.field_widget.objectName()
                    except RuntimeError:
                        self.field_widget = None
                return
            # For other errors, log and stop
            logger.error(f"Live update failed: {exc}", exc_info=True)
            self.stopLiveUpdates()
            self.setPlotSubtitle(f"Live update error: {exc}")

    # ==========================================
    #   Basic maths methods
    # ==========================================

    def updateBasicMathInfo(self, curveID):
        if not curveID:
            self.clearBasicMath()
            return
        try:
            x, y = self.curveManager.getCurveXYData(curveID)
            if x is None or y is None:
                self.clearBasicMath()
                return
            stats = self.calculateBasicMath(x, y)
            for i, txt in zip(stats, ["min_text", "max_text", "com_text", "mean_text"]):
                label_widget = self.parent.findChild(QtWidgets.QLabel, txt)
                if label_widget is not None:
                    if isinstance(i, tuple):
                        result = f"({utils.num2fstr(i[0])}, {utils.num2fstr(i[1])})"
                    else:
                        result = f"{utils.num2fstr(i)}" if i else "n/a"
                    label_widget.setText(result)
        except Exception as exc:
            logger.error(f"Error updating basic math from CurveManager: {exc}")
            self.clearBasicMath()

    def clearBasicMath(self):
        for txt in ["min_text", "max_text", "com_text", "mean_text"]:
            label = self.parent.findChild(QtWidgets.QLabel, txt)
            if label is not None:  # Check for None
                label.setText("n/a")

    def calculateBasicMath(self, x_data, y_data):
        x_array = numpy.array(x_data, dtype=float)
        y_array = numpy.array(y_data, dtype=float)
        # Find y_min and y_max
        y_min = numpy.min(y_array)
        y_max = numpy.max(y_array)
        # Find the indices of the min and max y value
        y_min_index = numpy.argmin(y_array)
        y_max_index = numpy.argmax(y_array)
        # Find the corresponding x values for y_min and y_max
        x_at_y_min = x_array[y_min_index]
        x_at_y_max = x_array[y_max_index]
        # Calculate x_com and y_mean
        x_com = (
            numpy.sum(x_array * y_array) / numpy.sum(y_array)
            if numpy.sum(y_array) != 0
            else None
        )
        y_mean = numpy.mean(y_array)
        return (x_at_y_min, y_min), (x_at_y_max, y_max), x_com, y_mean

    # ==========================================
    #   Cursors methods
    # ==========================================

    # def onRemoveCursor(self, cursor_num):
    #     cross = self.cursors.get(cursor_num)
    #     if cross is not None:
    #         try:
    #             cross.remove()
    #         except (NotImplementedError, AttributeError):
    #             # Handle case where artist cannot be removed
    #             pass
    #         self.cursors[cursor_num] = None
    #         self.cursors[f"pos{cursor_num}"] = None
    #         self.cursors[f"text{cursor_num}"] = (
    #             "middle click or alt+right click" if cursor_num == 1 else "right click"
    #         )
    #     self.cursors["diff"] = "n/a"
    #     self.cursors["midpoint"] = "n/a"
    #     self.updateCursorInfo()
    #     # Recompute the axes limits and autoscale:
    #     self.main_axes.relim()
    #     self.main_axes.autoscale_view()
    #     self.canvas.draw()

    # def clearCursors(self):
    #     self.onRemoveCursor(1)
    #     self.onRemoveCursor(2)

    # def onSnapCursorsToggled(self, checked):
    #     """Handle snap cursors checkbox toggle.

    #     Parameters:
    #         checked (bool): True if checkbox is checked (snap enabled), False if unchecked (snap disabled)
    #     """
    #     self._snap_to_curve = checked

    # def findNearestPoint(
    #     self, x_click: float, y_click: float
    # ) -> Optional[tuple[float, float]]:
    #     """
    #     Find the nearest data point in the selected curve to the given click position.

    #     Parameters:
    #     - x_click: X coordinate of the click
    #     - y_click: Y coordinate of the click

    #     Returns:
    #     - Tuple of (x_nearest, y_nearest) if a curve is selected and has data, None otherwise
    #     """
    #     curveID = self.getSelectedCurveID()
    #     if not curveID or curveID not in self.curveManager.curves():
    #         return None

    #     curve_data = self.curveManager.getCurveData(curveID)
    #     if not curve_data:
    #         return None

    #     ds = curve_data.get("ds")
    #     if not ds or len(ds) < 2:
    #         return None

    #     x_data = ds[0]
    #     y_data = ds[1]

    #     # Ensure data are numpy arrays
    #     if not isinstance(x_data, numpy.ndarray):
    #         x_data = numpy.array(x_data, dtype=float)
    #     if not isinstance(y_data, numpy.ndarray):
    #         y_data = numpy.array(y_data, dtype=float)

    #     # Apply offset and factor to y_data to match what's displayed
    #     factor = curve_data.get("factor", 1)
    #     offset = curve_data.get("offset", 0)
    #     y_data = numpy.multiply(y_data, factor) + offset

    #     # Calculate distances to all points
    #     distances = numpy.sqrt((x_data - x_click) ** 2 + (y_data - y_click) ** 2)

    #     # Find the index of the nearest point
    #     nearest_index = numpy.argmin(distances)

    #     return (float(x_data[nearest_index]), float(y_data[nearest_index]))

    # def onclick(self, event):
    #     # Check if the click was in the main_axes
    #     if event.inaxes is self.main_axes:
    #         # Determine cursor position based on snap setting
    #         if self._snap_to_curve:
    #             # Find the nearest point in the selected curve
    #             nearest_point = self.findNearestPoint(event.xdata, event.ydata)

    #             if nearest_point is None:
    #                 # No curve selected or no data available
    #                 return

    #             x_cursor, y_cursor = nearest_point
    #         else:
    #             # Use exact click position
    #             x_cursor, y_cursor = event.xdata, event.ydata

    #         # Middle click or Alt+right click for red cursor (cursor 1)
    #         if event.button == MIDDLE_BUTTON or (
    #             event.button == RIGHT_BUTTON and self.alt_pressed
    #         ):
    #             if self.cursors[1] is not None:
    #                 try:
    #                     self.cursors[1].remove()  # Remove existing red cursor
    #                 except (NotImplementedError, AttributeError):
    #                     # Handle case where artist cannot be removed
    #                     pass
    #             (self.cursors[1],) = self.main_axes.plot(
    #                 x_cursor, y_cursor, "r+", markersize=15, linewidth=2
    #             )
    #             # Update cursor position
    #             self.cursors["pos1"] = (x_cursor, y_cursor)

    #         # Right click (without Alt) for blue cursor (cursor 2)
    #         elif event.button == RIGHT_BUTTON and not self.alt_pressed:
    #             if self.cursors[2] is not None:
    #                 try:
    #                     self.cursors[2].remove()  # Remove existing blue cursor
    #                 except (NotImplementedError, AttributeError):
    #                     # Handle case where artist cannot be removed
    #                     pass
    #             (self.cursors[2],) = self.main_axes.plot(
    #                 x_cursor, y_cursor, "b+", markersize=15, linewidth=2
    #             )

    #             # Update cursor position
    #             self.cursors["pos2"] = (x_cursor, y_cursor)

    #         # Update the info panel with cursor positions
    #         self.calculateCursors()

    #         # Redraw the canvas to display the new markers
    #         self.canvas.draw()

    # def calculateCursors(self):
    #     """
    #     Update cursor information in info panel widget.
    #     """
    #     # Check for the first cursor and update text accordingly
    #     if self.cursors[1]:
    #         x1, y1 = self.cursors["pos1"]
    #         self.cursors["text1"] = f"({utils.num2fstr(x1)}, {utils.num2fstr(y1)})"
    #     # Check for the second cursor and update text accordingly
    #     if self.cursors[2]:
    #         x2, y2 = self.cursors["pos2"]
    #         self.cursors["text2"] = f"({utils.num2fstr(x2)}, {utils.num2fstr(y2)})"
    #     # Calculate differences and midpoints only if both cursors are present
    #     if self.cursors[1] and self.cursors[2]:
    #         delta_x = x2 - x1
    #         delta_y = y2 - y1
    #         midpoint_x = (x1 + x2) / 2
    #         midpoint_y = (y1 + y2) / 2
    #         self.cursors["diff"] = (
    #             f"({utils.num2fstr(delta_x)}, {utils.num2fstr(delta_y)})"
    #         )
    #         self.cursors["midpoint"] = (
    #             f"({utils.num2fstr(midpoint_x)}, {utils.num2fstr(midpoint_y)})"
    #         )
    #     self.updateCursorInfo()

    # def updateCursorInfo(self):
    #     self.mda_mvc.mda_file_viz.pos1_text.setText(self.cursors["text1"])
    #     self.mda_mvc.mda_file_viz.pos2_text.setText(self.cursors["text2"])
    #     self.mda_mvc.mda_file_viz.diff_text.setText(self.cursors["diff"])
    #     self.mda_mvc.mda_file_viz.midpoint_text.setText(self.cursors["midpoint"])

    # def clearCursorInfo(self):
    #     self.mda_mvc.mda_file_viz.pos1_text.setText("middle click or alt+right click")
    #     self.mda_mvc.mda_file_viz.pos2_text.setText("right click")
    #     self.mda_mvc.mda_file_viz.diff_text.setText("n/a")
    #     self.mda_mvc.mda_file_viz.midpoint_text.setText("n/a")


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
