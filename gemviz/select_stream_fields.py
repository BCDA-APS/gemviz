"""
QWidget to select stream data fields for plotting.

.. autosummary::

    ~SelectStreamsWidget
    ~to_datasets
"""

import datetime
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


class SelectStreamsWidget(QtWidgets.QWidget):
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
        self.run_summary.setText(tapi.run_summary(self.run))

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


def to_datasets(stream, selections, scan_id=None):
    """Prepare datasets and options for plotting."""
    from . import chartview

    x_axis = selections.get("X")
    x_datetime = False  # special scaling using datetime
    if x_axis is None:
        x_data = None
        x_units = ""
        x_axis = "data point number"
    else:
        x_data = stream["data"][x_axis].compute()
        x_shape = x_data.shape
        x_units = tapi.stream_data_field_units(stream, x_axis)
        if len(x_shape) != 1:
            # fmt: off
            raise ValueError(
                "Can only plot 1-D data now."
                f" {x_axis} shape is {x_shape}"
            )
            # fmt: on
        if x_axis == "time" and min(x_data) > chartview.TIMESTAMP_LIMIT:
            x_units = ""
            x_datetime = True

    datasets = []
    for y_axis in selections.get("Y", []):
        ds, ds_options = [], {}
        color = chartview.auto_color()
        symbol = chartview.auto_symbol()

        y_data = stream["data"][y_axis].compute()
        y_units = tapi.stream_data_field_units(stream, y_axis)
        y_shape = y_data.shape
        if len(y_shape) != 1:
            # fmt: off
            raise ValueError(
                "Can only plot 1-D data now."
                f" {y_axis} shape is {y_shape}"
            )
        suffix = stream.metadata["stream_name"]
        run_uid = stream.metadata["descriptors"][0].get("run_start", "")
        if scan_id is not None:
            suffix = f"#{scan_id} {suffix} {run_uid[:7]}"
        ds_options["name"] = f"{y_axis} ({suffix})"
        ds_options["pen"] = color  # line color
        ds_options["symbol"] = symbol
        ds_options["symbolBrush"] = color  # fill color
        ds_options["symbolPen"] = color  # outline color
        # size in pixels (if pxMode==True, then data coordinates.)
        ds_options["symbolSize"] = 10  # default: 10

        if x_data is None:
            ds = [y_data]  # , title=f"{y_axis} v index"
        else:
            if x_shape != y_shape:
                raise ValueError(
                    "Cannot plot.  Different shapes for"
                    f" X ({x_shape!r})"
                    f" and Y ({y_shape!r}) data."
                )
            ds = [x_data, y_data]
        datasets.append((ds, ds_options))

    plot_options = {
        "x_datetime": x_datetime,
        "x_units": x_units,
        "x": x_axis,
        "y_units": y_units,
        "y": ", ".join(selections.get("Y", [])),
    }

    return datasets, plot_options
