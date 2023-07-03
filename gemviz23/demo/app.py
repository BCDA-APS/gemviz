#!/usr/bin/env python

"""
gemviz23: Python Qt5 application to demonstrate multiple UI files.
"""

import sys


def gui():
    """Display the main window"""
    from PyQt5.QtWidgets import QApplication

    from mainwindow import MainWindow

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.status = "Application started ..."
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    gui()
