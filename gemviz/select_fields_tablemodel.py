"""
Select data fields for 1-D plotting: QAbstractTableModel.

General plot model is: Y/Mon vs X.  If X is not selected, use index number. If
Mon is not selected, use 1.0 (trivial case, do not divide by Mon).

Data Field Selection Rules:

1. A data field selection could have one of four states:
    * unselected (`None`)
    * `"X"`: ordinate (independent axis)
    * `"Y"` : abcissae (dependent axes)
    * `"Mon"` : divide this array into each Y
2. Only zero or one data field can be selected as `"X"`.
3. Only zero or one data field can be selected as `"Mon"`.
4. One or more data fields can be selected as `"Y"`.

When Model/View is created, the view should call 'model.setFields(fields)' with
the list of field names for selection.  (If 'fields' is a different structure,
such a 'list(object)' or 'dict(str=object)', then change both 'columns()' and
'fields()' so that each returns 'list(str)'.)  Note that
'model.setFields(fields)' can only be called once.

.. autosummary::

    ~SelectFieldsTableModel
    ~ColumnDataType
    ~FieldSelectionRuleType
    ~TableColumn
    ~TableField
"""

import logging
from dataclasses import KW_ONLY
from dataclasses import dataclass

from PyQt5 import QtCore

logger = logging.getLogger(__name__)


class ColumnDataType:
    """Data types expected by TableColumn.column_type."""

    checkbox = "checkbox"
    text = "text"


class FieldRuleType:
    """Data field selection rule types."""

    multiple = "multiple"
    unique = "unique"

    def apply(self, *args, **kwargs):
        """Apply the selection rule."""


@dataclass(frozen=True)
class TableColumn:
    """One column of the table."""

    name: str
    column_type: ColumnDataType
    _: KW_ONLY  # all parameters below are specified by keyword
    rule: (FieldRuleType, None) = None


@dataclass(frozen=True)
class TableField:
    """One data field candidate for user-selection.

    NOTE: Data for the "Description" and "PV" TableColumns is
    provided by the "description" and "pv" attributes here
    using `cname.lower()`.  (FIXME: This could break.  Easily.)
    """

    name: str  # the "Field" column
    selection: (str, None) = None  # either of these, selection rule 1.
    _: KW_ONLY  # all parameters below are specified by keyword
    description: str = ""  # the "Description" column
    pv: str = ""  # the "PV" column
    shape: tuple = ()  # the "Shape" column


