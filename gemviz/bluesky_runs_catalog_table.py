"""
QTableView of tiled "CatalogOfBlueskyRuns".

Uses :class:`bluesky_runs_catalog_model.TableModel`.

.. autosummary::

    ~ResultWindow
"""

from functools import partial

from PyQt5 import QtCore, QtWidgets

import utils


class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter


class ResultWindow(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        # fmt: off
        widgets = [
            [self.parent.filter_panel.plan_name, "returnPressed",],
            [self.parent.filter_panel.scan_id, "returnPressed",],
            [self.parent.filter_panel.status, "returnPressed",],
            [self.parent.filter_panel.positioners, "returnPressed",],
            [self.parent.filter_panel.detectors, "returnPressed",],
            [self.parent.filter_panel.date_time_widget.apply, "released",],
        ]
        # fmt: on
        for widget, signal in widgets:
            getattr(widget, signal).connect(self.displayTable)

        # since we cannot set header's ResizeMode in Designer ...
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        for button_name in "first back next last".split():
            button = getattr(self, button_name)
            # custom: pass the button name to the receiver
            button.released.connect(partial(self.doPagerButtons, button_name))

        self.pageSize.currentTextChanged.connect(self.doPageSize)
        self.doButtonPermissions()
        self.setPagerStatus()
        self.tableView.doubleClicked.connect(self.doRunSelected)

    def doPagerButtons(self, action, **kwargs):
        # self.setStatus(f"{action=} {kwargs=}")
        model = self.tableView.model()

        if model is not None:
            model.doPager(action)
            self.setStatus(f"{model.pageOffset()=}")
        self.doButtonPermissions()
        self.setPagerStatus()

    def doPageSize(self, value):
        # self.setStatus(f"doPageSize {value =}")
        model = self.tableView.model()

        if model is not None:
            model.doPager("pageSize", value)
        self.doButtonPermissions()
        self.setPagerStatus()

    def doButtonPermissions(self):
        model = self.tableView.model()
        atStart = False if model is None else model.isPagerAtStart()
        atEnd = False if model is None else model.isPagerAtEnd()

        self.first.setEnabled(not atStart)
        self.back.setEnabled(not atStart)
        self.next.setEnabled(not atEnd)
        self.last.setEnabled(not atEnd)

    def displayTable(self):
        from bluesky_runs_catalog_model import TableModel

        self.cat = self.parent.filter_panel.filteredCatalog()
        data_model = TableModel(self.cat)
        # self.setStatus(f"Displaying catalog: {self.cat.item['id']!r}")
        page_size = self.pageSize.currentText()  # remember the current value
        self.tableView.setModel(data_model)
        self.doPageSize(page_size)  # restore
        self.setPagerStatus()
        self.parent.filter_panel.enableDateRange(
            len(self.parent.filter_panel.catalog()) > 0
        )
        labels = data_model.columnLabels

        def centerColumn(label):
            if label in labels:
                column = labels.index(label)
                delegate = _AlignCenterDelegate(self.tableView)
                self.tableView.setItemDelegateForColumn(column, delegate)

        centerColumn("Scan ID")
        centerColumn("#points")

    def setPagerStatus(self, text=None):
        if text is None:
            model = self.tableView.model()
            if model is not None:
                text = model.pagerStatus()

        self.status.setText(text)

    def doRunSelected(self, index):
        model = self.tableView.model()
        if model is not None:
            self.parent.viz.setMetadata(model.getMetadata(index))
            self.parent.viz.setData(model.getDataDescription(index))

    def setStatus(self, text):
        self.parent.setStatus(text)
