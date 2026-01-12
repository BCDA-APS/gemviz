"""
QWidget to select stream data fields for plotting.

.. autosummary::

    ~SelectFieldsWidget
    ~to_datasets
"""

import datetime
import logging

import numpy
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

    def __init__(self, parent, run, preferred_stream=None, preferred_fields=None):
        self.parent = parent
        self.run = run  # tapi.RunMetadata object
        self.preferred_fields = preferred_fields
        self.preferred_stream = preferred_stream
        self.table_view = None

        # Force refresh of run data to get latest shapes
        if run.is_active:
            logger.info(f"Refreshing active run {run.uid[:7]} for field selection")
            # Note: is_active force refresh the run metadata

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

        # Determine which stream to use: preferred_stream if available, otherwise default
        stream_to_use = self.stream_name  # Default from analysis (set in __init__)
        if self.preferred_stream and self.preferred_stream in stream_list:
            stream_to_use = self.preferred_stream

        if len(stream_list) > 0:
            # Add items to combobox & setup connection
            self.streams.clear()
            self.streams.addItems(stream_list)
            self.streams.currentTextChanged.connect(self.setStream)

            # Select the desired stream in the combobox
            self.streams.blockSignals(True)
            index = stream_list.index(stream_to_use)
            self.streams.setCurrentIndex(index)
            self.streams.blockSignals(False)

            self.setStream(stream_to_use)

    def setStream(self, stream_name):
        from functools import partial

        self.stream_name = stream_name
        stream = self.run.run[stream_name]
        logger.debug("stream_name=%s, stream=%s", stream_name, stream)

        x_names = self.analysis["plot_axes"]
        y_name = self.analysis["plot_signal"]

        # Check if we have an existing table with fields
        has_existing_table = (
            self.table_view is not None
            and hasattr(self.table_view, "tableView")
            and self.table_view.tableView.model() is not None
            and len(self.table_view.tableView.model().fields()) > 0
        )

        # describe the data fields for the dialog.
        try:
            sdf = self.run.stream_data_fields(stream_name)
            # print(f"{__name__}.{__class__.__name__}: {sdf=}")
        except Exception as exc:
            # If we can't get fields and we have an existing table, skip rebuild
            if has_existing_table:
                logger.debug(
                    f"Could not get fields for {stream_name}: {exc}, "
                    "skipping rebuild to avoid empty flash"
                )
                return
            # If no existing table, we need to try building one
            sdf = []

        fields = []
        # Get preferred fields for this stream (if any)
        preferred_x = None
        preferred_y = []
        if self.preferred_fields is not None:
            preferred_x = self.preferred_fields.get("X")
            preferred_y = self.preferred_fields.get("Y", [])

        # Check if any preferred Y detectors exist in current scan
        has_preferred_x = False
        if preferred_x:
            has_preferred_x = preferred_x is not None and preferred_x in sdf

        has_preferred_y = False
        if preferred_y:
            has_preferred_y = any(field in sdf for field in preferred_y)

        for field_name in sdf:
            selection = None
            # First check if this field is in preferred selections (remembered from previous scan)
            if self.preferred_fields is not None:
                if preferred_x is not None and field_name == preferred_x:
                    selection = "X"
                elif field_name in preferred_y:
                    selection = "Y"
                # Fall back to default X if preferred_x is not in sdf
                elif (
                    not has_preferred_x
                    and x_names is not None
                    and field_name in x_names
                ):
                    selection = "X"
                # Fall back to default Y only if none of preferred_y exist in sdf
                elif (
                    not has_preferred_y and y_name is not None and field_name == y_name
                ):
                    selection = "Y"

            # Fall back to default selections if not in preferred
            else:
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

        # Check if any fields have valid (non-empty) shapes
        # If all fields have empty shapes, they're not readable yet (Container objects)
        has_readable_fields = any(len(field.shape) > 0 for field in fields)

        # If no readable fields AND we have an existing table, skip rebuild
        if not has_readable_fields and has_existing_table:
            logger.debug(
                f"No readable fields available for {stream_name} (all have empty shapes), "
                "skipping rebuild to avoid empty flash"
            )
            return

        # build the view of this stream
        view = SelectFieldsTableView(self)
        self.table_view = view
        view.displayTable(STREAM_COLUMNS, fields)
        view.selected.connect(partial(self.relayPlotSelections, stream_name))

        layout = self.groupbox.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(view)

    def relayPlotSelections(self, stream_name, action, selections):
        """Receive selections from the dialog and relay to the caller."""
        # selections["stream_name"] = self.stream_name
        self.selected.emit(stream_name, action, selections)

    def refreshFieldData(self):
        """Refresh the field data to get latest shapes."""
        if self.run.is_active:
            logger.info(f"Refreshing field data for active run {self.run.uid[:7]}")
            # Note: is_active force refresh the run metadata

            # Remember which fields are currently selected (if we have a table).
            saved = {}
            if self.table_view is not None:
                try:
                    model = self.table_view.tableView.model()
                    if model is not None:
                        saved = model.plotFields()
                except RuntimeError:
                    # Widget was deleted, skip saving selections
                    logger.debug("table_view widget was deleted, skipping save")
                    self.table_view = None
                    saved = {}

            # Rebuild the table for the current stream using fresh data.
            # setStream() will check if fields are readable before rebuilding
            current_stream = self.stream_name
            self.setStream(current_stream)

            # Restore the previous selections on the new model.
            if self.table_view is not None and saved:
                try:
                    model = self.table_view.tableView.model()
                    if model is not None:
                        fields = model.fields()
                        x_field = saved.get("X")
                        if x_field and x_field in fields:
                            model.setSelectionsItem(fields.index(x_field), "X")
                        for y_field in saved.get("Y", []):
                            if y_field in fields:
                                model.setSelectionsItem(fields.index(y_field), "Y")
                        model.updateCheckboxes()
                except RuntimeError:
                    logger.debug(
                        "table_view widget was deleted during restore, skipping"
                    )
                    self.table_view = None
        else:
            logger.info(
                f"Skipping field refresh: run {self.run.uid[:7]} is no longer active"
            )


