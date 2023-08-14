import analyze_run
import utils
from PyQt5 import QtCore, QtWidgets
import datetime
import yaml
import pyRestTable
DEFAULT_PAGE_SIZE = 20
DEFAULT_PAGE_OFFSET = 0

class TableModel(QtCore.QAbstractTableModel):
    """Bluesky catalog for QtCore.QAbstractTableModel."""

    def __init__(self, data):
        self.actions_library = {
            "Scan ID": ["start", "scan_id"],
            "Plan Name": ["start", "plan_name"],
            "Positioners": self.get_run_positioners,
            "Detectors": self.get_run_detectors,
            "#points": ["start", "num_points"],
            "Date": self.get_run_start_time,
            "Status": ["stop", "exit_status"],
            "Streams": self.get_run_stream_names,
            # "uid": ["start", "uid"],
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

            if isinstance(action, list):
                return utils.get_md(run, *action)
            else:
                return action(run)
            
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal: 
                return self.columnLabels[section]
            else:
                return str(section + 1) #may want to alter at some point

    # ------------ methods required by the results table 

    def doPager(self, action, value = None):
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
            value = min(value, catalog_length - 1 - size)
            value = max(value, 0)
            self.setPageOffset(value)
        elif action == "last":
            value = catalog_length - 1 - size
            value = max(value, 0)
            self.setPageOffset(value)
        
        self.setUidList(self._get_uidList())
        # print(f"{self.pageOffset()=} {self.pageSize()=}")


    def isPagerAtStart(self):
        return self.pageOffset()==0

    def isPagerAtEnd(self):
        return (self.pageOffset() + len(self.uidList())) >= self.catalog_length()
    
    # ------------ local methods

    def _get_uidList(self):
        cat = self.catalog()
        start = self.pageOffset()
        end = start + self.pageSize()
        ascending = 1 if self.ascending() else -1
        gen = cat._keys_slice(start, end, ascending)
        return list(gen)  # FIXME: fails here with big catalogs, see issue #51

    def get_run_detectors(self, run):
        """Return the run's detector names as a list."""
        items = utils.get_md(run, "start", "detectors", [])
        return ", ".join(items)

    def get_run_positioners(self, run):
        """Return the run's positioner names as a list."""
        items = utils.get_md(run, "start", "motors", [])
        return ", ".join(items)

    def get_run_start_time(self, run):
        """Return the run's start time as ISO8601 string."""
        ts = utils.get_md(run, "start", "time", 0)
        dt = datetime.datetime.fromtimestamp(round(ts))
        return dt.isoformat(sep=" ")

    def get_run_stream_names(self, run):
        """Return the run's stream names as a list."""
        items = utils.get_md(run, "summary", "stream_names", [])
        return ", ".join(items)

    def get_run_uid7(self, run):
        """Return the run's uid, truncated to the first 7 characters."""
        uid = utils.get_md(run, "start", "uid")
        return uid[:7]

    # ------------ get & set methods
    
    def catalog(self):
        return self._data
    
    def catalog_length(self):
        return self._catalog_length
    
    def setCatalog(self, catalog):
        self._data=catalog
        self._catalog_length = len(catalog)

    def uidList(self):
        return self._uidList

    def setUidList(self, value):
        self._uidList=value
    
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
        self._ascending=value

    def pagerStatus(self):
        total= self.catalog_length()
        if total==0:
            text = "No runs"
        else:
            start = self.pageOffset()
            end = start+len(self.uidList())
            text = f"{start + 1}-{end} of {total} runs"
        return text
    
    def getMetadata(self, index):
        """Provide a text view of the run metadata."""
        uid=self.uidList()[index.row()]
        run=self.catalog()[uid]
        md=yaml.dump(dict(run.metadata), indent=4)
        return md

    def getDataDescription(self, index):
        """Provide text description of the data streams."""
        uid=self.uidList()[index.row()]
        run=self.catalog()[uid]

        # Describe what will be plotted.
        analysis = analyze_run.SignalAxesFields(run).to_dict()
        table = pyRestTable.Table()
        table.labels = "item description".split()
        table.addRow(("scan", analysis['scan_id']))
        table.addRow(("plan", analysis['plan']))
        table.addRow(("chart", analysis['chart_type']))
        if analysis["plot_signal"] is not None:
            table.addRow(("stream", analysis['stream']))
            table.addRow(("plot signal", analysis['plot_signal']))
            table.addRow(("plot axes", ', '.join(analysis['plot_axes'])))
            table.addRow(("all detectors", ', '.join(analysis['detectors'])))
            table.addRow(("all positioners", ', '.join(analysis['positioners'])))
        text = "plot summary"
        text += ("\n" + "-" * len(text) + "\n" * 2)
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

    

class ResultWindow(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

            
    def setup(self):
        from functools import partial

        self.mainwindow.filter_panel.catalogs.currentTextChanged.connect(self.displayTable)
        self.mainwindow.filter_panel.plan_name.returnPressed.connect(self.displayTable)
        self.mainwindow.filter_panel.scan_id.returnPressed.connect(self.displayTable)
        self.mainwindow.filter_panel.status.returnPressed.connect(self.displayTable)
        self.mainwindow.filter_panel.positioners.returnPressed.connect(self.displayTable)
        self.mainwindow.filter_panel.detectors.returnPressed.connect(self.displayTable)
        self.mainwindow.filter_panel.date_time_widget.apply.released.connect(self.displayTable)

        # since we cannot set header's ResizeMode in Designer ...
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        
        for button_name in "first back next last".split():
            button = getattr(self, button_name)
            # custom: pass the button name to the receiver
            button.released.connect(partial(self.doPagerButtons, button_name))
        
        self.pageSize.currentTextChanged.connect(self.doPageSize)
        self.doButtonPermissions()
        self.setPagerStatus()
        self.tableView.doubleClicked.connect(self.doRunSelected)

    def doPagerButtons(self, action, **kwargs):
        # print(f"{action=} {kwargs=}")
        model = self.tableView.model()

        if model is not None:
            print(f"{model.pageOffset()=}")
            model.doPager(action)
        self.doButtonPermissions()
        self.setPagerStatus()
    
    def doPageSize(self, value):
        # print(f"doPageSize {value =}")
        model = self.tableView.model()

        if model is not None:
            model.doPager("pageSize", value)
        self.doButtonPermissions()
        self.setPagerStatus()

    def doButtonPermissions(self):
        model = self.tableView.model()
        atStart = False if model is None else model.isPagerAtStart()
        atEnd = False if model is None else model.isPagerAtEnd()

        self.first.setEnabled(not atStart)
        self.back.setEnabled(not atStart)
        self.next.setEnabled(not atEnd)
        self.last.setEnabled(not atEnd)
        

        
    def displayTable(self, *args):
        self.cat = self.mainwindow.filter_panel.filteredCatalog()
        data_model = TableModel(self.cat)
        # print(f"Displaying catalog: {self.cat.item['id']!r}")
        page_size = self.pageSize.currentText() # remember the current value
        self.tableView.setModel(data_model) 
        self.doPageSize(page_size) # restore
        self.setPagerStatus()
        self.mainwindow.filter_panel.enableDateRange(len(self.mainwindow.filter_panel.catalog())>0)

    def setPagerStatus(self, text=None):
        if text is None:
            model = self.tableView.model()
            if model is not None:
                text=model.pagerStatus()

        self.status.setText(text)

    def doRunSelected(self, index):
        model = self.tableView.model()
        if model is not None:
            self.mainwindow.viz.setMetadata(model.getMetadata(index))
            self.mainwindow.viz.setData(model.getDataDescription(index))
