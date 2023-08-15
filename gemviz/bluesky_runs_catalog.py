"""
MVC implementation of CatalogOfBlueskyRuns.

.. autosummary::

    ~BlueskyRunsCatalogMVC
"""

import time
from functools import partial

from PyQt5 import QtWidgets

import utils


class BlueskyRunsCatalogMVC(QtWidgets.QWidget):
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
        from app_settings import settings
        from filterpanel import FilterPanel
        from bluesky_runs_catalog_table import ResultWindow
        # from vizpanel import VizPanel

        self.filter_panel = FilterPanel(self)
        layout = self.filter_groupbox.layout()
        layout.addWidget(self.filter_panel)
        self.filter_panel.catalogSelected(self.catalog().item["id"])

        self.results = ResultWindow(self)
        layout = self.runs_groupbox.layout()
        layout.addWidget(self.results)
        self.results.displayTable()

        # self.viz = VizPanel(self)
        # layout = self.viz_groupbox.layout()
        # layout.addWidget(self.viz)

        # save/restore splitter sizes in application settings
        self.hsplitter_deadline = 0
        self.hsplitter_wait_thread = None
        self.vsplitter_deadline = 0
        self.vsplitter_wait_thread = None
        for key in "hsplitter vsplitter".split():
            splitter = getattr(self, key)
            sname = self.splitter_settings_name(key)
            settings.restoreSplitter(splitter, sname)
            splitter.splitterMoved.connect(partial(self.splitter_moved, key))

    def catalog(self):
        return self.parent.catalog()

    def splitter_moved(self, key, pos, index):
        setattr(self, f"{key}_deadline", time.time() + self.motion_wait_time)

        thread = getattr(self, f"{key}_wait_thread")
        if thread is None or not thread.is_alive():
            self.setStatus(f"Start new thread now.  {key=}")
            self.hsplitter_wait_thread = self.splitter_wait_changes(key)

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
        from app_settings import settings

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