def to_datasets(run, stream_name, selections, scan_id=None):
    """Prepare datasets and options for plotting."""
    from . import chartview

    # Return empty datasets if stream_name is not provided
    if not stream_name or stream_name == "":
        return [], {}

    try:
        # For active runs, read raw arrays to avoid shape mismatches
        if run.is_active:
            logger.info(f"Force refreshing stream data for active run {run.uid[:7]}")
            stream = run.force_refresh_stream_data(stream_name, raw=True)
        else:
            stream = run.stream_data(stream_name)
    except KeyError as exc:
        logger.error(f"Stream {stream_name} not found in run data: {exc}")
        raise ValueError(f"Stream {stream_name} not found in run data")
    except Exception as exc:
        logger.error(f"Error reading stream {stream_name}: {exc}")
        raise ValueError(f"Error reading stream {stream_name}: {exc}") from exc

    raw_stream = isinstance(stream, dict)
    if stream is None or (raw_stream and not stream):
        raise ValueError("Stream data not yet available for live run.")

    def get_field_array(field_name):
        try:
            if raw_stream:
                data = numpy.asarray(stream[field_name])
            else:
                data_obj = stream[field_name]
                if hasattr(data_obj, "compute"):
                    data_obj = data_obj.compute()
                data = numpy.asarray(getattr(data_obj, "data", data_obj))
        except Exception as exc:
            logger.error(f"Error reading data for {field_name}: {exc}")
            available = list(stream.keys()) if hasattr(stream, "keys") else "unknown"
            logger.error(f"Stream data keys: {available}")
            raise ValueError(f"Error reading field '{field_name}': {exc}") from exc

        return data

    x_axis = selections.get("X")
    x_datetime = False  # special scaling using datetime
    if x_axis is None:
        x_data = None
        x_units = ""
        x_axis = "data point number"
    else:
        x_data = get_field_array(x_axis)
        x_shape = x_data.shape
        x_units = run.stream_data_field_units(stream_name, x_axis)
        if len(x_shape) != 1:
            raise ValueError(
                "Can only plot 1-D data now." f" {x_axis} shape is {x_shape}"
            )
        if x_axis == "time" and numpy.min(x_data) > chartview.TIMESTAMP_LIMIT:
            x_units = ""
            x_datetime = True
            x_data = numpy.array(
                list(map(datetime.datetime.fromtimestamp, numpy.asarray(x_data)))
            )

    datasets = []
    y_selections = selections.get("Y", [])
    if len(y_selections) == 0:
        raise ValueError("No Y data selected.")
    for y_axis in y_selections:
        ds, ds_options = [], {}
        color = chartview.auto_color()
        symbol = chartview.auto_symbol()

        try:
            y_data = get_field_array(y_axis)
            y_units = run.stream_data_field_units(stream_name, y_axis)
            y_shape = y_data.shape
            if len(y_shape) != 1:
                # fmt: off
                raise ValueError(
                    "Can only plot 1-D data now."
                    f" {y_axis} shape is {y_shape}"
                )
        except Exception as exc:
            raise ValueError(f"Failed to get fresh data for {y_axis}: {exc}")

        # keys used here must match the plotting back-end (matplotlib)
        scan_id = run.get_run_md("start", "scan_id")
        # verbose labels
        # ds_options["label"] = f"{y_axis} ({run.summary()} {run.uid[:7]})"
        # terse labels
        ds_options["label"] = f"{scan_id} ({run.uid[:7]}) - {y_axis}"
        ds_options["color"] = color  # line color
        ds_options["marker"] = symbol
        ds_options["markersize"] = 5  # default: 10

        # Add metadata for CurveManager
        ds_options["run_uid"] = run.uid
        ds_options["y_field"] = y_axis  # y_axis is the field name
        ds_options["stream_name"] = stream_name

        if x_data is None:
            ds = [y_data]  # , title=f"{y_axis} v index"
        else:
            if x_shape != y_shape:
                raise ValueError(
                    "Cannot plot.  Different shapes for"
                    f" X ({x_shape!r})"
                    f" and Y ({y_shape!r}) data."
                )
            # Sort by x_data to avoid artifacts when data is not in order
            # (happens with batch_size=1 incremental writes)
            sort_indices = numpy.argsort(x_data)
            x_data = x_data[sort_indices]
            y_data = y_data[sort_indices]

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
