import utils
from PyQt5 import QtCore, QtGui, QtWidgets

# imports tiled
import tiled.queries
from tiled.client import from_uri
from tiled.client.cache import Cache
from tiled.utils import tree

import datetime

# imports widget
import sys
import pathlib
from PyQt5.uic import loadUi

###

# # this is what we customize:
# class ResultWindow(QtWidgets.QWidget):
#     def __init__(self, mainwindow):
#         self.mainwindow = mainwindow
#         self.max_num_of_entries = 100
#         super().__init__()
#         utils.myLoadUi(UI_FILE, baseinstance=self)
#         self.setup()

#     def setup(self):
#         from resultwindow import ResultWindow

#         # TODO widget initilization

#     def load_data(self):
#         cat = [
#             {
#                 "Catalog": "1",
#                 "Plan": "2",
#                 "Scan ID": "333",
#                 "Status": "Success",
#                 "Positioner": "4",
#             }
#         ]
#         row = 0
#         self.tableWidget.setRowCount(len(cat))
#         for catalog in cat:
#             self.tableWidget.setItem(
#                 row, 0, QtWidgets.QTableWidgetItem(catalog["Catalog"])
#             )
#             row = row + 1

###


###

# # tiled server information
# tiled_server = "otz.xray.aps.anl.gov"
# tiled_server_port = 8000
# catalog = "developer"
# start_time = "2021-03-17 00:30"
# end_time = "2021-05-19 15:15"

# # connect our client with the server
# uri = f"http://{tiled_server}:{tiled_server_port}"
# print(f"{uri=}")
# client = from_uri(uri, cache=Cache.in_memory(2e9))
# print(f"{client=}")
# print(f"{catalog=}")
# cat = client[catalog]
# print(f"{cat=}")


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.columnLabels = ["Scan ID", "Plan Name", "Detectors", "Date", "Status"]
        self._data = data
        self._uidList = list(reversed(list(self._data)))
        print("stop")

    def rowCount(self, parent=None):
        # Want it to return the number of rows to be shown at a given time
        value = len(self._data)
        return value

    def columnCount(self, parent=None):
        # Want it to return the number of columns to be shown at a given time
        # value = len(max(self._data, key=len))
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
                return str(run.metadata["start"].get("detectors", ""))
            elif column==3:
                ts = run.metadata["start"].get("time", "")
                dt = datetime.datetime.fromtimestamp(round(ts))
                return dt.isoformat(sep=" ")
            elif column==4:
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


    # def setData(self, index, value, role=Qt.EditRole):
    #     if role in (QtCore.Qt.DisplayRole, Qt.EditRole):
    #         print("Edit role:", index.row(), index.column())
    #         # if value is blank
    #         if not value:
    #             return False
    #         self._data[index.row()][index.column()] = value
    #         self.dataChanged.emit(index, index)
    #     return True

    # def flags(self, index):
    #     return super().flags(index) | Qt.ItemIsEditable


class ResultWindow(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()
        # self.window_width, self.window_height = 600, 600
        # self.setMinimumSize(self.window_width, self.window_height)
        # self.setStyleSheet(
        #     """
		# 	QWidget {
		# 		font-size: 30px;
		# 	}
		# """
        # )

        # self.layout = {}
        # self.layout["main"] = QtCore.QVBoxLayout()
        # self.setLayout(self.layout["main"])
    def setup(self):
        # from filterpanel import FilterPanel
        self.tableView = QtWidgets.QTableView()
        # self.layout["main"].addWidget(self.table)
        
        
        self.mainwindow.filter_panel.catalogs.currentTextChanged.connect(self.displayTable)
        
    def displayTable(self, *args):
        server = self.mainwindow.filter_panel._server
        self.cat = server.get(args[0], {})
        data_model = TableModel(self.cat)
        print(args[0])
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
