#!/usr/bin/env python

"""
gemviz23: Python Qt5 application to visualize Bluesky data from tiled server.
"""

import pathlib
import sys

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.uic import loadUi

UI_FILE = pathlib.Path(__file__).parent / "hello.ui"


def myLoadUi(ui_file, baseinstance=None, **kw):
    """
    load a .ui file for use in building a GUI

    Wraps `uic.loadUi()` with code that finds our program's
    *resources* directory.

    :see: http://nullege.com/codes/search/PyQt4.uic.loadUi
    :see: http://bitesofcode.blogspot.ca/2011/10/comparison-of-loading-techniques.html

    inspired by:
    http://stackoverflow.com/questions/14892713/how-do-you-load-ui-files-onto-python-classes-with-pyside?lq=1
    """
    return loadUi(ui_file, baseinstance=baseinstance, **kw)


class MainWindow(QWidget):
    """loads a custom .ui file"""

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        myLoadUi(UI_FILE, baseinstance=self)  # get the design from the .ui file
        self.label.setText("Bluesky")


def gui():
    """display the main widget"""
    app = QApplication(sys.argv)
    main_window = MainWindow()
    print(f"{main_window.label=}")
    print(f"{main_window.label.text()=}")
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    gui()
