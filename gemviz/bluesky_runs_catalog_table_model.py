"""
QAbstractTableModel of tiled "CatalogOfBlueskyRuns".

BRC: BlueskyRunsCatalog

.. autosummary::

    ~BRCTableModel
"""

import datetime

import pyRestTable
import yaml
from PyQt5 import QtCore

from . import analyze_run
from . import utils

DEFAULT_PAGE_SIZE = 20
DEFAULT_PAGE_OFFSET = 0


class BRCTableModel(QtCore.QAbstractTableModel):
    """Bluesky catalog for QtCore.QAbstractTableModel."""

    def __init__(self, data):
        self.actions_library = {
            "Scan ID": lambda run: utils.get_md(run, "start", "scan_id"),
            "Plan Name": lambda run: utils.get_md(run, "start", "plan_name"),
            "Positioners": lambda run: self.get_str_list(run, "start", "motors"),
            "Detectors": lambda run: self.get_str_list(run, "start", "detectors"),
            "#points": lambda run: utils.get_md(run, "start", "num_points"),
            "Date": self.get_run_start_time,
            "Status": lambda run: utils.get_md(run, "stop", "exit_status"),
            "Streams": lambda run: self.get_str_list(run, "summary", "stream_names"),
            # "uid": lambda run: utils.get_md(run, "start", "uid"),
            # "uid7": self.get_run_uid7,
        }
        self.columnLabels = list(self.actions_library.keys())

        self.setPageOffset(DEFAULT_PAGE_OFFSET, init=True)
        self.setPageSize(DEFAULT_PAGE_SIZE, init=True)
        self.setAscending(True)
        self._catalog_length = 0

        super().__init__()

        self.setCatalog(data)
        self.setUidList(self._get_uidList())

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
        # display data
        if role == QtCore.Qt.DisplayRole:
            # print("Display role:", index.row(), index.column())
            uid = self.uidList()[index.row()]
            run = self.catalog()[uid]
            label = self.columnLabels[index.column()]
            action = self.actions_library[label]
            return action(run)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.columnLabels[section]
            else:
                return str(section + 1)  # may want to alter at some point

    # ------------ methods required by the results table

    def doPager(self, action, value=None):
        # print(f"doPager {action =}, {value =}")

        catalog_length = self.catalog_length()
        offset = self.pageOffset()
        size = self.pageSize()
        # print(f"{catalog_length=} {offset=}  {size=}")

        if action == "first":
            self.setPageOffset(0)
        elif action == "pageSize":
            self.setPageSize(value)
        elif action == "back":
            value = offset - size
            value = min(value, catalog_length)
            value = max(value, 0)
            self.setPageOffset(value)
        elif action == "next":
            value = offset + size
            value = min(value, catalog_length - size)
            value = max(value, 0)
            self.setPageOffset(value)
        elif action == "last":
            value = catalog_length - size
            value = max(value, 0)
            self.setPageOffset(value)

        self.setUidList(self._get_uidList())
        # print(f"{self.pageOffset()=} {self.pageSize()=}")

    def isPagerAtStart(self):
        return self.pageOffset() == 0

    def isPagerAtEnd(self):
        # number is zero-based
        last_row_number = self.pageOffset() + len(self.uidList())
        return last_row_number >= self.catalog_length()

    # ------------ local methods

    def _get_uidList(self):
        cat = self.catalog()
        start = self.pageOffset()
        end = start + self.pageSize()
        ascending = 1 if self.ascending() else -1
        gen = cat._keys_slice(start, end, ascending)
        return list(gen)  # FIXME: fails here with big catalogs, see issue #51

    def get_run_start_time(self, run):
        """Return the run's start time as ISO8601 string."""
        ts = utils.get_md(run, "start", "time", 0)
        dt = datetime.datetime.fromtimestamp(round(ts))
        return dt.isoformat(sep=" ")

    def get_run_uid7(self, run):
        """Return the run's uid, truncated to the first 7 characters."""
        uid = utils.get_md(run, "start", "uid")
        return uid[:7]

    def get_str_list(self, run, doc, key):
        """Return the document's key values as a list."""
        items = utils.get_md(run, doc, key, [])
        return ", ".join(items)

    # ------------ get & set methods

    def catalog(self):
        return self._data

    def catalog_length(self):
        return self._catalog_length

    def setCatalog(self, catalog):
        self._data = catalog
        self._catalog_length = len(catalog)

    def uidList(self):
        return self._uidList

    def setUidList(self, value):
        self._uidList = value

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
        total = self.catalog_length()
        if total == 0:
            text = "No runs"
        else:
            start = self.pageOffset()
            end = start + len(self.uidList())
            text = f"{start + 1}-{end} of {total} runs"
        return text

    def index2run(self, index):
        uid = self.uidList()[index.row()]
        return self.catalog()[uid]

    def getMetadata(self, index):
        """Provide a text view of the run metadata."""
        run = self.index2run(index)
        md = yaml.dump(dict(run.metadata), indent=4)
        return md

    def getDataDescription(self, index):
        """Provide text description of the data streams."""
        run = self.index2run(index)

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
        run = self.index2run(index)
        return (
            f'#{utils.get_md(run, "start", "scan_id", "unknown")}'
            f'  {utils.get_md(run, "start", "plan_name", "unknown")}'
        )
