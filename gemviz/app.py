#!/usr/bin/env python

"""
gemviz: Python Qt5 application to visualize Bluesky data from tiled server.
"""

import sys


def gui():
    """Display the main window"""
    from PyQt5 import QtWidgets

    from .mainwindow import MainWindow

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setStatus("Application started ...")
    main_window.show()
    sys.exit(app.exec())


def main():  # for future command-line options
    gui()


if __name__ == "__main__":
    main()
