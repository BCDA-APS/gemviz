### I want to inport the information from the test database filter through and find key words and info

from test_infomation_database import test_catalog_2

def test_function():
    return (test_catalog_2)

### Run the "mainwindow.ui" file within the python file
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
        super().__init__()
        #import UI file
        ui_file = pathlib.Path(__file__).parent / "Filter_Window.ui"
        myLoadUi(ui_file, self)
        self.add_catalog_names()
        self.InputBox1.activated.connect(self.show_selected_catalog)
        #self.InputBox1.activated.connect(self.show_selected_catalog_status)

    def add_catalog_names(self):    # write to the pull down menu
        self.tf = test_function()
        print(f"\n{self.tf.keys() = }")
        print(f"{self.InputBox1 = }")
        self.InputBox1.clear()
        self.InputBox1.addItems(self.tf.keys())

    def show_selected_catalog(self, itemnumber):    # read selected value from pull down menu
        print(f"\n{itemnumber = }") 
        print(f"{self.InputBox1.currentText() = }") 
        key = self.InputBox1.currentText()  
        print(f"{self.tf[key] = }") 
        self.statusbar.showMessage(str(len(self.tf[key])) + " entries")

    # def show_selected_catalog_status(self, itemnumber):
    #     print(f"\n{itemnumber = }") 
    #     print(f"{self.InputBox1.currentText() = }") 
    #     key = self.InputBox1.currentText()  










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