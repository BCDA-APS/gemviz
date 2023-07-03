import pathlib
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

# this is not going to change:
def myLoadUi(ui_file, baseinstance=None, **kw):
    """
    function to call for UI file
    """
    return loadUi(ui_file, baseinstance=baseinstance, **kw)





# this is what we customize:
class MyMainWindow(QMainWindow):
    def __init__(self):
        self.max_num_of_entries = 100
        super().__init__()
        #import UI file
        ui_file = pathlib.Path(__file__).parent / "ui_files/result_window.ui"
        myLoadUi(ui_file, self)
        #self.load_data


    def load_data(self):
        cata = [{"Catalog":"1" , "Plan": "2" , "Scan ID":"333", "Status":"Success","Positioner":"4"}]        
        row = 0
        self.tableWidget.setRowCount(len(cata))
        for catalog in cat:
            self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(catalog["Catalog"]))
            row = row +1


    #def horizontal_header():have to make this dynamic so that it takes information from tiled and adapts 
    
    #def vertical_header():have to make this dynamic so that it takes information from tiled and adapts

        



# this is not going to change:
def gui():
    """display the main widget"""
    app = QApplication(sys.argv)
    main_window = MyMainWindow()
    #print(f"{main_window.tf = }")
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    gui()