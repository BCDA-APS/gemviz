import utils
from PyQt5 import QtCore, QtWidgets
import datetime
import sys

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.columnLabels = ["Scan ID", "Plan Name", "Motors", "Detectors", "Date", "Status"]
        self._data = data
        # FIXME temporary way to handle large catalog
        self._uidList = list(reversed(list(self._data)))[-20:] 


    def rowCount(self, parent=None):
        # Want it to return the number of rows to be shown at a given time
        value = len(self._uidList) #We don't to use data becasue list could be too big so we use uidList
        return value

    def columnCount(self, parent=None):
        # Want it to return the number of columns to be shown at a given time
        value = len(self.columnLabels)
        return value

    def data(self, index, role=None):
        # display data
        if role == QtCore.Qt.DisplayRole:
            print("Display role:", index.row(), index.column())
            uid=self._uidList[index.row()]
            run=self._data[uid]
            column=index.column()
            if column==0:
                return run.metadata["start"].get("scan_id", "")
            elif column==1:
                return run.metadata["start"].get("plan_name", "")
            elif column==2:
                return str(run.metadata["start"].get("motors", ""))
            elif column==3:
                return str(run.metadata["start"].get("detectors", ""))
            elif column==4:
                ts = run.metadata["start"].get("time", "")
                dt = datetime.datetime.fromtimestamp(round(ts))
                return dt.isoformat(sep=" ")
            elif column==5:
                return run.metadata.get("stop", {}).get("exit_status", "")
            
            try:
                return self._data[index.row()][index.column()]
            except IndexError:
                return ""
            
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal: 
                return self.columnLabels[section]
            else:
                return str(section + 1) #may want to alter at some point


class ResultWindow(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        self.mainwindow.filter_panel.catalogs.currentTextChanged.connect(self.displayTable)
        
    def displayTable(self, *args):
        server = self.mainwindow.filter_panel._server
        self.cat = server[args[0]]
        data_model = TableModel(self.cat)
        print(f"Displaying catalog: {args[0]}")
        self.tableView.setModel(data_model)


if __name__ == "__main__":
    myApp = ResultWindow()
    myApp.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print("Closing Window...")
    

# this is not going to change:
def gui():
    """display the main widget"""
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = ResultWindow()
    main_window.show()
    main_window.load_data()
    sys.exit(app.exec_())


if __name__ == "__main__":
    gui()
