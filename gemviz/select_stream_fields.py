"""
Modal QDialog to select stream data fields for plotting.

.. autosummary::

    ~SelectStreamsDialog
"""

import logging
from dataclasses import dataclass

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import tapi
from . import utils
from .analyze_run import SignalAxesFields
from .select_fields_tablemodel import ColumnDataType
from .select_fields_tablemodel import FieldRuleType
from .select_fields_tablemodel import TableColumn
from .select_fields_tablemodel import TableField
from .select_fields_tableview import SelectFieldsTableView

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
    selected = QtCore.pyqtSignal(str, str, dict)

    def __init__(self, parent, run, default_stream=DEFAULT_STREAM):
        self.parent = parent
        self.run = run
        self.analysis = SignalAxesFields(run)
        self.stream_name = default_stream

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        summary = tapi.run_summary(self.run)
        summary_elide = 40
        if len(summary) > summary_elide:  # elide right
            summary = summary[: summary_elide - 4] + " ..."
        self.run_summary.setText(summary)
        self.buttonbox.clicked.connect(self.dismiss)

        stream_list = list(self.run)
        if self.stream_name in stream_list:
            # Move the default stream to the first position.
            stream_list.remove(self.stream_name)
            stream_list.insert(0, self.stream_name)

        if len(stream_list) > 0:
            self.setStream(stream_list[0])

            self.streams.clear()
            self.streams.addItems(stream_list)
            self.streams.currentTextChanged.connect(self.setStream)

    def dismiss(self, button):
        """Close the dialog."""
        self.close()

    def setStream(self, stream_name):
        from functools import partial

        self.stream_name = stream_name
        stream = self.run[stream_name]
        logger.debug("stream_name=%s, stream=%s", stream_name, stream)

        # TODO: This is for 1-D.  Generalize for multi-dimensional.
        # hint: Checkbox column in the columns table might provide.
        x_name = None
        y_name = None
        if stream_name == self.analysis.stream_name:
            if len(self.analysis.plot_axes) > 0:
                x_name = self.analysis.plot_axes[0]
            y_name = self.analysis.plot_signal

        # describe the data fields for the dialog.
        fields = []
        for field_name in tapi.stream_data_fields(stream):
            selection = None
            if x_name is not None and field_name == x_name:
                selection = "X"
            elif y_name is not None and field_name == y_name:
                selection = "Y"
            shape = tapi.stream_data_field_shape(stream, field_name)
            field = TableField(field_name, selection=selection, shape=shape)
            fields.append(field)
        logger.debug("fields=%s", fields)

        # build the view of this stream
        view = SelectFieldsTableView(self)
        view.displayTable(STREAM_COLUMNS, fields)
        view.selected.connect(partial(self.relayPlotSelections, stream_name))

        layout = self.groupbox.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(view)

    def relayPlotSelections(self, stream_name, action, selections):
        """Receive selections from the dialog and relay to the caller."""
        # selections["stream_name"] = self.stream_name
        self.selected.emit(stream_name, action, selections)
