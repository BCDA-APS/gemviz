"""
QAbstractTableModel of tiled "CatalogOfBlueskyRuns".

BRC: BlueskyRunsCatalog

.. autosummary::

    ~BRCTableModel
"""

import logging

from PyQt5 import QtCore
from PyQt5 import QtGui

from . import utils

BGCLUT = {  # BackGround Color Lookup Table
    "success": None,
    # mark background color of unsuccessful runs
    "abort": QtGui.QColorConstants.Svg.lightyellow,  # ffffe0
    "fail": QtGui.QColorConstants.Svg.mistyrose,  # ffe4e1
    # other, such as None (when no stop document)
    "other": QtGui.QColor(0xE2E2EC),  # light blue/grey
}
logger = logging.getLogger(__name__)


class BRCTableModel(QtCore.QAbstractTableModel):
    """Page of Bluesky catalog runs."""

    def __init__(self, parent):
        self.parent = parent  # QTableView
        self.runs = {}

        def get_str_list(run, doc, key):
            return ", ".join(run.get_run_md(doc, key, []))

        self.actions_library = {
            "Scan ID": lambda run: run.get_run_md("start", "scan_id"),
            "Plan Name": lambda run: run.get_run_md("start", "plan_name"),
            "Positioners": lambda run: get_str_list(run, "start", "motors"),
            "Detectors": lambda run: get_str_list(run, "start", "detectors"),
            "#points": lambda run: run.get_run_md("start", "num_points"),
            "Date": lambda run: utils.ts2iso(round(run.get_run_md("start", "time"))),
            "Status": lambda run: run.get_run_md("stop", "exit_status"),
            "Streams": lambda run: get_str_list(run, "summary", "stream_names"),
            # "uid": lambda run: run.get_run_md("start", "uid"),
            # "uid7": lambda run: run.get_run_md("start", "uid")[:7],
        }
        self.columnLabels = list(self.actions_library.keys())

        super().__init__(parent)
        # print(f"{__name__}: {data=}")

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        """Return the number of rows. Called by QTableView."""
        # Want it to return the number of rows to be shown at a given time
        value = len(self.runs)
        return value

    def columnCount(self, parent=None):
        """Return the number of columns. Called by QTableView."""
        # Want it to return the number of columns to be shown at a given time
        value = len(self.columnLabels)
        return value

    def data(self, index, role=None):
        """Return the cell data. Called by QTableView."""
        if role == QtCore.Qt.DisplayRole:  # display data
            row, column = index.row(), index.column()
            label = self.columnLabels[column]
            action = self.actions_library[label]
            run = list(self.runs.values())[row]
            result = action(run)
            logger.debug("Display role: (%d, %d) %s", row, column, result)
            # print(f"{__name__}: ({row}, {column}) {result}")
            return result

        elif role == QtCore.Qt.BackgroundRole:
            run = list(self.runs.values())[index.row()]
            exit_status = run.get_run_md("stop", "exit_status", "unknown")
            bgcolor = BGCLUT.get(exit_status, BGCLUT["other"])
            if bgcolor is not None:
                return QtGui.QBrush(bgcolor)

        elif role == QtCore.Qt.TextAlignmentRole:
            if index.column() in [0, 4]:
                return QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter
            else:
                return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """Return the column label. Called by QTableView."""
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # ------------ methods required by the view

    def getMetadata(self, index):
        """Return the selected run's metadata."""
        return list(self.runs.values())[index]

    def setRuns(self, runs):
        """
        Define the run (metadata) to be shown in the table now.

        runs *dict(uid, metadata_dictionary)*:
            Dictionary of run metadata, keyed by run uid.
        """
        self.runs = runs
        self.layoutChanged.emit()  # Tell the view there is new data.


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2024, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
