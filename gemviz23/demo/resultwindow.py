import utils
from PyQt5 import QtCore, QtWidgets
import datetime
import sys

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        self.columnLabels = ["Scan ID", "Plan Name", "Motors", "Detectors", "Date", "Status"]
        self.setPageOffset(0)
        self.setPageSize(20)
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
            print("Display role:", index.row(), index.column())
            uid=self.uidList()[index.row()]
            run=self.catalog()[uid]
            column=index.column()
            if column==0:
                return run.metadata["start"].get("scan_id", "")
            elif column==1:
                return run.metadata["start"].get("plan_name", "")
            elif column==2:
                return ", ".join(run.metadata["start"].get("motors", []))
            elif column==3:
                return ", ".join(run.metadata["start"].get("detectors", []))
            elif column==4:
                ts = run.metadata["start"].get("time", "")
                dt = datetime.datetime.fromtimestamp(round(ts))
                return dt.isoformat(sep=" ")
            elif column==5:
                return run.metadata.get("stop", {}).get("exit_status", "")
            
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal: 
                return self.columnLabels[section]
            else:
                return str(section + 1) #may want to alter at some point
    
    # ------------ local methods
    def _get_uidList(self):
        gen = self.catalog()._keys_slice(self.pageOffset(), self.pageOffset() + self.pageSize(), 1 if self.ascending() else -1)
        return list(gen)

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

    def setPageOffset(self, value):
        self._pageOffset=value

    def setPageSize(self, value):
        self._pageSize=value

    def ascending(self):
        return self._ascending
    
    def setAscending(self, value):
        self._ascending=value
    

class ResultWindow(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

            
    def setup(self):
        self.mainwindow.filter_panel.catalogs.currentTextChanged.connect(self.displayTable)
        # since we cannot set header's ResizeMode in Designer ...
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        
    def displayTable(self, *args):
        server = self.mainwindow.filter_panel._server
        self.cat = server[args[0]]
        data_model = TableModel(self.cat)
        print(f"Displaying catalog: {args[0]}")
        self.tableView.setModel(data_model)


# if __name__ == "__main__":
#     myApp = ResultWindow()
#     myApp.show()

#     try:
#         sys.exit(app.exec_())
#     except SystemExit:
#         print("Closing Window...")
    

# # this is not going to change:
# def gui():
#     """display the main widget"""
#     import sys

#     app = QtWidgets.QApplication(sys.argv)
#     main_window = ResultWindow()
#     main_window.show()
#     main_window.load_data()
#     sys.exit(app.exec_())


# if __name__ == "__main__":
#     gui()
