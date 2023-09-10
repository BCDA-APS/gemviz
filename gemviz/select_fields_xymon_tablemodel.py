"""
Select X, Y, and Mon data fields for 1-D plotting: QAbstractTableModel.

General plot model is: Y/Mon vs X.  If X is not selected, use index number. If
Mon is not selected, use 1.0 (trivial case, do not divide by Mon).

When Model/View is created, the view should call 'model.setFields(fields)' with
the list of field names for selection.  (If 'fields' is a different structure,
such a 'list(object)' or 'dict(str=object)', then change both 'columns()' and
'fields()' so that each returns 'list(str)'.)  Note that
'model.setFields(fields)' can only be called once.

.. autosummary::

    ~SelectXYMonTableModel
"""

import logging

from PyQt5 import QtCore

logger = logging.getLogger(__name__)


class SelectXYMonTableModel(QtCore.QAbstractTableModel):
    """
    Bluesky catalog for QtCore.QAbstractTableModel.

    https://doc.qt.io/qtforpython-5/PySide2/QtCore/QAbstractTableModel.html
    """

    _columns = "Field X Y Mon Description PV".split()  # a constant list
    checkboxColumns = (1, 2, 3)

    def __init__(self, fields):
        self.selections = {}  # dict(row_number=column number}
        self._fields_locked = False
        self.setFields(fields)
        self._fields_locked = True

        super().__init__()
        self.updateCheckboxes()

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        """Number of fields."""
        value = len(self.fields())
        return value

    def columnCount(self, parent=None):
        """Number of columns."""
        value = len(self.columns())
        return value

    def data(self, index, role=None):
        if role == QtCore.Qt.CheckStateRole:
            if index.column() in self.checkboxColumns:
                return self.checkbox(index)
        elif role == QtCore.Qt.DisplayRole:
            row, column = index.row(), index.column()
            if column == 0:
                return self.fieldName(row)
            if column not in [0] + list(self.checkboxColumns):
                return self.fieldParameter(row, column)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnName(section)
            else:
                return str(section + 1)  # may want to alter at some point

    # ------------ checkbox methods

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole:
            if index.column() in self.checkboxColumns:
                self.setCheckbox(index, value)
                return True
        return False

    def flags(self, index):
        original_flags = super().flags(index)
        if index.column() in self.checkboxColumns:
            # use a checkbox in this column
            return original_flags | QtCore.Qt.ItemIsUserCheckable
        return original_flags

    def checkbox(self, index):
        """Return the checkbox state."""
        nm = self.columnName(index.column())  # selection name of THIS column
        selection = self.selections.get(index.row())  # user selection
        return QtCore.Qt.Checked if selection == nm else QtCore.Qt.Unchecked

    def setCheckbox(self, index, state):
        """
        Set the checkbox state.

        Selection Rules:

        1. A data field selection could have one of four states: unselected
           (`None`), `"X"`, `"Y"`, or `"Mon"`.
        2. Only zero or one data field can be selected as `"X"`.
        3. Only zero or one data field can be selected as `"Mon"`.
        4. One or more data fields can be selected as `"Y"`.

        """
        row, column = index.row(), index.column()
        column_name = self.columnName(column)
        checked = state == QtCore.Qt.Checked
        prior = self.selections.get(row)
        self.selections[row] = column_name if checked else None  # Rule 1
        changes = self.selections[row] != prior
        logger.debug("selections: %s", self.selections)

        # Apply selection rules 2-4.
        if checked:
            for r, v in sorted(self.selections.items()):
                if v in ("X", "Mon"):
                    if r != row and column_name == v:
                        self.selections[r] = None
                        changes = True

        if changes:
            self.updateCheckboxes()

        self.logCheckboxSelections()
        logger.debug(self.plotFields())  # plotter should call plotFields()

    def updateCheckboxes(self):
        """Update checkboxes to agree with self.selections."""
        top = min(self.selections)
        left = min(self.checkboxColumns)
        bottom = max(self.selections)
        right = max(self.checkboxColumns)
        logger.debug("corners: (%d,%d)  (%d,%d)", top, left, bottom, right)

        # Re-evaluate the checkboxes bounded by the two corners (inclusive).
        corner1 = self.index(top, left)
        corner2 = self.index(bottom, right)
        self.dataChanged.emit(corner1, corner2, [QtCore.Qt.CheckStateRole])

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

    def plotFields(self):
        """
        Return dictionary with the selected fields to be plotted.

        key=column_name, value=field_name(s)
        """
        choices = dict(Y=[])
        for row, column_name in self.selections.items():
            field = self.fieldName(row)
            if column_name in ("X", "Mon"):
                choices[column_name] = field  # only one choice
            elif column_name == "Y":
                choices[column_name].append(field)  # one or more
        return choices

    # ------------ local methods

    def columnName(self, column):
        return self.columns()[column]

    def columns(self):
        return self._columns  # return list(str)

    def fieldName(self, row):
        return self.fields()[row]

    def fieldParameter(self, row, column):
        fname = self.fieldName(row)
        cname = self.columnName(column)
        # assume self._fields[fname][cname] is text
        return self._fields[fname].get(cname, "")

    def fields(self):
        return list(self._fields.keys())  # return list(str)

    def setFields(self, fields):
        if self._fields_locked:
            raise RuntimeError("Once defined, cannot change fields.")
        self._fields = fields

        # Pre-select fields with columns
        # fields is dict(str=object) where object is column name or None
        for k, obj in fields.items():
            v = obj.get("select")
            if v in ("X", "Y", "Mon"):
                self.selections[self.fields().index(k)] = v
