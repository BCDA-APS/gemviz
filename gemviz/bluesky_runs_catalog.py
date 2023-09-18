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

from . import tapi
from . import utils


class BRC_MVC(QtWidgets.QWidget):
    """MVC class for CatalogOfBlueskyRuns."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)
    motion_wait_time = 1  # wait for splitter motion to stop to update settings

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from .bluesky_runs_catalog_run_viz import BRCRunVisualization
        from .bluesky_runs_catalog_search import BRCSearchPanel
        from .bluesky_runs_catalog_table_view import BRCTableView
        from .user_settings import settings

        self.brc_search_panel = BRCSearchPanel(self)
        layout = self.filter_groupbox.layout()
        layout.addWidget(self.brc_search_panel)
        self.brc_search_panel.setupCatalog(self.catalogName())

        self.brc_tableview = BRCTableView(self)
        layout = self.runs_groupbox.layout()
        layout.addWidget(self.brc_tableview)
        self.brc_tableview.displayTable()

        self.brc_run_viz = BRCRunVisualization(self)
        layout = self.viz_groupbox.layout()
        layout.addWidget(self.brc_run_viz)

        # connect search signals with tableview update
        # fmt: off
        widgets = [
            [self.brc_search_panel.plan_name, "returnPressed"],
            [self.brc_search_panel.scan_id, "returnPressed"],
            [self.brc_search_panel.status, "returnPressed"],
            [self.brc_search_panel.positioners, "returnPressed"],
            [self.brc_search_panel.detectors, "returnPressed"],
            [self.brc_search_panel.date_time_widget.apply, "released"],
        ]
        # fmt: on
        for widget, signal in widgets:
            getattr(widget, signal).connect(self.brc_tableview.displayTable)

        self.brc_tableview.run_selected.connect(self.doRunSelectedSlot)

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
        from .chartview import ChartView
        from .select_stream_fields import to_datasets

        # TODO: make the plots configurable
        scan_id = tapi.get_md(run, "start", "scan_id")

        # setup datasets
        datasets, options = to_datasets(run[stream_name], selections, scan_id=scan_id)

        # get the chartview widget, if exists
        layout = self.brc_run_viz.plotPage.layout()
        if layout.count() != 1:  # in case something changes ...
            raise RuntimeError("Expected exactly one widget in this layout!")
        widget = layout.itemAt(0).widget()
        if not isinstance(widget, ChartView) or action == "replace":
            widget = ChartView(self, **options)  # Make a blank chart.
            if action == "add":
                action == "replace"

        if action in ("remove"):  # TODO: implement "remove"
            raise ValueError(f"Unsupported action: {action=}")

        if action in ("replace", "add"):
            for ds, ds_options in datasets:
                widget.plot(*ds, **ds_options)
            self.brc_run_viz.setPlot(widget)

    def doRunSelectedSlot(self, run):
        """Slot: run is clicked in the table view."""
        from functools import partial

        from .select_stream_fields import SelectStreamsWidget

        self.brc_run_viz.setMetadata(yaml.dump(dict(run.metadata), indent=4))
        self.brc_run_viz.setData(tapi.run_description_table(run))
        self.setStatus(tapi.run_summary(run))

        widget = SelectStreamsWidget(self, run)
        widget.selected.connect(partial(self.doPlotSlot, run))
        layout = self.fields_groupbox.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(widget)

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
