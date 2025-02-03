"""
QWidget to select stream data fields for plotting.

.. autosummary::

    ~SelectFieldsWidget
    ~to_datasets
"""

import datetime
import logging

import xarray
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import utils
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


class SelectFieldsWidget(QtWidgets.QWidget):
    """Panel to select fields (signals) for plotting."""

    ui_file = utils.getUiFileName(__file__)
    selected = QtCore.pyqtSignal(str, str, dict)

    def __init__(self, parent, run):
        self.parent = parent
        self.run = run  # tapi.RunMetadata object
        self.analysis = run.plottable_signals()
        self.stream_name = self.analysis.get("stream", DEFAULT_STREAM)

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        self.run_summary.setText(self.run.summary())

        stream_list = list(self.run.stream_metadata())
        if "baseline" in stream_list:
            # Too many signals! 2 points each.  Do not plot from "baseline" stream.
            stream_list.pop(stream_list.index("baseline"))
        index = stream_list.index(self.stream_name)
        if index > 0:
            # Move the default stream to the first position.
            stream_list.insert(0, stream_list.pop(index))

        if len(stream_list) > 0:
            self.setStream(stream_list[0])

            self.streams.clear()
            self.streams.addItems(stream_list)
            self.streams.currentTextChanged.connect(self.setStream)

    def setStream(self, stream_name):
        from functools import partial

        self.stream_name = stream_name
        stream = self.run.run[stream_name]
        logger.debug("stream_name=%s, stream=%s", stream_name, stream)

        x_names = self.analysis["plot_axes"]
        y_name = self.analysis["plot_signal"]

        # describe the data fields for the dialog.
        sdf = self.run.stream_data_fields(stream_name)
        # print(f"{__name__}.{__class__.__name__}: {sdf=}")
        fields = []
        for field_name in sdf:
            selection = None
            if x_names is not None and field_name in x_names:
                selection = "X"
            elif y_name is not None and field_name == y_name:
                selection = "Y"
            shape = self.run.stream_data_field_shape(stream_name, field_name)
            if len(shape) == 0:
                # print(f"{stream_name=} {field_name=} {shape=}")
                logger.debug(
                    "stream_name=%s field_name=%s shape=%s",
                    stream_name,
                    field_name,
                    shape,
                )
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


def to_datasets(run, stream_name, selections, scan_id=None):
    """Prepare datasets and options for plotting."""
    from . import chartview

    stream = run.stream_data(stream_name)

    x_axis = selections.get("X")
    x_datetime = False  # special scaling using datetime
    if x_axis is None:
        x_data = None
        x_units = ""
        x_axis = "data point number"
    else:
        x_data = stream[x_axis].compute()
        x_shape = x_data.shape
        x_units = run.stream_data_field_units(stream_name, x_axis)
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
            x_data = xarray.DataArray(
                data=list(map(datetime.datetime.fromtimestamp, x_data[x_axis].data)),
                name=x_axis,
                # dims=x_axis,
                # coords=?,
            )

    datasets = []
    y_selections = selections.get("Y", [])
    if len(y_selections) == 0:
        raise ValueError("No Y data selected.")
    for y_axis in y_selections:
        ds, ds_options = [], {}
        color = chartview.auto_color()
        symbol = chartview.auto_symbol()

        y_data = stream[y_axis].compute()
        y_units = run.stream_data_field_units(stream_name, y_axis)
        y_shape = y_data.shape
        if len(y_shape) != 1:
            # fmt: off
            raise ValueError(
                "Can only plot 1-D data now."
                f" {y_axis} shape is {y_shape}"
            )

        # keys used here must match the plotting back-end (matplotlib)
        scan_id = run.get_run_md("start", "scan_id")
        # verbose labels
        # ds_options["label"] = f"{y_axis} ({run.summary()} {run.uid[:7]})"
        # terse labels
        ds_options["label"] = f"{scan_id} ({run.uid[:7]})"
        ds_options["color"] = color  # line color
        ds_options["marker"] = symbol
        ds_options["markersize"] = 5  # default: 10

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


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
