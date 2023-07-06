import utils
from PyQt5 import QtCore, QtGui, QtWidgets

UI_FILE = utils.getUiFileName(__file__)


# this is what we customize:
class ResultWindow(QtWidgets.QWidget):
    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.max_num_of_entries = 100
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        from resultwindow import ResultWindow

        # TODO widget initilization

    def load_data(self):
        cat = [
            {
                "Catalog": "1",
                "Plan": "2",
                "Scan ID": "333",
                "Status": "Success",
                "Positioner": "4",
            }
        ]
        row = 0
        self.tableWidget.setRowCount(len(cat))
        for catalog in cat:
            self.tableWidget.setItem(
                row, 0, QtWidgets.QTableWidgetItem(catalog["Catalog"])
            )
            row = row + 1

    # def horizontal_header():have to make this dynamic so that it takes information from tiled and adapts

    # def vertical_header():have to make this dynamic so that it takes information from tiled and adapts


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
