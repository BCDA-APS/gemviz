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
        # since we cannot set header's ResizeMode in Designer ...
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.addButton.clicked.connect(self.addPlotFields)
        self.removeButton.clicked.connect(self.removePlotFields)
        self.replaceButton.clicked.connect(self.replacePlotFields)

    def displayTable(self, columns, fields):
        from .select_fields_tablemodel import SelectFieldsTableModel

        data_model = SelectFieldsTableModel(columns, fields)
        self.tableView.setModel(data_model)

    def addPlotFields(self):
        """Signals that selected fields should be added to current plot."""
        self.selected.emit("add", self.tableView.model().plotFields())

    def removePlotFields(self):
        """Signals that selected fields should be removed from current plot."""
        self.selected.emit("remove", self.tableView.model().plotFields())

    def replacePlotFields(self):
        """Signals to replace current plot with selected fields."""
        self.selected.emit("replace", self.tableView.model().plotFields())
