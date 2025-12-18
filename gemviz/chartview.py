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
from .fit_manager import FitManager

MIDDLE_BUTTON = 2
RIGHT_BUTTON = 3

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
        self._log_x = False
        self._log_y = False

        # Initialize CurveManager
        self.curveManager = CurveManager(self)
        self.curveManager.curveAdded.connect(self.onCurveAdded)
        self.curveManager.curveUpdated.connect(self.onCurveUpdated)
        self.curveManager.curveRemoved.connect(self.onCurveRemoved)
        self.curveManager.allCurvesRemoved.connect(self.onAllCurvesRemoved)

        # Initialize FitManager
        self.fitManager = FitManager(self)
        self.fitManager.fitAdded.connect(self.onFitAdded)
        self.fitManager.fitUpdated.connect(self.onFitUpdated)
        self.fitManager.fitRemoved.connect(self.onFitRemoved)
        # Track fit plot objects (dict mapping curveID to fit Line2D objects)
        self.fitObjects = {}  #

        # Access UI elements from parent BRCRunVisualization
        if self.parent is not None:
            # Connect curve combobox
            self.curveBox = self.parent.brc_run_viz.curveBox
            self.curveBox.clear()  # Clear any old curves from previous ChartView
            self.curveBox.currentIndexChanged.connect(self.onCurveSelected)

            # Definition clear/remove buttons
            self.clearAll = self.parent.brc_run_viz.clearAll
            self.curveRemove = self.parent.brc_run_viz.curveRemove
            self.removeCursor1 = self.parent.brc_run_viz.cursor1_remove
            self.removeCursor2 = self.parent.brc_run_viz.cursor2_remove

            # Connect clear/remove buttons
            self.clearAll.clicked.connect(self.onClearAllClicked)
            self.curveRemove.clicked.connect(self.onCurveRemoveClicked)
            self.removeCursor1.clicked.connect(lambda: self.onRemoveCursor(1))
            self.removeCursor2.clicked.connect(lambda: self.onRemoveCursor(2))

            # Connect offset & factor QLineEdit:
            self.offset_value = self.parent.brc_run_viz.offset_value
            self.factor_value = self.parent.brc_run_viz.factor_value
            self.offset_value.editingFinished.connect(self.onOffsetFactorChanged)
            self.factor_value.editingFinished.connect(self.onOffsetFactorChanged)

            # Connect snap cursor checkbox (default to free placement)
            self._snap_to_curve = False
            self.snapCursors = self.parent.brc_run_viz.snapCursors
            self.snapCursors.setChecked(self._snap_to_curve)
            self.snapCursors.toggled.connect(self.onSnapCursorsToggled)

            # Connect derivative checkbox (default to False)
            self._derivative = False
            self.derivativeCheckBox = self.parent.brc_run_viz.derivativeCheckBox
            self.derivativeCheckBox.setChecked(self._derivative)
            self.derivativeCheckBox.toggled.connect(self.onDerivativeToggled)

            # Definition fit UI elements
            self.fitModelCombo = self.parent.brc_run_viz.fitModelCombo
            self.fitButton = self.parent.brc_run_viz.fitButton
            self.clearFitsButton = self.parent.brc_run_viz.clearFitsButton
            self.useFitRangeCheck = self.parent.brc_run_viz.useFitRangeCheck
            self.fitDetails = self.parent.brc_run_viz.fitDetails
            self.fitDetails.clear()

            # Populate fit model combo box with available models
            from .fit_models import get_available_models

            available_models = get_available_models()
            self.fitModelCombo.clear()
            self.fitModelCombo.addItems(list(available_models.keys()))

            # Connect fit button to handler
            self.fitButton.clicked.connect(self.onFitButtonClicked)
            self.clearFitsButton.clicked.connect(self.onClearFitClicked)

        else:
            self.curveBox = None
            self.factor_value = None
            self.offset_value = None
            self.derivativeCheckBox = None
            self.fitModelCombo = None
            self.fitButton = None
            self.clearFitsButton = None
            self.useFitRangeCheck = None
            self.fitDetails = None

        # Initially disable fit buttons (no curve selected yet)
        self.updateFitButtonStates()

        # Connect the click event to a handler
        self.cid = self.canvas.mpl_connect("button_press_event", self.onclick)
        self.alt_pressed = False
        # Set up a timer to check modifier key state
        self.key_check_timer = QtCore.QTimer()
        self.key_check_timer.timeout.connect(self.check_modifier_keys)
        self.key_check_timer.start(50)  # Check every 50ms

        # Initialize cursor storage
        self.cursors = {
            1: None,
            "pos1": None,
            "text1": "middle click or alt+right click",
            2: None,
            "pos2": None,
            "text2": "right click",
            "diff": "n/a",
            "midpoint": "n/a",
        }

        # Maths & statistics
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

    def onCurveAdded(self, curveID):
        """Handle the addition of a new curve on the plot."""
        if self.curveBox is None:
            return
        curve_info = self.curveManager.getCurveData(curveID)
        if curve_info:
            label = curve_info.get("label", curveID)
            self.curveBox.addItem(label, curveID)
            # Always select the newly added curve
            self.curveBox.setCurrentIndex(self.curveBox.count() - 1)
        # Update fit button states (new curve is auto-selected)
        self.updateFitButtonStates()

    def onCurveUpdated(self, curveID):
        """Handle updates to an existing curve on the plot."""
        pass

    def onCurveRemoved(self, curveID, curve_data, count):
        """Handle the removal of an existing curve on the plot."""
        # Remove fit if this curve had one
        if self.fitManager.hasFit(curveID):
            self.fitManager.removeFit(curveID)
            # RemoveFit will emit fitRemoved signal which calls onFitRemoved
            # which will handle removing the plot line and redrawing

        if self.curveBox is None:
            return

        # Block signals to prevent currentIndexChanged from firing during removal
        # This prevents the combo box from getting into an inconsistent state
        self.curveBox.blockSignals(True)

        try:
            # Find and remove the item with this curveID
            for i in range(self.curveBox.count()):
                if self.curveBox.itemData(i) == curveID:
                    self.curveBox.removeItem(i)
                    break
        finally:
            # Always unblock signals, even if an exception occurs
            self.curveBox.blockSignals(False)

        # Select first remaining curve if one exists
        # currentIndexChanged signal triggers onCurveSelected if index changes
        # If index didn't change (signal didn't fire), call onCurveSelected manually
        if self.curveBox.count() > 0:
            current_index = self.curveBox.currentIndex()
            self.curveBox.setCurrentIndex(0)
            if self.curveBox.currentIndex() == current_index:
                self.onCurveSelected(0)
        else:
            # No curves remaining - clear basic math
            self.clearBasicMath()
            self.clearTransformations()

        # Update fit button states
        self.updateFitButtonStates()

    def onAllCurvesRemoved(self):
        """Handle the removal of all curves on the plot."""
        # Remove any existing fit
        for curveID in list(self.fitObjects.keys()):
            if self.fitManager.hasFit(curveID):
                self.fitManager.removeFit(curveID)

        if self.curveBox is not None:
            self.curveBox.clear()

        if self.fitDetails is not None:
            self.fitDetails.clear()

        # Disable fit buttons when no curves remain
        self.updateFitButtonStates()
        self.clearTransformations()

    def onCurveSelected(self, index):
        """Handle curve selection change in combobox."""
        if self.curveBox is None or index < 0:
            self.updateFitButtonStates()
            self.clearBasicMath()
            return
        # Get curveID from combobox item data
        curveID = self.curveBox.itemData(index)
        if curveID:
            # Update basic math stats for the selected curve
            self.updateBasicMathInfo(curveID)
            # Populate offset and factor values for the selected curve
            curve_info = self.curveManager.getCurveData(curveID)
            if curve_info:
                offset = curve_info.get("offset", 0.0)
                factor = curve_info.get("factor", 1.0)
                derivative = curve_info.get("derivative", False)
                if self.offset_value and self.factor_value and self.derivativeCheckBox:
                    self.offset_value.setText(str(offset))
                    self.factor_value.setText(str(factor))
                    self.derivativeCheckBox.setChecked(derivative)
        # Update fit button states
        self.updateFitButtonStates()

    def onCurveRemoveClicked(self):
        """Handle Remove Curve button click."""
        if self.curveBox is None or self.curveBox.count() == 0:
            return

        # Get the currently selected curve
        current_index = self.curveBox.currentIndex()
        if current_index < 0:  # if comboBox empty
            return

        curveID = self.curveBox.itemData(current_index)
        if curveID is None:
            return

        # Get the plot object reference
        plot_obj = self.curveManager.getCurvePlotObj(curveID)

        # Remove from CurveManager (will emit curveRemoved signal)
        self.curveManager.removeCurve(curveID)

        # Remove plot object from axes
        if plot_obj is not None:
            plot_obj.remove()

        # Generate title from remaining curves and update plot
        scan_ids = set()
        for curveID, curve_info in self.curveManager.curves().items():
            label = curve_info.get("label", "")
            if label:
                scan_id = label.split()[0] if label.split() else ""
                if scan_id:
                    scan_ids.add(scan_id)
        title = f"scan(s):{', '.join(sorted(scan_ids))}" if scan_ids else ""
        self.updatePlot(title)

        # Redraw canvas
        self.canvas.draw()

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

        # Add to CurveManager if we have the required info
        run_uid = kwargs.get("run_uid")
        y_field = kwargs.get("y_field")
        stream_name = kwargs.get("stream_name")

        if run_uid is not None and y_field is not None and stream_name is not None:
            # Generate curveID and add to CurveManager
            curveID = self.curveManager.generateCurveID(run_uid, stream_name, y_field)

            # Prepare data for CurveManager
            x_data = args[0] if len(args) >= 2 else None
            y_data = args[1] if len(args) >= 2 else args[0] if len(args) >= 1 else None

            # Extract only style kwargs (exclude metadata that's passed separately)
            style_kwargs = {
                k: v
                for k, v in kwargs.items()
                if k not in ["label", "run_uid", "y_field", "stream_name"]
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
            return curveID
        else:
            # No metadata - curve is plotted but not added to CurveManager
            # Return None since this curve isn't tracked in CurveManager
            return None

    def getCurveIDFromLabel(self, label):
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

    def getSelectedCurveID(self):
        """
        Get the ID of the currently selected curve from the combo box.

        Returns:
            str or None: The curve ID of the selected curve if valid, None otherwise.
        """
        if self.curveBox is None:
            return None

        current_index = self.curveBox.currentIndex()
        if current_index >= 0:
            curveID = self.curveBox.itemData(current_index)
            # Validate that curve exists in manager
            if curveID and curveID in self.curveManager.curves():
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

        # Check if curve already exists in CurveManager
        run_uid = ds_options.get("run_uid")
        y_field = ds_options.get("y_field")
        stream_name = ds_options.get("stream_name")

        # Determine curveID based on available metadata
        if run_uid and y_field and stream_name:
            curveID = self.curveManager.generateCurveID(run_uid, stream_name, y_field)
            curve_exists = curveID in self.curveManager.curves()
        else:
            curveID = self.getCurveIDFromLabel(label)
            curve_exists = curveID is not None

        # Add curve if it doesn't exist
        if not curve_exists:
            curveID = self.addCurve(*args, title=title, **ds_options)
        if curveID:
            self.updateBasicMathInfo(curveID)

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
        """Update or remove the legend based on current plot handles."""
        labels = self.main_axes.get_legend_handles_labels()[1]
        valid_labels = [label for label in labels if not label.startswith("_")]
        if valid_labels:
            self.main_axes.legend()
        else:
            # Remove legend when no curves with visible labels remain
            # (curves with labels starting with "_" are hidden from legend by matplotlib convention)
            legend = self.main_axes.get_legend()
            if legend is not None:
                legend.remove()

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

    def setLogScales(self, log_x: bool, log_y: bool):
        """
        Set logarithmic scales for X and Y axes.

        Parameters:
        - log_x (bool): Whether to use logarithmic scale for X-axis
        - log_y (bool): Whether to use logarithmic scale for Y-axis
        """
        try:
            # Store the log scale state
            self._log_x = log_x
            self._log_y = log_y

            if log_x:
                self.main_axes.set_xscale("log")
            else:
                self.main_axes.set_xscale("linear")

            if log_y:
                self.main_axes.set_yscale("log")
            else:
                self.main_axes.set_yscale("linear")

            # Redraw the canvas to apply changes
            self.canvas.draw()
        except Exception as exc:
            logger.error(f"Error setting log scales: {exc}")
            # If setting log scale fails (e.g., negative values), revert to linear
            self._log_x = False
            self._log_y = False
            self.main_axes.set_xscale("linear")
            self.main_axes.set_yscale("linear")
            self.canvas.draw()

    def onClearAllClicked(self):
        """Handle Clear Graph button click."""
        # Store current log scale state before clearing
        if self.parent and hasattr(self.parent, "brc_run_viz"):
            stored_log_x, stored_log_y = self.parent.brc_run_viz.getLogScaleState()
        else:
            stored_log_x, stored_log_y = self._log_x, self._log_y

        # Clear the curve manager (will emit allCurvesRemoved signal)
        self.curveManager.removeAllCurves()

        # Clear all plot lines, legend, axis labels, and axes title
        self.main_axes.clear()

        # Clear figure title (suptitle)
        self.figure.suptitle("")

        # Reapply log scale state after clearing
        self.setLogScales(stored_log_x, stored_log_y)

        # Redraw the canvas
        self.canvas.draw()

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
            x_data = (
                None  # Initialize to avoid UnboundLocalError if no curves are updated
            )
            # Get selected curve ID
            selected_curveID = self.getSelectedCurveID()

            for label, (x_field, y_field) in self.live_data_fields.items():
                # Get curveID from label
                curveID = self.getCurveIDFromLabel(label)
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

                    # Get raw data from stream (not transformed)
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

                    # Sort by x_data to avoid artifacts when data is not in order
                    # (happens with batch_size=1 incremental writes in Tiled 0.2.2)
                    if x_data.ndim != 0 and y_data.ndim != 0 and len(x_data) > 0:
                        sort_indices = numpy.argsort(x_data)
                        x_data = x_data[sort_indices]
                        y_data = y_data[sort_indices]

                except KeyError as e:
                    logger.error(
                        f"Field {e} not found in stream data. Available keys: {list(stream_data.keys()) if hasattr(stream_data, 'keys') else 'unknown'}"
                    )
                    continue

                # Check if data shapes have changed
                try:
                    # Update CurveManager with new data
                    # Note: y_data is raw from stream, not transformed.
                    # update_original_data=True will update original_y_data and reapply
                    # any active transformations.
                    self.curveManager.updateCurve(
                        curveID=curveID,
                        plot_obj=plot_obj,
                        x_data=x_data,
                        y_data=y_data,
                        update_original_data=True,
                    )
                except (ValueError, TypeError) as e:
                    if "shape" in str(e).lower() or "dimension" in str(e).lower():
                        logger.info(
                            f"Data shape changed for {label}, recreating plot: {e}"
                        )
                        # Data shape changed, need to recreate the plot
                        # Clear the old plot
                        if plot_obj:
                            plot_obj.remove()

                        # Create new plot with same style
                        new_plot = self.main_axes.plot(
                            x_data, y_data, label=label, **style_kwargs
                        )[0]

                        # Update CurveManager with new plot object and data
                        # Note: y_data is raw from stream, update_original_data=True
                        # will update original_y_data and reapply transformations.
                        self.curveManager.updateCurve(
                            curveID=curveID,
                            plot_obj=new_plot,
                            x_data=x_data,
                            y_data=y_data,
                            update_original_data=True,
                        )
                    else:
                        logger.error(f"Error updating plot data for {label}: {e}")
                        raise

            # Update basic math info for the selected curve after all curves are updated
            if selected_curveID:
                self.updateBasicMathInfo(selected_curveID)

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

            # Only log if at least one curve was successfully updated
            if x_data is not None:
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

    def onOffsetFactorChanged(self):
        """Handle offset or factor value change."""
        if self.curveBox is None:
            return

        current_index = self.curveBox.currentIndex()
        if current_index < 0:
            return

        curveID = self.curveBox.itemData(current_index)
        if curveID is None:
            return

        # Get offset and factor values from UI
        try:
            offset = (
                float(self.offset_value.text()) if self.offset_value.text() else 0.0
            )
        except ValueError:
            offset = 0.0
            # Reset to default if conversion fails
            self.offset_value.setText(str(offset))
            return
        try:
            factor = (
                float(self.factor_value.text()) if self.factor_value.text() else 1.0
            )
        except ValueError:
            factor = 1.0
            # Reset to default if conversion fails
            if self.factor_value:
                self.factor_value.setText(str(factor))
            return

        # Update curve with new offset and factor
        if self.curveManager.updateCurveOffsetFactor(
            curveID, offset=offset, factor=factor
        ):
            # Update basic math info with transformed data
            self.updateBasicMathInfo(curveID)

            # Recompute axes limits and autoscale and redraw canvas
            self.main_axes.relim()
            self.main_axes.autoscale_view()
            self.canvas.draw()

    def updateBasicMathInfo(self, curveID):
        """Update basic math statistics for the selected curve."""
        if not curveID or self.parent is None:
            self.clearBasicMath()
            return

        self.clearBasicMath()

        try:
            x, y = self.curveManager.getCurveXYData(curveID)
            if x is None or y is None:
                return

            basic_stats = self.calculateBasicMath(x, y)
            peak_stats = self.calculateRawDataPeak(curveID)
            if peak_stats:
                basic_stats.update(peak_stats)
            for label_name, stats_value in basic_stats.items():
                self._updateMathLabel(label_name, stats_value)

        except Exception as exc:
            logger.error(f"Error updating basic math from CurveManager: {exc}")
            self.clearBasicMath()

    def _updateMathLabel(self, label_name, stats_value):
        """Update a single math label with formatted value."""
        if self.parent is None:
            return
        label_widget = self.parent.findChild(QtWidgets.QLabel, label_name)
        if label_widget is not None:
            formatted_text = self._formatStatValue(stats_value)
            label_widget.setText(formatted_text)

    def _formatStatValue(self, value):
        """Format statistic value for display."""
        if value is None:
            return "n/a"
        if isinstance(value, tuple):
            return f"({utils.num2fstr(value[0])}, {utils.num2fstr(value[1])})"
        return f"{utils.num2fstr(value,3)}"

    def clearBasicMath(self):
        """Clear basic maths text label ('n/a')"""
        if self.parent is None:
            return
        for txt in [
            "min_text",
            "max_text",
            "com_text",
            "mean_text",
            "peak_text",
            "FWHM_text",
            "center_text",
        ]:
            label = self.parent.findChild(QtWidgets.QLabel, txt)
            if label is not None:  # Check for None
                label.setText("n/a")

    def clearTransformations(self):
        """Reset derivative, offset and factor values"""
        self._derivative = False
        if self.derivativeCheckBox:
            self.derivativeCheckBox.setChecked(self._derivative)
        if self.factor_value:
            self.factor_value.setText(str(1.0))
        if self.offset_value:
            self.offset_value.setText(str(0))

    def calculateBasicMath(self, x_data, y_data):
        """Calculate basic curve statistics"""

        x_array = numpy.array(x_data, dtype=float)
        y_array = numpy.array(y_data, dtype=float)
        if len(x_array) == 0 or len(y_array) == 0:
            result = {
                "min_text": None,
                "max_text": None,
                "com_text": None,
                "mean_text": None,
            }
            return result

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
        # Return a dictionary
        result = {
            "min_text": (x_at_y_min, y_min),
            "max_text": (x_at_y_max, y_max),
            "com_text": x_com,
            "mean_text": y_mean,
        }
        return result

    def calculateRawDataPeak(self, curveID: str) -> dict | None:
        """
        Calculate peak characteristics from raw data (not fit), assuming a single
        positive peak on top of a (possibly sloped) baseline.

        Parameters
        ----------
        curveID : str
            ID of the curve.

        Returns
        -------
        dict or None
            Dictionary with keys 'peak_text', 'FWHM_text', 'center_text'
            containing peak position, FWHM width, and center values, or None if
            computation is not possible
        """

        # --- Get curve data from curveManager ---
        curve_info = self.curveManager.getCurveData(curveID)
        if curve_info is None:
            return None

        plot_obj, x_data, y_data = curve_info["data"]

        # --- Convert to numpy arrays ---
        x = numpy.asarray(x_data, dtype=float)
        y = numpy.asarray(y_data, dtype=float)

        # Remove NaNs / infs
        mask = numpy.isfinite(x) & numpy.isfinite(y)
        x = x[mask]
        y = y[mask]

        if x.size < 3 or y.size < 3:
            return None

        # Ensure sorted in x (just in case)
        order = numpy.argsort(x)
        x = x[order]
        y = y[order]

        # Use average of first and last N points (e.g., 10% or min 5 points)
        # n_edge = max(5, len(y) // 10)
        # baseline = 0.5 * (numpy.mean(y[:n_edge]) + numpy.mean(y[-n_edge:]))

        # Positive peak: global maximum above baseline
        peak_idx = numpy.argmax(y)
        y_max = y[peak_idx]
        x_peak = x[peak_idx]
        baseline_at_peak, baseline_value, baseline_coeffs = self.calculateBaseline(
            x, y, x_peak
        )
        baseline = baseline_at_peak
        amplitude = y_max - baseline

        # Reject peaks at boundaries
        if peak_idx == 0 or peak_idx == len(y) - 1:
            return None

        # Require a strictly positive peak
        if amplitude <= 0:
            return None

        # Amplitude vs baseline check
        if amplitude < 0.005 * abs(baseline):
            return None

        # Calculate FWHM and its center
        result = self.calculateFWHM(
            x, y, peak_idx, baseline_coeffs, baseline_value, amplitude
        )

        if result is None:
            return None

        fwhm, fwhm_center = result

        peak_stats = {
            "peak_text": x_peak,
            "FWHM_text": fwhm,
            "center_text": fwhm_center,
        }
        return peak_stats

    def calculateBaseline(self, x, y, x_peak):
        """
        Calculate baseline for peak analysis, handling both sloped and constant baselines.

        Attempts to fit a linear baseline to edge regions of the data (first and last
        10% or minimum 5 points). If the linear fit is not valid or fails, falls back
        to a constant baseline calculated as the median of the lowest values.

        Parameters
        ----------
        x : array-like
            X data array
        y : array-like
            Y data array
        x_peak : float
            X position of the peak where baseline should be evaluated

        Returns
        -------
        tuple
            (baseline_at_peak, baseline_value, baseline_coeffs)
            - baseline_at_peak (float): Baseline value at the peak position
            - baseline_value (float or None): Constant baseline value if sloped fit
            failed, None if sloped fit succeeded
            - baseline_coeffs (array or None): Polynomial coefficients [slope, intercept]
            for linear baseline if fit succeeded, None if constant baseline used
        """
        # Baseline: fit line to edge regions to handle sloped baselines
        n_edge = max(5, len(y) // 10)
        baseline_coeffs = None
        baseline_value = None

        # Try to fit sloped baseline to edges
        if len(y) >= 2 * n_edge:
            x_left = x[:n_edge]
            y_left = y[:n_edge]
            x_right = x[-n_edge:]
            y_right = y[-n_edge:]

            # Check if we have enough unique x values for fitting (need at least 2 distinct x values)
            if len(set(x_left)) > 1 and len(set(x_right)) > 1:
                try:
                    x_edges = numpy.concatenate([x_left, x_right])
                    y_edges = numpy.concatenate([y_left, y_right])
                    coeffs = numpy.polyfit(x_edges, y_edges, 1)

                    # Validate fit: check if residuals are reasonable
                    y_fit = numpy.polyval(coeffs, x_edges)
                    residuals = numpy.abs(y_edges - y_fit)
                    # Accept if median residual is reasonable (< 50% of data std)
                    if numpy.median(residuals) < 0.5 * numpy.std(y_edges):
                        baseline_coeffs = coeffs
                except (numpy.linalg.LinAlgError, ValueError, numpy.RankWarning):
                    pass

        # Fallback to constant baseline (median of lowest or edge average)
        if baseline_coeffs is None:
            sorted_y = numpy.sort(y)
            n_low = max(5, len(sorted_y) // 10)
            baseline_value = numpy.median(sorted_y[:n_low])
            # Alternative: baseline_value = 0.5 * (numpy.mean(y[:n_edge]) + numpy.mean(y[-n_edge:]))

        # Evaluate baseline at peak position for amplitude calculation
        if baseline_coeffs is not None:
            baseline_at_peak = numpy.polyval(baseline_coeffs, x_peak)
        else:
            baseline_at_peak = baseline_value

        return baseline_at_peak, baseline_value, baseline_coeffs

    def calculateFWHM(self, x, y, peak_idx, baseline_coeffs, baseline_value, amplitude):
        """
        Find left/right intersection with half-level, handling sloped baselines.

        Parameters
        ----------
        x, y : array-like
            Data arrays
        peak_idx : int
            Index of peak
        baseline_coeffs : array or None
            Polynomial coefficients for sloped baseline [slope, intercept] or None
        baseline_value : float or None
            Constant baseline value (used if baseline_coeffs is None)
        amplitude : float
            Peak amplitude above baseline

        Returns
        -------
        tuple or None
            (fwhm, fwhm_center) or None if FWHM cannot be determined
        """
        # Helper function to evaluate baseline at any x position
        if baseline_coeffs is not None:

            def baseline_at(x_pos):
                return numpy.polyval(baseline_coeffs, x_pos)

        else:

            def baseline_at(x_pos):
                return baseline_value

        # Helper function to evaluate half-level at any x position
        def half_level_at(x_pos):
            return baseline_at(x_pos) + 0.5 * amplitude

        # Search backwards from peak to find the closest crossing
        left_x = None
        for i in range(peak_idx - 1, -1, -1):
            if i + 1 >= len(y):
                continue
            y1, y2 = y[i], y[i + 1]
            x1, x2 = x[i], x[i + 1]

            # Evaluate half_level at segment midpoint for comparison
            x_mid = 0.5 * (x1 + x2)
            half_level = half_level_at(x_mid)

            # Check for crossing
            if y1 <= half_level < y2:
                denom = y2 - y1
                if denom == 0:
                    continue
                # Linear interpolation to find crossing point
                t = (half_level - y1) / denom
                x_cross = x1 + t * (x2 - x1)

                # For sloped baseline, refine by re-evaluating at crossing point
                if baseline_coeffs is not None:
                    half_level_refined = half_level_at(x_cross)
                    # Iterate once for better accuracy
                    t = (half_level_refined - y1) / denom
                    x_cross = x1 + t * (x2 - x1)

                left_x = x_cross
                break  # Found closest crossing, stop searching

        # Find right intersection with half_level (closest crossing after peak)
        right_x = None
        for i in range(peak_idx, len(y) - 1):
            y1, y2 = y[i], y[i + 1]
            x1, x2 = x[i], x[i + 1]

            x_mid = 0.5 * (x1 + x2)
            half_level = half_level_at(x_mid)

            # Crossing from above to below (or at) half_level
            if y1 >= half_level > y2:
                denom = y2 - y1
                if denom == 0:
                    continue

                t = (half_level - y1) / denom
                x_cross = x1 + t * (x2 - x1)

                if baseline_coeffs is not None:
                    half_level_refined = half_level_at(x_cross)
                    t = (half_level_refined - y1) / denom
                    x_cross = x1 + t * (x2 - x1)

                right_x = x_cross
                break

        # Validation
        if left_x is None or right_x is None:
            return None

        fwhm = right_x - left_x
        fwhm_center = 0.5 * (left_x + right_x)

        # Ensure FWHM is within data range and reasonable
        x_min, x_max = x[0], x[-1]
        if (
            left_x < x_min
            or right_x > x_max
            or fwhm > 0.9 * (x_max - x_min)
            or fwhm < 0
        ):
            return None

        return fwhm, fwhm_center

    def onDerivativeToggled(self, checked):
        """Handle derivative checkbox toggle.

        Parameters:
            checked (bool): True if checkbox is checked (derivative enabled), False if unchecked (derivative disabled)
        """
        self._derivative = checked
        current_index = self.curveBox.currentIndex()
        if current_index < 0:
            return

        curveID = self.curveBox.itemData(current_index)
        if curveID is None:
            return

        # Update curve with new derivative status
        if self.curveManager.updateCurveDerivative(curveID, derivative=checked):
            # Update basic math info with transformed data:
            self.updateBasicMathInfo(curveID)
            # Recompute axes limits and autoscale and redraw canvas
            self.main_axes.relim()
            self.main_axes.autoscale_view()
            self.canvas.draw()

    # ==========================================
    #   Cursors methods
    # ==========================================

    def onRemoveCursor(self, cursor_num):
        """Remove a cursor from the plot.

        Parameters:
            cursor_num (int): Cursor number to remove (1 or 2)
        """
        cross = self.cursors.get(cursor_num)
        if cross is not None:
            try:
                cross.remove()
            except (NotImplementedError, AttributeError):
                # Handle case where artist cannot be removed
                pass
            self.cursors[cursor_num] = None
            self.cursors[f"pos{cursor_num}"] = None
            self.cursors[f"text{cursor_num}"] = (
                "middle click or alt+right click" if cursor_num == 1 else "right click"
            )
        self.cursors["diff"] = "n/a"
        self.cursors["midpoint"] = "n/a"
        self.updateCursorInfo()
        # Recompute the axes limits and autoscale:
        self.main_axes.relim()
        self.main_axes.autoscale_view()
        self.canvas.draw()

    def clearCursors(self):
        """Clear both cursors from the plot."""
        self.onRemoveCursor(1)
        self.onRemoveCursor(2)

    def onSnapCursorsToggled(self, checked):
        """Handle snap cursors checkbox toggle.

        Parameters:
            checked (bool): True if checkbox is checked (snap enabled), False if unchecked (snap disabled)
        """
        self._snap_to_curve = checked

    def findNearestPoint(
        self, x_click: float, y_click: float
    ) -> tuple[float, float] | None:
        """
        Find the nearest data point in the selected curve to the given click position.

        Parameters:
        - x_click: X coordinate of the click
        - y_click: Y coordinate of the click

        Returns:
        - Tuple of (x_nearest, y_nearest) if a curve is selected and has data, None otherwise
        """
        curveID = self.getSelectedCurveID()
        if not curveID or curveID not in self.curveManager.curves():
            return None

        # Get curve data from CurveManager
        x_data, y_data = self.curveManager.getCurveXYData(curveID)
        if x_data is None or y_data is None:
            return None

        # Ensure data are numpy arrays
        if not isinstance(x_data, numpy.ndarray):
            x_data = numpy.array(x_data, dtype=float)
        if not isinstance(y_data, numpy.ndarray):
            y_data = numpy.array(y_data, dtype=float)

        if len(x_data) == 0 or len(y_data) == 0:
            return None

        # Normalize by axis ranges to account for different scales
        x_range = self.main_axes.get_xlim()
        y_range = self.main_axes.get_ylim()
        x_scale = x_range[1] - x_range[0] if x_range[1] != x_range[0] else 1.0
        y_scale = y_range[1] - y_range[0] if y_range[1] != y_range[0] else 1.0

        # Calculate normalized distances
        dx = (x_data - x_click) / x_scale
        dy = (y_data - y_click) / y_scale
        distances = numpy.sqrt(dx**2 + dy**2)

        # Find the index of the nearest point
        nearest_index = numpy.argmin(distances)

        return (float(x_data[nearest_index]), float(y_data[nearest_index]))

    def onclick(self, event):
        """Handle mouse click events on the plot to place cursors."""
        # Check if the click was in the main_axes
        if event.inaxes is self.main_axes:
            # Determine cursor position based on snap setting
            if self._snap_to_curve:
                # Find the nearest point in the selected curve
                nearest_point = self.findNearestPoint(event.xdata, event.ydata)

                if nearest_point is None:
                    # No curve selected or no data available
                    return

                x_cursor, y_cursor = nearest_point
            else:
                # Use exact click position
                x_cursor, y_cursor = event.xdata, event.ydata

            # Middle click or Alt+right click for red cursor (cursor 1)
            if event.button == MIDDLE_BUTTON or (
                event.button == RIGHT_BUTTON and self.alt_pressed
            ):
                if self.cursors[1] is not None:
                    try:
                        self.cursors[1].remove()  # Remove existing red cursor
                    except (NotImplementedError, AttributeError):
                        # Handle case where artist cannot be removed
                        pass
                plot_result = self.main_axes.plot(
                    x_cursor, y_cursor, "r+", markersize=15, linewidth=2
                )
                self.cursors[1] = plot_result[0]
                # Update cursor position
                self.cursors["pos1"] = (x_cursor, y_cursor)

            # Right click (without Alt) for blue cursor (cursor 2)
            elif event.button == RIGHT_BUTTON and not self.alt_pressed:
                if self.cursors[2] is not None:
                    try:
                        self.cursors[2].remove()  # Remove existing blue cursor
                    except (NotImplementedError, AttributeError):
                        # Handle case where artist cannot be removed
                        pass
                plot_result = self.main_axes.plot(
                    x_cursor, y_cursor, "b+", markersize=15, linewidth=2
                )
                self.cursors[2] = plot_result[0]
                # Update cursor position
                self.cursors["pos2"] = (x_cursor, y_cursor)

            # Update the info panel with cursor positions
            self.calculateCursors()

            # Redraw the canvas to display the new markers
            self.canvas.draw()

    def check_modifier_keys(self):
        """Check for modifier keys using Qt's global state."""
        try:
            # Get the global keyboard state
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            self.alt_pressed = bool(modifiers & QtCore.Qt.AltModifier)
        except Exception:
            # Fallback if Qt method fails
            pass

    def calculateCursors(self):
        """
        Update cursor information in info panel widget.
        """
        # Check for the first cursor and update text accordingly
        if self.cursors[1] and self.cursors["pos1"] is not None:
            x1, y1 = self.cursors["pos1"]
            self.cursors["text1"] = f"({utils.num2fstr(x1)}, {utils.num2fstr(y1)})"
        # Check for the second cursor and update text accordingly
        if self.cursors[2] and self.cursors["pos2"] is not None:
            x2, y2 = self.cursors["pos2"]
            self.cursors["text2"] = f"({utils.num2fstr(x2)}, {utils.num2fstr(y2)})"
        # Calculate differences and midpoints only if both cursors are present
        if (
            self.cursors[1]
            and self.cursors["pos1"] is not None
            and self.cursors[2]
            and self.cursors["pos2"] is not None
        ):
            delta_x = x2 - x1
            delta_y = y2 - y1
            midpoint_x = (x1 + x2) / 2
            midpoint_y = (y1 + y2) / 2
            self.cursors["diff"] = (
                f"({utils.num2fstr(delta_x)}, {utils.num2fstr(delta_y)})"
            )
            self.cursors["midpoint"] = (
                f"({utils.num2fstr(midpoint_x)}, {utils.num2fstr(midpoint_y)})"
            )
        self.updateCursorInfo()

    def updateCursorInfo(self):
        """Update the cursor info UI labels."""
        if self.parent is None:
            return
        self.parent.brc_run_viz.pos1_text.setText(self.cursors["text1"])
        self.parent.brc_run_viz.pos2_text.setText(self.cursors["text2"])
        self.parent.brc_run_viz.diff_text.setText(self.cursors["diff"])
        self.parent.brc_run_viz.midpoint_text.setText(self.cursors["midpoint"])

    def clearCursorInfo(self):
        """Clear the cursor info UI labels."""
        if self.parent is None:
            return
        self.parent.brc_run_viz.pos1_text.setText("middle click or alt+right click")
        self.parent.brc_run_viz.pos2_text.setText("right click")
        self.parent.brc_run_viz.diff_text.setText("n/a")
        self.parent.brc_run_viz.midpoint_text.setText("n/a")

    def getCursorRange(self):
        """
        Get the range defined by the cursors.

        Returns:
        - Tuple of (x_min, x_max) if both cursors are set, None otherwise
        """
        pos1 = self.cursors.get("pos1")
        pos2 = self.cursors.get("pos2")
        if pos1 is not None and pos2 is not None:
            x1, y1 = pos1
            x2, y2 = pos2
            return (min(x1, x2), max(x1, x2))
        return None

    # ==========================================
    #   Fit methods
    # ==========================================

    def updateFitButtonStates(self) -> None:
        """Update enabled/disabled state of fit buttons based on curve selection."""
        if self.fitButton is None or self.clearFitsButton is None:
            return

        # Enable buttons if a curve is selected
        has_selection = (
            self.curveBox is not None
            and self.curveBox.count() > 0
            and self.curveBox.currentIndex() >= 0
        )

        self.fitButton.setEnabled(has_selection)
        self.clearFitsButton.setEnabled(has_selection)

    def updateFitDetails(self, curveID: str) -> None:
        """
        Update the fit details display.

        Parameters:
        - curveID: ID of the curve
        """
        if self.fitDetails is None:
            return

        # Get fit data
        fit_data = self.fitManager.getFitData(curveID)
        if not fit_data:
            self.fitDetails.clear()
            return

        # Format fit results
        result = fit_data.fit_result
        curve_info = self.curveManager.getCurveData(curveID)
        details_text = ""

        # Parameters
        details_text += "Fitting results:\n"
        for param_name, param_value in result.parameters.items():
            uncertainty = result.uncertainties.get(param_name, 0.0)
            details_text += f"  {param_name}: {utils.num2fstr(param_value, 3)}"
            if uncertainty > 0:
                details_text += f" ± {utils.num2fstr(uncertainty, 3)}"
            details_text += "\n"
            if fit_data.model_name == "Gaussian" and param_name == "sigma":
                details_text += f"  FWHM: {utils.num2fstr(2.35482*param_value,3)}"
                details_text += f" ± {utils.num2fstr(2.35482*uncertainty, 3)}\n"
            if fit_data.model_name == "Lorentzian" and param_name == "gamma":
                details_text += f"  FWHM: {utils.num2fstr(2*param_value,3)}"
                details_text += f" ± {utils.num2fstr(2*uncertainty, 3)}\n"

        # Quality metrics
        details_text += "\nQuality Metrics:\n"
        details_text += f"  R²: {utils.num2fstr(result.r_squared,3)}\n"
        details_text += f"  χ²: {utils.num2fstr(result.chi_squared,3)}\n"
        details_text += (
            f"  Reduced χ²: {utils.num2fstr(result.reduced_chi_squared,3)}\n"
        )

        if curve_info:
            # Data transformation
            details_text += "\nData transformation:\n"
            details_text += f"  Derivative: {curve_info['derivative']}\n"
            details_text += f"  Factor: {curve_info['factor']}\n"
            details_text += f"  Offset: {curve_info['offset']}\n"

        self.fitDetails.setText(details_text)

    def onFitAdded(self, curveID: str) -> None:
        """
        Handle when a fit is added to a curve.

        Parameters:
        - curveID: ID of the curve that was fitted
        """
        # Get fit data and plot the fit curve
        fit_data = self.fitManager.getFitCurveData(curveID)
        if fit_data:
            x_fit, y_fit = fit_data
            # Plot fit curve with dashed line style and higher z-order
            fit_line = self.main_axes.plot(
                x_fit, y_fit, "--", alpha=1, linewidth=2, zorder=10
            )[0]
            self.fitObjects[curveID] = fit_line

            # Update fit results
            self.updateFitDetails(curveID)

            # Redraw the canvas
            self.canvas.draw()

    def onFitUpdated(self, curveID: str) -> None:
        """
        Handle when a fit is updated.

        Parameters:
        - curveID: ID of the curve
        """
        # Remove existing fit line if any
        self.onFitRemoved(curveID, False)
        self.onFitAdded(curveID)

    def onFitRemoved(self, curveID: str, redraw: bool = True) -> None:
        """
        Handle when a fit is removed.

        Parameters:
        - curveID: ID of the curve
        """
        # Remove fit line from plot
        if curveID in self.fitObjects:
            try:
                self.fitObjects[curveID].remove()
            except (NotImplementedError, AttributeError):
                pass
            del self.fitObjects[curveID]
            # Clear fit results
            if self.fitDetails is not None:
                self.fitDetails.clear()
            # Redraw the canvas
            if redraw:
                self.canvas.draw()

    def onFitButtonClicked(self) -> None:
        """Handle Fit button click - fit the currently selected curve."""
        # Get the currently selected curve
        curveID = self.getSelectedCurveID()
        if curveID is None:
            return

        # Get curve data
        curve_info = self.curveManager.getCurveData(curveID)
        if curve_info is None:
            QtWidgets.QMessageBox.warning(
                self, "Fit Error", "Could not retrieve curve data."
            )
            return

        # Get transformed x and y data (already has offset/factor/derivative applied)
        plot_obj, x_data, y_data = curve_info["data"]

        # Convert to numpy arrays if needed
        if not isinstance(x_data, numpy.ndarray):
            x_data = numpy.array(x_data, dtype=float)
        if not isinstance(y_data, numpy.ndarray):
            y_data = numpy.array(y_data, dtype=float)

        # Check for valid data
        if len(x_data) == 0 or len(y_data) == 0:
            QtWidgets.QMessageBox.warning(
                self, "Fit Error", "No data available for fitting."
            )
            return

        if len(x_data) != len(y_data):
            QtWidgets.QMessageBox.warning(
                self, "Fit Error", "X and Y data have different lengths."
            )
            return

        # Get selected fit model
        model_name = self.fitModelCombo.currentText()
        if not model_name:
            QtWidgets.QMessageBox.warning(
                self, "Fit Error", "Please select a fit model."
            )
            return

        # Get fit range if "use cursor range" is checked
        x_range = None
        if self.useFitRangeCheck and self.useFitRangeCheck.isChecked():
            x_range = self.getCursorRange()

        try:
            # Clear any existing fit from other curves (only one fit at a time)
            all_curves = list(self.curveManager.curves().keys())
            for other_curve_id in all_curves:
                if other_curve_id != curveID and self.fitManager.hasFit(other_curve_id):
                    self.fitManager.removeFit(other_curve_id)

            # Perform the fit (this will replace any existing fit for the current curve)
            self.fitManager.addFit(curveID, model_name, x_data, y_data, x_range)

        except ValueError as e:
            # Show error message
            QtWidgets.QMessageBox.warning(self, "Fit Error", str(e))

    def onClearFitClicked(self) -> None:
        """Handle Clear Fit button click - remove fit from currently selected curve."""
        # Get the currently selected curve
        curveID = self.getSelectedCurveID()
        if curveID is None:
            # Button should be disabled, but check just in case
            return
        # Clear fit results
        if self.fitDetails is not None:
            self.fitDetails.clear()
        # Remove fit if it exists: curveManager emits fitRemoved signal which trigers onFitRemoved
        if self.fitManager.hasFit(curveID):
            self.fitManager.removeFit(curveID)
        # If no fit exists, silently do nothing (button is enabled when curve selected)


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
