#imports tiled
import tiled.queries
from tiled.client import from_uri
from tiled.client.cache import Cache
from tiled.utils import tree

#imports widget
import sys
import pathlib
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
###

#tiled server information 
tiled_server = "otz.xray.aps.anl.gov"
tiled_server_port = 8000
catalog = "developer"
start_time = "2021-03-17 00:30"
end_time = "2021-05-19 15:15"

# connect our client with the server
uri = f"http://{tiled_server}:{tiled_server_port}"
print(f"{uri=}")
client = from_uri(uri, cache=Cache.in_memory(2e9))
print(f"{client=}")
print(f"{catalog=}")
cat = client[catalog]
print(f"{cat=}")


class TableModel(QAbstractTableModel):
	def __init__(self, data):
		super().__init__()
		self._data = data

	def rowCount(self, parent=QModelIndex()):
		return len(self._data)

	def columnCount(self, parent=QModelIndex()):
		return len(max(self._data, key=len))

	def data(self, index, role=Qt.DisplayRole):
		# display data
		if role == Qt.DisplayRole:
			print('Display role:', index.row(), index.column())
			try:
				return self._data[index.row()][index.column()]
			except IndexError:
				return ''

	def setData(self, index, value, role=Qt.EditRole):		
		if role in (Qt.DisplayRole, Qt.EditRole):
			print('Edit role:', index.row(), index.column())
			# if value is blank
			if not value:
				return False	
			self._data[index.row()][index.column()] = value
			self.dataChanged.emit(index, index)
		return True

	def flags(self, index):
		return super().flags(index) | Qt.ItemIsEditable

class MainApp(QWidget):
	def __init__(self):
		super().__init__()
		self.window_width, self.window_height = 1600, 1200
		self.setMinimumSize(self.window_width, self.window_height)
		self.setStyleSheet('''
			QWidget {
				font-size: 30px;
			}
		''')		

		self.layout = {}
		self.layout['main'] = QVBoxLayout()
		self.setLayout(self.layout['main'])

		self.table = QTableView()
		self.layout['main'].addWidget(self.table)

		data_model = TableModel(data)
		self.table.setModel(data_model)


if __name__ == '__main__':
	data = [
		['A1', 'A2', 'A3'],
		['B1', 'B2', 'B3', 'B4'],
		['C1', 'C2', 'C3', 'C4', 'C5']
	]

	# row count
	# print(len(data))

	# column count
	# print(len(max(data, key=len)))

	app = QApplication(sys.argv)
	
	myApp = MainApp()
	myApp.show()

	try:
		sys.exit(app.exec_())
	except SystemExit:
		print('Closing Window...')

    



# run and display ui file for testing
def gui():
    app = QApplication(sys.argv)
    main_window = ResultWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    gui()