# fmt: off
# Example lists of columns & fields.
XY_COLUMNS = [
    TableColumn("Field", ColumnDataType.text),
    TableColumn("X", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("Y", ColumnDataType.checkbox, rule=FieldRuleType.multiple),
]
MDAVIZ_COLUMNS = XY_COLUMNS + [
    TableColumn("Mon", ColumnDataType.checkbox, rule=FieldRuleType.unique),
    TableColumn("Description", ColumnDataType.text),
    TableColumn("PV", ColumnDataType.text),
]
XY_FIELDS = [
    TableField("motor", "X", description="some motor"),
    TableField("I", "Y"),
    TableField("I00", "Y"),
    TableField("scint"),
    TableField("diode"),
]
MDAVIZ_FIELDS = [
    TableField("time", description="epoch"),
    TableField("motor", "X", pv="ioc:m1"),
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
# fmt: on


class SelectFieldsTableModel(QtCore.QAbstractTableModel):
    """
    Select fields for plots.

    .. autosummary::

        ~rowCount
        ~columnCount
        ~data
        ~headerData
        ~setData
        ~flags
        ~checkbox
        ~applySelectionRules
        ~updateCheckboxes
        ~logCheckboxSelections
        ~columnName
        ~columnNumber
        ~columns
        ~setColumns
        ~fieldName
        ~fieldText
        ~fields
        ~setFields
        ~plotFields

    https://doc.qt.io/qtforpython-5/PySide2/QtCore/QAbstractTableModel.html
    """

    def __init__(self, columns, fields):
        self.selections = {}  # dict(row_number=column number}

        self._columns_locked, self._fields_locked = False, False
        self.setColumns(columns)
        self.setFields(fields)
        self._columns_locked, self._fields_locked = True, True

        super().__init__()
        self.updateCheckboxes()

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        """Number of fields."""
        return len(self.fields())

    def columnCount(self, parent=None):
        """Number of columns."""
        return len(self.columns())

    def data(self, index, role=None):
        """Table data.  Called by QTableView."""
        if role == QtCore.Qt.CheckStateRole:
            if index.column() in self.checkboxColumns:
                return self.checkbox(index)
        elif role == QtCore.Qt.DisplayRole:
            if index.column() in self.textColumns:
                return self.fieldText(index)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """Column headers.  Called by QTableView."""
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnName(section)
            else:
                return str(section + 1)  # may want to alter at some point

    def setData(self, index, value, role):
        """Toggle the checkboxes.  Called by QTableView."""
        if role == QtCore.Qt.CheckStateRole:
            if index.column() in self.checkboxColumns:
                self.setCheckbox(index, value)
                return True
        return False

    def flags(self, index):
        """Identify the checkbox cells.  Called by QTableView."""
        original_flags = super().flags(index)
        if index.column() in self.checkboxColumns:
            # use a checkbox in this column
            return original_flags | QtCore.Qt.ItemIsUserCheckable
        return original_flags

    # ------------ checkbox methods

    def checkbox(self, index):
        """Return the checkbox state."""
        nm = self.columnName(index.column())  # selection name of THIS column
        selection = self.selections.get(index.row())  # user selection
        return QtCore.Qt.Checked if selection == nm else QtCore.Qt.Unchecked

    def setCheckbox(self, index, state):
        """Set the checkbox state."""
        row, column = index.row(), index.column()
        column_name = self.columnName(column)
        checked = state == QtCore.Qt.Checked
        prior = self.selections.get(row)
        self.selections[row] = column_name if checked else None  # Rule 1
        changes = self.selections[row] != prior
        logger.debug("selections: %s", self.selections)

        changes = self.applySelectionRules(index, changes)

        if changes:
            self.updateCheckboxes()

        self.logCheckboxSelections()
        logger.debug(self.plotFields())  # plotter should call plotFields()

    def applySelectionRules(self, index, changes=False):
        """Apply selection rules 2-4."""
        row = index.row()
        column_name = self.columnName(index.column())
        for r, v in sorted(self.selections.items()):
            if v is not None:
                if self.columnNumber(v) in self.uniqueSelectionColumns:
                    if r != row and column_name == v:
                        self.selections[r] = None
                        changes = True
        return changes

    def updateCheckboxes(self):
        """Update checkboxes to agree with self.selections."""
        if len(self.selections) > 0:
            top, bottom = min(self.selections), max(self.selections)
        else:
            top, bottom = 0, self.rowCount() - 1
        left, right = min(self.checkboxColumns), max(self.checkboxColumns)
        logger.debug("corners: (%d,%d)  (%d,%d)", top, left, bottom, right)

        # Re-evaluate the checkboxes bounded by the two corners (inclusive).
        corner1 = self.index(top, left)
        corner2 = self.index(bottom, right)
        self.dataChanged.emit(corner1, corner2, [QtCore.Qt.CheckStateRole])

        # prune empty data from self.selections
        # fmt: off
        self.selections = {
            k: v for k, v in self.selections.items() if v is not None
        }
        # fmt: on

    def logCheckboxSelections(self):
        logger.debug("checkbox selections:")
        for r in range(self.rowCount()):
            text = ""
            for c in self.checkboxColumns:
                state = self.checkbox(self.index(r, c))
                choices = {QtCore.Qt.Checked: "*", QtCore.Qt.Unchecked: "-"}
                text += choices[state]
            text += f" {self.fieldName(r)}"
            logger.debug(text)

    # ------------ local methods

    def columnName(self, column: int):
        return self.columns()[column]

    def columnNumber(self, column_name):
        return self.columns().index(column_name)

    def columns(self):
        return list(self._columns)  # return list(str)

    def setColumns(self, columns):
        """Define the columns for the table."""
        if self._columns_locked:
            raise RuntimeError("Once defined, cannot change columns.")

        self._columns = {column.name: column for column in columns}
        # NOTE: list(int), not list(str): column _number_ (not column name)
        self.checkboxColumns = [
            column_number
            for column_number, column in enumerate(columns)
            if column.column_type == ColumnDataType.checkbox
        ]
        self.uniqueSelectionColumns = [
            column_number
            for column_number, column in enumerate(columns)
            if column.column_type == ColumnDataType.checkbox
            if column.rule == FieldRuleType.unique
        ]
        self.multipleSelectionColumns = [
            column_number
            for column_number, column in enumerate(columns)
            if column.column_type == ColumnDataType.checkbox
            if column.rule == FieldRuleType.multiple
        ]
        self.textColumns = [
            column_number
            for column_number, column in enumerate(columns)
            if column.column_type == ColumnDataType.text
        ]

    def fieldName(self, row):
        return self.fields()[row]

    def fieldText(self, index):
        row, column = index.row(), index.column()
        assert column in self.textColumns, f"{column=} is not text"

        fname = self.fieldName(row)
        if column == 0:
            return fname  # special case

        cname = self.columnName(column)
        text = str(getattr(self._fields[fname], cname.lower(), ""))
        return text

    def fields(self):
        """Return a list of the field names."""
        return list(self._fields)  # return list(str)

    def setFields(self, fields):
        """Define the data fields (rows) for the table."""
        if self._fields_locked:
            raise RuntimeError("Once defined, cannot change fields.")
        self._fields = {field.name: field for field in fields}

        # Pre-select fields with columns, where fields is list(Field).
        for row, field in enumerate(fields):
            if field.selection is not None:
                column_number = self.columnNumber(field.selection)
                if column_number in self.checkboxColumns:
                    self.selections[row] = field.selection

    # ------------ reporting

    def plotFields(self):
        """
        Returns a dictionary with the selected fields to be plotted.

        key=column_name, value=field_name(s)
        """
        choices = dict(Y=[])
        for row, column_name in self.selections.items():
            field_name = self.fieldName(row)
            column_number = self.columnNumber(column_name)
            if column_number in self.uniqueSelectionColumns:
                choices[column_name] = field_name
            elif column_number in self.multipleSelectionColumns:
                choices[column_name].append(field_name)
        return choices
