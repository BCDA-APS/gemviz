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
        from .select_fields_xymon_tablemodel import TableField
        from .select_fields_xymon_tablemodel import Select1DTableModel
        from .select_fields_xymon_tablemodel import XY_COLUMNS
        from .select_fields_xymon_tablemodel import STANDARD_COLUMNS

        stream = None  # TODO: Pass as arg?
        # TODO: use data from stream
        fields = [
            TableField("time", description="epoch"),
            TableField("motor", "X", description="some motor"),
            TableField("I", "Y"),
            TableField("I0", "Mon", description="use as monitor", pv="ioc:I0"),
            TableField("I00", "Y"),
            TableField("I000"),
            TableField("scint"),
            TableField("diode"),
            TableField("ROI1"),
            TableField("ROI2"),
            TableField("ROI3"),
        ]

        data_model = Select1DTableModel(STANDARD_COLUMNS, fields)
        self.tableView.setModel(data_model)

    def setStatus(self, text):
        self.parent.setStatus(text)
