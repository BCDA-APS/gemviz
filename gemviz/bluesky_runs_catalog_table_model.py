"""
QAbstractTableModel of tiled "CatalogOfBlueskyRuns".

BRC: BlueskyRunsCatalog

.. autosummary::

    ~BRCTableModel
"""

import datetime
import logging

import pyRestTable
import yaml
from PyQt5 import QtCore
from PyQt5 import QtGui

from . import analyze_run
from . import tapi

logger = logging.getLogger(__name__)
DEFAULT_PAGE_SIZE = 5
DEFAULT_PAGE_OFFSET = 0
BGCLUT = {  # BackGround Color Lookup Table
    "success": None,
    # mark background color of unsuccessful runs
    "abort": QtGui.QColorConstants.Svg.lightyellow,  # ffffe0
    "fail": QtGui.QColorConstants.Svg.mistyrose,  # ffe4e1
    # other, such as None (when no stop document)
    "other": QtGui.QColor(0xE2E2EC),  # light blue/grey
}


class BRCTableModel(QtCore.QAbstractTableModel):
    """Bluesky catalog for QtCore.QAbstractTableModel."""

    def __init__(self, data):
        self.actions_library = {
            "Scan ID": lambda run: tapi.get_md(run, "start", "scan_id"),
            "Plan Name": lambda run: tapi.get_md(run, "start", "plan_name"),
            "Positioners": lambda run: self.get_str_list(run, "start", "motors"),
            "Detectors": lambda run: self.get_str_list(run, "start", "detectors"),
            "#points": lambda run: tapi.get_md(run, "start", "num_points"),
            "Date": self.get_run_start_time,
            "Status": lambda run: tapi.get_md(run, "stop", "exit_status"),
            "Streams": lambda run: self.get_str_list(run, "summary", "stream_names"),
            # "uid": lambda run: tapi.get_md(run, "start", "uid"),
            # "uid7": self.get_run_uid7,
        }
        self.columnLabels = list(self.actions_library.keys())

        self.setPageOffset(DEFAULT_PAGE_OFFSET, init=True)
        self.setPageSize(DEFAULT_PAGE_SIZE, init=True)
        self.setAscending(True)
        self._catalog_count = 0

        self.setCatalog(data)
        self.setUidList()

        super().__init__()

    # ------------ methods required by Qt's view

    def rowCount(self, parent=None):
        # Want it to return the number of rows to be shown at a given time
        value = len(self.uidList())
        return value

    def columnCount(self, parent=None):
        # Want it to return the number of columns to be shown at a given time
        value = len(self.columnLabels)
        return value

    def data(self, index, role=None):
        if role == QtCore.Qt.DisplayRole:  # display data
            logger.debug("Display role: %d, %d", index.row(), index.column())
            run = self.indexToRun(index)
            label = self.columnLabels[index.column()]
            action = self.actions_library[label]
            return action(run)

        elif role == QtCore.Qt.BackgroundRole:
            run = self.indexToRun(index)
            exit_status = tapi.get_md(run, "stop", "exit_status", "unknown")
            bgcolor = BGCLUT.get(exit_status, BGCLUT["other"])
            if bgcolor is not None:
                return QtGui.QBrush(bgcolor)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # ------------ methods required by the view

    def doPager(self, action, value=None):
        logger.debug("action=%s, value=%s", action, value)

        catalog_count = self.catalogCount()
        offset = self.pageOffset()
        size = self.pageSize()
        logger.debug(
            "catalog_count=%s, offset=%s, size=%s", catalog_count, offset, size
        )

        if action == "first":
            self.setPageOffset(0)
        elif action == "pageSize":
            self.setPageSize(value)
        elif action == "back":
            value = offset - size
            value = min(value, catalog_count)
            value = max(value, 0)
            self.setPageOffset(value)
        elif action == "next":
            value = offset + size
            value = min(value, catalog_count - size)
            value = max(value, 0)
            self.setPageOffset(value)
        elif action == "last":
            value = catalog_count - size
            value = max(value, 0)
            self.setPageOffset(value)

        try:
            self.setUidList()
        except tapi.TiledServerError as exc:
            # reset to previous values
            self.setPageOffset(offset)
            self.setPageSize(size)

            # re-raise for reporting in the view
            raise exc
        logger.debug("pageOffset=%s, pageSize=%s", self.pageOffset(), self.pageSize())

    def isPagerAtStart(self):
        return self.pageOffset() == 0

    def isPagerAtEnd(self):
        # number is zero-based
        last_row_number = self.pageOffset() + len(self.uidList())
        return last_row_number >= self.catalogCount()

    # ------------ local methods

    def get_run_start_time(self, run):
        """Return the run's start time as ISO8601 string."""
        ts = tapi.get_md(run, "start", "time", 0)
        dt = datetime.datetime.fromtimestamp(round(ts))
        return dt.isoformat(sep=" ")

    def get_run_uid7(self, run):
        """Return the run's uid, truncated to the first 7 characters."""
        uid = tapi.get_md(run, "start", "uid")
        return uid[:7]

    def get_str_list(self, run, doc, key):
        """Return the document's key values as a list."""
        items = tapi.get_md(run, doc, key, [])
        return ", ".join(items)

    # ------------ get & set methods

    def catalog(self):
        return self._catalog

    def catalogCount(self):
        return self._catalog_count

    def setCatalog(self, catalog):
        self._catalog = catalog
        self._catalog_count = len(catalog)

    def uidList(self):
        return self._uidList

    def setUidList(self):
        self._uidList = tapi.get_tiled_slice(
            self.catalog(),
            self.pageOffset(),
            self.pageSize(),
            self.ascending(),
        )

    def pageOffset(self):
        return self._pageOffset

    def pageSize(self):
        return self._pageSize

    def setPageOffset(self, offset, init=False):
        """Set the pager offset."""
        offset = int(offset)
        if init:
            self._pageOffset = offset
        elif offset != self._pageOffset:
            self._pageOffset = offset
            self.layoutChanged.emit()

    def setPageSize(self, value, init=False):
        """Set the pager size."""
        value = int(value)
        if init:
            self._pageSize = value
        elif value != self._pageSize:
            self._pageSize = value
            self.layoutChanged.emit()

    def ascending(self):
        return self._ascending

    def setAscending(self, value):
        self._ascending = value

    def pagerStatus(self):
        total = self.catalogCount()
        if total == 0:
            text = "No runs"
        else:
            start = self.pageOffset()
            end = start + len(self.uidList())
            text = f"{start + 1}-{end} of {total} runs"
        return text

    def indexToRun(self, index):
        uid = self.uidList()[index.row()]
        return self.catalog()[uid]

    def getMetadata(self, index):
        """Provide a text view of the run metadata."""
        run = self.indexToRun(index)
        md = yaml.dump(dict(run.metadata), indent=4)
        return md

    def getDataDescription(self, index):
        """Provide text description of the data streams."""
        run = self.indexToRun(index)

        # Describe what will be plotted.
        analysis = analyze_run.SignalAxesFields(run).to_dict()
        table = pyRestTable.Table()
        table.labels = "item description".split()
        table.addRow(("scan", analysis["scan_id"]))
        table.addRow(("plan", analysis["plan"]))
        table.addRow(("chart", analysis["chart_type"]))
        if analysis["plot_signal"] is not None:
            table.addRow(("stream", analysis["stream"]))
            table.addRow(("plot signal", analysis["plot_signal"]))
            table.addRow(("plot axes", ", ".join(analysis["plot_axes"])))
            table.addRow(("all detectors", ", ".join(analysis["detectors"])))
            table.addRow(("all positioners", ", ".join(analysis["positioners"])))
        text = "plot summary"
        text += "\n" + "-" * len(text) + "\n" * 2
        text += f"{table.reST()}\n"

        # information about each stream
        rows = []
        for sname in run:
            title = f"stream: {sname}"
            rows.append(title)
            rows.append("-" * len(title))
            stream = run[sname]
            data = stream["data"].read()
            rows.append(str(data))
            rows.append("")

        text += "\n".join(rows).strip()
        return text

    def getSummary(self, index):
        run = self.indexToRun(index)
        return (
            f'#{tapi.get_md(run, "start", "scan_id", "unknown")}'
            f'  {tapi.get_md(run, "start", "plan_name", "unknown")}'
        )
