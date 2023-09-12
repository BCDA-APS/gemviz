"""
Modal QDialog to select stream data fields for plotting.

.. autosummary::

    ~SelectStreamsDialog
"""

import logging
from dataclasses import dataclass

from PyQt5 import QtWidgets

from . import tiled_support as support
from . import utils
from .analyze_run import SignalAxesFields
from .select_fields_tablemodel import ColumnDataType
from .select_fields_tablemodel import FieldRuleType
from .select_fields_tablemodel import TableColumn
from .select_fields_tablemodel import TableField
from .select_fields_tableview import SelectFieldsTableView


@dataclass(frozen=True)
class MyTableField(TableField):
    shape: tuple = ()  # the "Shape" column


logger = logging.getLogger(__name__)
DEFAULT_STREAM = "primary"

STREAM_COLUMNS = [
    TableColumn("Field", ColumnDataType.text),
    TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
    TableColumn("Shape", ColumnDataType.text),
]


class SelectStreamsDialog(QtWidgets.QDialog):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent, run, default_stream=DEFAULT_STREAM):
        self.parent = parent
        self.run = run
        self.analysis = SignalAxesFields(run)
        self.default_stream_name = default_stream

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        summary = support.run_summary(self.run)
        summary_elide = 40
        if len(summary) > summary_elide:  # elide right
            summary = summary[: summary_elide - 4] + " ..."
        self.run_summary.setText(summary)
        self.buttonbox.clicked.connect(self.dismiss)

        stream_list = list(self.run)
        if self.default_stream_name in stream_list:
            # Move the default stream to the first position.
            stream_list.remove(self.default_stream_name)
            stream_list.insert(0, self.default_stream_name)

        if len(stream_list) > 0:
            self.setStream(stream_list[0])

            self.streams.clear()
            self.streams.addItems(stream_list)
            self.streams.currentTextChanged.connect(self.setStream)

    def dismiss(self, button):
        """Close the dialog."""
        self.close()

    def setStream(self, stream_name):
        stream = self.run[stream_name]
        logger.debug("stream_name=%s, stream=%s", stream_name, stream)

        x_name = None
        y_name = None
        if stream_name == self.analysis.stream_name:
            if len(self.analysis.plot_axes) > 0:
                x_name = self.analysis.plot_axes[0]
            y_name = self.analysis.plot_signal

        fields = []
        for field_name in support.stream_data_fields(stream):
            selection = None
            if x_name is not None and field_name == x_name:
                selection = "X"
            elif y_name is not None and field_name == y_name:
                selection = "Y"
            shape = support.stream_data_field_shape(stream, field_name)
            fields.append(MyTableField(field_name, selection=selection, shape=shape))
        logger.debug("fields=%s", fields)

        view = SelectFieldsTableView(self)
        view.displayTable(STREAM_COLUMNS, fields)
        layout = self.groupbox.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(view)
