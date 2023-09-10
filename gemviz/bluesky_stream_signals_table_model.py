"""
QAbstractTableModel of tiled "BlueskyStream".

BSS: BlueskyStreamSignals

.. autosummary::

    ~BSSTableModel
"""

import logging

from PyQt5 import QtCore

logger = logging.getLogger(__name__)


class BSSTableModel(QtCore.QAbstractTableModel):
    """
    Bluesky catalog for QtCore.QAbstractTableModel.

    https://doc.qt.io/qtforpython-5/PySide2/QtCore/QAbstractTableModel.html
    """

    _columns = "Signal X Y Mon".split()  # a constant list
    checkboxColumns = (1, 2, 3)

    def __init__(self, run):
        # TODO: get signals from run
        # This is an example.
        self.setSignals("time motor I I0 I00 I000 diode scint".split())
        self.selections = {}  # key=row, value=column number

        super().__init__()

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        """Number of signals."""
        value = len(self.signals())
        return value

    def columnCount(self, parent=None):
        """Number of columns."""
        value = len(self.columns())
        return value

    def data(self, index, role=None):
        if role == QtCore.Qt.CheckStateRole:
            if index.column() in self.checkboxColumns:
                return self.checkbox(index)

        if role == QtCore.Qt.DisplayRole and index.column() == 0:
            # signal name
            return self.signals()[index.row()]

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columns()[section]
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
        nm = self.columns()[index.column()]  # selection name of THIS column
        selection = self.selections.get(index.row())  # user selection
        return QtCore.Qt.Checked if selection == nm else QtCore.Qt.Unchecked

    def setCheckbox(self, index, state):
        """Set the checkbox state."""
        row, column = index.row(), index.column()
        column_name = self.columns()[column]
        checked = (state == QtCore.Qt.Checked)
        prior = self.selections.get(row)
        self.selections[row] = column_name if checked else None
        changes = self.selections[row] != prior
        logger.debug("selections: %s", self.selections)

        # apply selection rules
        # 1. If X or Mon, uncheck any other rows with this column name.
        if checked:
            for r, v in sorted(self.selections.items()):
                if v in ("X", "Mon"):
                    if r != row and column_name == v:
                        self.selections[r] = None
                        changes = True

        # 2. update checkboxes to agree with self.selections
        if changes:
            top = min(self.selections)
            left = min(self.checkboxColumns)
            bottom = max(self.selections)
            right = max(self.checkboxColumns)
            logger.debug("corners: (%d,%d)  (%d,%d)", top, left, bottom, right)
            self.dataChanged.emit(
                self.index(top, left),
                self.index(bottom, right),
                [QtCore.Qt.CheckStateRole]
            )

        self.logCheckboxSelections()

    def logCheckboxSelections(self):
        logger.debug("checkbox selections:")
        for r in range(self.rowCount()):
            text = ""
            for c in self.checkboxColumns:
                state = self.checkbox(self.index(r, c))
                choices = {QtCore.Qt.Checked: "*", QtCore.Qt.Unchecked: "-"}
                text += choices[state]
            text += f" {self.signals()[r]}"
            logger.debug(text)

    # ------------ local methods

    def columns(self):
        return self._columns

    def signals(self):
        return self._signals

    def setSignals(self, signals):
        self._signals = signals
