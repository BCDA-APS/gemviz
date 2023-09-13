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

from . import tapi
from . import utils

logger = logging.getLogger(__name__)


class _AlignCenterDelegate(QtWidgets.QStyledItemDelegate):
    """https://stackoverflow.com/a/61722299"""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter


class BRCTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)
    run_selected = QtCore.pyqtSignal(object)

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
        self.tableView.clicked.connect(self.doRunSelectedSlot)

    def doPagerButtons(self, action, **kwargs):
        # self.setStatus(f"{action=} {kwargs=}")
        model = self.tableView.model()

        if model is not None:
            try:
                model.doPager(action)
                self.setStatus(f"{model.pageOffset()=}")
                self.doButtonPermissions()
                self.setPagerStatus()
            except tapi.TiledServerError as exc:
                self.setStatus(str(exc))
                dialog = QtWidgets.QMessageBox(self)
                dialog.setWindowTitle("Notice")
                dialog.setIcon(dialog.Warning)
                dialog.setText(f"Error when paging.\n{exc}")
                dialog.exec()

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

    def doRunSelectedSlot(self, index):
        model = self.tableView.model()
        if model is not None:
            self.run_selected.emit(model.indexToRun(index))

    def setStatus(self, text):
        self.parent.setStatus(text)
