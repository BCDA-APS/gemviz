import utils
from PyQt5 import QtCore, QtWidgets
import datetime
import sys
DEFAULT_PAGE_SIZE = 20
DEFAULT_PAGE_OFFSET = 0

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        self.columnLabels = ["Scan ID", "Plan Name", "Motors", "Detectors", "Date", "Status"]
        self.setPageOffset(DEFAULT_PAGE_OFFSET, init=True)
        self.setPageSize(DEFAULT_PAGE_SIZE, init=True)
        self.setAscending(True)

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
            #print("Display role:", index.row(), index.column())
            uid=self.uidList()[index.row()]
            run=self.catalog()[uid]
            column=index.column()
            if column==0:
                return self._getKey(run, "start", "scan_id")
            elif column==1:
                return self._getKey(run, "start", "plan_name")
            elif column==2:
                return ", ".join(self._getKey(run,"start", "motors", []))
            elif column==3:
                return ", ".join(self._getKey(run,"start", "detectors", []))
            elif column==4:
                ts = self._getKey(run, "start", "time")
                dt = datetime.datetime.fromtimestamp(round(ts))
                return dt.isoformat(sep=" ")
            elif column==5:
                return self._getKey(run, "stop", "exit_status")
            
    def _getKey(self, run, document_name, key, default=""):
        md=run.metadata
        if md is None:
            return default
        document=md.get(document_name) or {}
        return document.get(key, default)
            
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal: 
                return self.columnLabels[section]
            else:
                return str(section + 1) #may want to alter at some point

    # ------------ methods required by the results table 

    def doPager(self, action, value = None):
        print(f"doPager {action =}, {value =}")
        if action == "first":
            self.setPageOffset(0)
        elif action == "pageSize":
            self.setPageSize(value)
        elif action == "back":
            value = self.pageOffset() - self.pageSize()
            value = min(value, len(self.catalog()))
            value = max(value,0)
            self.setPageOffset(value)
        elif action == "next":
            value = self.pageOffset() + self.pageSize()
            value = min(value, len(self.catalog()) - 1 - self.pageSize())
            value = max(value,0)
            self.setPageOffset(value)
        elif action == "last":
            value = len(self.catalog()) - 1 - self.pageSize()
            value = max(value,0)
            self.setPageOffset(value)
        
        self.setUidList(self._get_uidList())
        print(f"{self.pageOffset() =} {self.pageSize() =}")


    def isPagerAtStart(self):
        return self.pageOffset()==0

    def isPagerAtEnd(self):
        return (self.pageOffset() + len(self.uidList())) >= len(self.catalog())
    
    # ------------ local methods

    def _get_uidList(self):
        cat = self.catalog()
        start = self.pageOffset()
        end = start + self.pageSize()
        ascending = 1 if self.ascending() else -1
        gen = cat._keys_slice(start, end, ascending)
        return list(gen)  # FIXME: fails here with big catalogs, see issue #51

    # ------------ get & set methods
    
    def catalog(self):
        return self._data
    
    def setCatalog(self, catalog):
        self._data=catalog

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
        total= len(self.catalog())
        if total==0:
            text = "No runs"
        else:
            start = self.pageOffset()
            end = start+len(self.uidList())
            text = f"{start + 1}-{end} of {total} runs"
        return text
    
    def getMetadata(self, index):
        import yaml
        uid=self.uidList()[index.row()]
        run=self.catalog()[uid]
        md=run.metadata
        md=yaml.dump(dict(md), indent=4)
        return md

    

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
        self.mainwindow.filter_panel.positioner.returnPressed.connect(self.displayTable)

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
        print(f"{action=} {kwargs=}")
        model = self.tableView.model()

        if model is not None:
            model.doPager(action)
        self.doButtonPermissions()
        self.setPagerStatus()
    
    def doPageSize(self, value):
        print(f"doPageSize {value =}")
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
        print(f"Displaying catalog: {self.cat.item['id']!r}")
        page_size = self.pageSize.currentText() # remember the current value
        self.tableView.setModel(data_model) 
        self.doPageSize(page_size) # restore
        self.setPagerStatus()

    def setPagerStatus(self, text=None):
        if text is None:
            model = self.tableView.model()
            if model is not None:
                text=model.pagerStatus()

        self.status.setText(text)

    def doRunSelected(self, index):
        model = self.tableView.model()
        if model is not None:
            metadata=model.getMetadata(index)
            self.mainwindow.viz.setMetadata(metadata)