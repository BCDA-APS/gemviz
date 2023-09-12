"""
QTableView of tiled "CatalogOfBlueskyRuns".

BRC: BlueskyRunsCatalog

Uses :class:`bluesky_runs_catalog_table_model.BRCTableModel`.

.. autosummary::

    ~BRCTableView
"""

import logging
from functools import partial

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import utils

logger = logging.getLogger(__name__)


class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter


class BRCTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
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
        self.tableView.clicked.connect(self.doPopup)

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
        from .bluesky_runs_catalog_table_model import BRCTableModel

        self.cat = self.parent.brc_search_panel.filteredCatalog()
        data_model = BRCTableModel(self.cat)
        # self.setStatus(f"Displaying catalog: {self.cat.item['id']!r}")
        page_size = self.pageSize.currentText()  # remember the current value
        self.tableView.setModel(data_model)
        self.doPageSize(page_size)  # restore
        self.setPagerStatus()
        self.parent.brc_search_panel.enableDateRange(
            len(self.parent.brc_search_panel.catalog()) > 0
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
        self.setStatus(text)

    def doDescribeRun(self, index):
        model = self.tableView.model()
        if model is not None:
            self.parent.brc_run_viz.setMetadata(model.getMetadata(index))
            self.parent.brc_run_viz.setData(model.getDataDescription(index))
            self.setStatus(model.getSummary(index))

    def doPopup(self, index):
        from functools import partial

        logger.debug("index=%s", index)
        r, c = index.row(), index.column()
        logger.debug("row=%s  column=%s", r, c)
        pos_local = QtCore.QPoint(
            self.tableView.rowViewportPosition(r),
            self.tableView.columnViewportPosition(c),
        )
        logger.debug("pos_local=%s", pos_local)
        pos_global = self.tableView.mapToGlobal(pos_local)
        logger.debug("pos_global=%s", pos_global)
        popup = QtWidgets.QMenu(self.tableView)
        popup.addAction("Select")
        popup.addAction("Describe")
        popup.addAction("Plot")
        popup.triggered.connect(partial(self.doPopupResponse, index=index))
        popup.popup(pos_global, popup.actions()[0])

    def doPopupResponse(self, action, index=None):
        handlers = {
            "Describe": self.doDescribeRun,
            "Plot": self.doPlotRun,
            "Select": None,  # nothing special here
        }
        handler = handlers.get(action.text())
        if handler is not None:
            handler(index)

    def doPlotRun(self, index):
        from .select_stream_fields import SelectStreamsDialog

        model = self.tableView.model()
        if model is not None:
            dialog = SelectStreamsDialog(self, model.indexToRun(index))
            dialog.selected.connect(self.doPlotResponse)
            dialog.exec()

    def doPlotResponse(self, action, selections):
        print(f"doPlotResponse({action=}, {selections=})")

    def setStatus(self, text):
        self.parent.setStatus(text)
