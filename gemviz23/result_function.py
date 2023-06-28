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