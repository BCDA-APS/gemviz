"""
Select X, Y, and Mon data fields for 1-D plotting: QTableView.

Uses :class:`select_fields_xymon_tablemodel.SelectXYMonTableModel`.

.. autosummary::

    ~SelectXYMonTableView
"""

from PyQt5 import QtWidgets

from . import utils


class SelectXYMonTableView(QtWidgets.QWidget):
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
        from .select_fields_xymon_tablemodel import SelectXYMonTableModel

        run = None  # TODO:
        data_model = SelectXYMonTableModel(run)
        self.tableView.setModel(data_model)

    def setStatus(self, text):
        self.parent.setStatus(text)
