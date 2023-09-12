"""
Select data fields for plotting: QTableView.

Uses :class:`select_fields_tablemodel.SelectFieldsTableModel`.

.. autosummary::

    ~SelectFieldsTableView
"""

from PyQt5 import QtWidgets

from . import utils


class SelectFieldsTableView(QtWidgets.QWidget):
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

        self.addButton.clicked.connect(self.addPlotFields)
        self.removeButton.clicked.connect(self.removePlotFields)
        self.replaceButton.clicked.connect(self.replacePlotFields)

    def displayTable(self, columns, fields):
        from .select_fields_tablemodel import SelectFieldsTableModel

        data_model = SelectFieldsTableModel(columns, fields)
        self.tableView.setModel(data_model)

    def addPlotFields(self):
        """Add selected fields to current plot."""
        print(f"Add: {self.tableView.model().plotFields()=}")
        # TODO:

    def removePlotFields(self):
        """Remove selected fields from current plot."""
        print(f"Remove: {self.tableView.model().plotFields()=}")
        # TODO:

    def replacePlotFields(self):
        """Replace current plot with selected fields."""
        print(f"Replace: {self.tableView.model().plotFields()=}")
        # TODO:
