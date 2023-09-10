"""
QTableView of tiled "BlueskyStream" signals.

BSS: BlueskyStreamSignals

Uses :class:`bluesky_stream_signals_table_model.BSSTableModel`.

.. autosummary::

    ~BSSTableView
"""

# from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import utils


class BSSTableView(QtWidgets.QWidget):
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

    def displayTable(self):
        from .bluesky_stream_signals_table_model import BSSTableModel

        run = None  # TODO:
        data_model = BSSTableModel(run)
        self.tableView.setModel(data_model)

    def setStatus(self, text):
        self.parent.setStatus(text)
