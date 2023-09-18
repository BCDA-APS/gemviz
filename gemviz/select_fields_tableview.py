"""
Select data fields for plotting: QTableView.

Uses :class:`select_fields_tablemodel.SelectFieldsTableModel`.

.. autosummary::

    ~SelectFieldsTableView
"""

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import utils


class SelectFieldsTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)
    selected = QtCore.pyqtSignal(str, dict)

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from functools import partial

        # since we cannot set header's ResizeMode in Designer ...
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.addButton.clicked.connect(partial(self.responder, "add"))
        self.removeButton.clicked.connect(partial(self.responder, "remove"))
        self.replaceButton.clicked.connect(partial(self.responder, "replace"))

    def displayTable(self, columns, fields):
        from .select_fields_tablemodel import SelectFieldsTableModel

        data_model = SelectFieldsTableModel(columns, fields)
        self.tableView.setModel(data_model)

    def responder(self, action):
        """Modify the plot with the described action."""
        self.selected.emit(action, self.tableView.model().plotFields())
