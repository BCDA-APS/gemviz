"""
MVC implementation of CatalogOfBlueskyRuns.

* BRC: BlueskyRunsCatalog
* MVC: Model View Controller

.. autosummary::

    ~BRC_MVC
"""

import time
from functools import partial

import yaml
from PyQt5 import QtWidgets

from . import utils

PAGE_START = 0
PAGE_SIZE = 10


class BRC_MVC(QtWidgets.QWidget):
    """MVC class for CatalogOfBlueskyRuns."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)
    motion_wait_time = 1  # wait for splitter motion to stop to update settings

    def __init__(self, parent):
        self.parent = parent
        self._title_keys = []  # for the plot title

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from .bluesky_runs_catalog_run_viz import BRCRunVisualization
        from .bluesky_runs_catalog_search import BRCSearchPanel
        from .bluesky_runs_catalog_table_view import BRCTableView
        from .user_settings import settings

        self.selected_run_uid = None
        self.current_field_widget = None
        self.last_selected_fields = {}
        self.last_selected_stream = None

        self.brc_search_panel = BRCSearchPanel(self)
        layout = self.tab_filter.layout()
        layout.addWidget(self.brc_search_panel)
        self.brc_search_panel.setupCatalog(self.catalogName())

        self.brc_tableview = BRCTableView(self, self.catalog(), PAGE_START, PAGE_SIZE)
        layout = self.tab_matches.layout()
        layout.addWidget(self.brc_tableview)

        self.brc_run_viz = BRCRunVisualization(self)
        layout = self.viz_groupbox.layout()
        layout.addWidget(self.brc_run_viz)

        # connect search signals with tableview update
        widgets = [
            [self.brc_search_panel.plan_name, "returnPressed"],
            [self.brc_search_panel.scan_id, "returnPressed"],
            [self.brc_search_panel.status, "returnPressed"],
            [self.brc_search_panel.positioners, "returnPressed"],
            [self.brc_search_panel.detectors, "returnPressed"],
            [self.brc_search_panel.date_time_widget.apply, "released"],
        ]
        for widget, signal in widgets:
            getattr(widget, signal).connect(self.refreshFilteredCatalogView)

        self.brc_tableview.run_selected.connect(self.doRunSelectedSlot)
        self.brc_tableview.run_double_selected.connect(self.doRunDoubleClickSlot)

        # save/restore splitter sizes in application settings
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    def catalog(self):
        return self.parent.catalog()

    def catalogName(self):
        return self.parent.catalogName()

    def doPlotSlot(self, run, stream_name, action, selections):
        """Slot: data field selected (for plotting) button is clicked."""
        import logging

        from .chartview import ChartView
        from .select_stream_fields import to_datasets

        logger = logging.getLogger(__name__)

        # TODO: make the plots configurable
        scan_id = run.get_run_md("start", "scan_id")
        # key = f"{scan_id}:{run.uid[:5]}"
        key = f"{scan_id}"

        # setup datasets
        try:
            # Force refresh of run data before plotting to avoid shape mismatches
            if run.is_active:
                logger.info(f"Refreshing active run {run.uid[:7]} before plotting")
                # Note: is_active refreshes metadata

            datasets, options = to_datasets(
                run, stream_name, selections, scan_id=scan_id
            )
        except ValueError as exc:
            self.setStatus(f"No plot: {exc}")
            return

        # get the chartview widget, if exists
        layout = self.brc_run_viz.plotPage.layout()
        if layout.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        old_widget = layout.itemAt(0).widget()

        # Stop any live updates on old widget before replacing
        if isinstance(old_widget, ChartView) and old_widget.live_mode:
            logger.info("Stopping live updates on old widget before replacement")
            old_widget.stopLiveUpdates()

        if not isinstance(old_widget, ChartView) or action == "replace":
            # Make a blank chart
            widget = ChartView(self, **options)
            # Apply stored log scale state to the new chart
            stored_log_x, stored_log_y = self.brc_run_viz.getLogScaleState()
            widget.setLogScales(stored_log_x, stored_log_y)
            self._title_keys = []
            if action == "add":
                action = "replace"
        else:
            widget = old_widget

        if action in ("remove"):
            # Remove this run from the plot
            # TODO: this does not work, remove always removes all curves from the graph
            if key in self._title_keys:
                self._title_keys.remove(key)
                logger.info(f"Removed run {key} from plot")

            # If no runs left, clear the plot completely
            if not self._title_keys:
                logger.info("All runs removed, clearing plot")
                self.setStatus("Plot cleared")
                # Create an empty plot
                widget = ChartView(self, **options)
                self.brc_run_viz.setPlot(widget)
                return

            # For now, just clear the plot when removing runs
            # A more sophisticated implementation would re-plot remaining runs
            logger.info("Plot cleared after removing run")
            self.setStatus(f"Removed run {key} from plot")
            widget = ChartView(self, **options)
            self.brc_run_viz.setPlot(widget)
            return

        if action in ("replace", "add"):
            # Store the selected fields and stream to remember them when switching scans
            self.last_selected_fields[stream_name] = {
                "X": selections.get("X"),  # Can be None
                "Y": selections.get("Y", []).copy(),  # Copy to avoid reference issues
            }
            self.last_selected_stream = stream_name

            if key not in self._title_keys:
                self._title_keys.append(key)
            title = f"scan(s): {', '.join(sorted(self._title_keys))}"
            for ds, ds_options in datasets:
                widget.plot(*ds, title=title, **ds_options)
            self.brc_run_viz.setPlot(widget)

            # Enable live plotting for active runs
            is_active = run.is_active
            logger.info(
                f"Checking live plot eligibility: run={run.uid[:7]}, is_active={is_active}, action={action}"
            )
            if is_active and action == "replace":
                # Build mapping of curve labels to field names for live updates
                x_field = selections.get("X")
                y_fields = selections.get("Y", [])
                logger.info(
                    f"Live plotting setup: x_field={x_field}, y_fields={y_fields}"
                )

                live_data_fields = {}
                for i, (ds, ds_options) in enumerate(datasets):
                    label = ds_options.get("label")
                    # Map each dataset to its corresponding y_field
                    if len(y_fields) > 0 and i < len(y_fields):
                        y_field = y_fields[i]
                        live_data_fields[label] = (x_field, y_field)
                        logger.info(
                            f"Live field mapping: {label} -> ({x_field}, {y_field})"
                        )

                if live_data_fields:
                    logger.info(f"Calling enableLiveMode for run {run.uid[:7]}")
                    logger.info(
                        f"Widget type: {type(widget)}, live_data_fields: {live_data_fields}"
                    )
                    self.setStatus(f"🔴 Live plotting enabled for scan {scan_id}")
                    widget.enableLiveMode(
                        run,
                        stream_name,
                        live_data_fields,
                        field_widget=self.current_field_widget,
                    )
                    logger.info(
                        f"enableLiveMode returned, widget.live_mode={widget.live_mode}, "
                        f"timer_active={widget.live_timer.isActive() if widget.live_timer else False}"
                    )
                else:
                    logger.warning("Could not set up live mode: no data fields mapped")
            else:
                logger.debug(
                    f"Run {run.uid[:7]} is not active or action is not 'replace'"
                )

            if not is_active:
                logger.debug(f"Run {run.uid[:7]} is not active, live mode not enabled")
            elif action != "replace":
                logger.debug(
                    f"Action is {action}, not 'replace', live mode not enabled"
                )

    def doRunSelectedSlot(self, run):
        """
        Slot: run is clicked in the table view.

        run *object*:
            Instance of ``tapi.RunMetadata``
        """
        import logging
        from functools import partial

        from .select_stream_fields import SelectFieldsWidget

        logger = logging.getLogger(__name__)

        # Force refresh of run metadata to get latest data
        if run.is_active:
            logger.info(f"Refreshing active run {run.uid[:7]} to get latest data")
            # Note: is_active refreshes metadata

        self.selected_run_uid = run.get_run_md("start", "uid")

        run_md = run.run_md
        self.brc_run_viz.setMetadata(yaml.dump(dict(run_md), indent=4))
        try:
            self.brc_run_viz.setData(self.getDataDescription(run))
        except (KeyError, ValueError) as exinfo:
            self.setStatus(
                f"Can't select that run: ({exinfo.__class__.__name__}) {exinfo}"
            )
            return
        self.setStatus(run.summary())

        # Clear reference to old widget (if any)
        self.current_field_widget = None

        # Get layout and remove any remaining widgets (safety net)
        layout = self.fields_groupbox.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        # Get remembered stream and selections (if any)
        analysis = run.plottable_signals()
        default_stream_name = analysis.get("stream", "primary")

        # Check if there is a remembered stream
        remembered_stream = None
        remembered_selections = None
        if self.last_selected_stream:
            # Check if the new scan has this stream
            available_streams = list(run.stream_metadata())
            if self.last_selected_stream in available_streams:
                remembered_stream = self.last_selected_stream
                remembered_selections = self.last_selected_fields.get(remembered_stream)

        # If no remembered stream, use default stream and check for remembered selections
        if remembered_stream is None:
            remembered_stream = default_stream_name
            remembered_selections = self.last_selected_fields.get(default_stream_name)

        # Now create the new widget with preferred stream and fields
        widget = SelectFieldsWidget(
            self,
            run,
            preferred_stream=remembered_stream,
            preferred_fields=remembered_selections,
        )
        self.current_field_widget = widget
        widget.selected.connect(partial(self.doPlotSlot, run))
        layout.addWidget(widget)

    def doRunDoubleClickSlot(self, run):
        """
        Slot: run is double clicked in the table view.

        run *object*:
            Instance of ``tapi.RunMetadata``
        """
        import logging
        from functools import partial

        from .select_stream_fields import SelectFieldsWidget

        logger = logging.getLogger(__name__)

        # Force refresh of run metadata to get latest data
        if run.is_active:
            logger.info(f"Refreshing active run {run.uid[:7]} to get latest data")
            # Note: is_active refreshes metadata

        self.selected_run_uid = run.get_run_md("start", "uid")

        run_md = run.run_md
        self.brc_run_viz.setMetadata(yaml.dump(dict(run_md), indent=4))
        try:
            self.brc_run_viz.setData(self.getDataDescription(run))
        except (KeyError, ValueError) as exinfo:
            self.setStatus(
                f"Can't select that run: ({exinfo.__class__.__name__}) {exinfo}"
            )
            return
        self.setStatus(run.summary())

        # Clear reference to old widget (if any)
        self.current_field_widget = None

        # Get layout and remove any remaining widgets (safety net)
        layout = self.fields_groupbox.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        # Get remembered stream and selections (if any)
        analysis = run.plottable_signals()
        default_stream_name = analysis.get("stream", "primary")

        # Check if there is a remembered stream
        remembered_stream = None
        remembered_selections = None
        if self.last_selected_stream:
            # Check if the new scan has this stream
            available_streams = list(run.stream_metadata())
            if self.last_selected_stream in available_streams:
                remembered_stream = self.last_selected_stream
                remembered_selections = self.last_selected_fields.get(remembered_stream)

        # If no remembered stream, use default stream and check for remembered selections
        if remembered_stream is None:
            remembered_stream = default_stream_name
            remembered_selections = self.last_selected_fields.get(default_stream_name)

        # Now create the new widget with preferred stream and fields
        widget = SelectFieldsWidget(
            self,
            run,
            preferred_stream=remembered_stream,
            preferred_fields=remembered_selections,
        )
        self.current_field_widget = widget
        widget.selected.connect(partial(self.doPlotSlot, run))
        layout.addWidget(widget)

        # After widget is created, get current selections and trigger plot
        # (equivalent to clicking the replace button)
        if widget.table_view is not None:
            model = widget.table_view.tableView.model()
            if model is not None:
                selections = model.plotFields()
                stream_name = widget.stream_name
                # Trigger plot with "replace" action
                self.doPlotSlot(run, stream_name, "replace", selections)

    def getDataDescription(self, run):
        """Provide text description of the data streams in the run."""
        import pyRestTable

        # Describe what will be plotted.  Show in the viz panel "Data" tab.
        analysis = run.plottable_signals()
        table = pyRestTable.Table()
        table.labels = "item description".split()
        table.addRow(("scan", run.get_run_md("start", "scan_id")))
        table.addRow(("plan", run.get_run_md("start", "plan_name")))
        if analysis["plot_signal"] is not None:
            table.addRow(("stream", analysis["stream"]))
            table.addRow(("plot signal", analysis["plot_signal"]))
            table.addRow(("plot axes", ", ".join(analysis["plot_axes"])))
            table.addRow(("all detectors", ", ".join(analysis["detectors"])))
            table.addRow(("all positioners", ", ".join(analysis["motors"])))
        text = "plot summary"
        text += "\n" + "-" * len(text) + "\n" * 2
        text += f"{table.reST()}\n"

        # Show information about each stream.
        rows = []
        for sname in run.stream_metadata():
            title = f"stream: {sname}"
            # row = [title, "-" * len(title), str(run.stream_data(sname)), ""]
            rows += [title, "-" * len(title), str(run.stream_data(sname)), ""]

        text += "\n".join(rows).strip()
        return text

    def refreshFilteredCatalogView(self, *args, **kwargs):
        """Update the view with the new filtered catalog."""
        # print(f"{__name__}.{__class__.__name__} {args=} {kwargs=}")
        filtered_catalog = self.brc_search_panel.filteredCatalog()
        self.brc_tableview.setCatalog(filtered_catalog)

    def splitter_moved(self, key, *arg, **kwargs):
        thread = getattr(self, f"{key}_wait_thread", None)
        setattr(self, f"{key}_deadline", time.time() + self.motion_wait_time)
        if thread is None or not thread.is_alive():
            self.setStatus(f"Start new thread now.  {key=}")
            setattr(self, f"{key}_wait_thread", self.splitter_wait_changes(key))

    def splitter_settings_name(self, key):
        """Name to use with settings file for 'key' splitter."""
        return f"{self.__class__.__name__.lower()}_{key}"

    @utils.run_in_thread
    def splitter_wait_changes(self, key):
        """
        Wait for splitter to stop changing before updating settings.

        PARAMETERS

        key *str*:
            Name of splitter (either 'hsplitter' or 'vsplitter')
        """
        from .user_settings import settings

        splitter = getattr(self, key)
        while time.time() < getattr(self, f"{key}_deadline"):
            # self.setStatus(
            #     f"Wait: {time.time()=:.3f}"
            #     f"  {getattr(self, f'{key}_deadline')=:.3f}"
            # )
            time.sleep(self.motion_wait_time * 0.1)

        sname = self.splitter_settings_name(key)
        self.setStatus(f"Update settings: {sname=} {splitter.sizes()=}")
        settings.saveSplitter(splitter, sname)

    def setStatus(self, text):
        self.parent.setStatus(text)


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
