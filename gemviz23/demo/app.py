#!/usr/bin/env python

"""
gemviz23: Python Qt5 application to demonstrate multiple UI files.
"""

import sys

from PyQt5.QtWidgets import QApplication


def gui():
    """Display the main window"""
    from mainwindow import MainWindow

    app = QApplication(sys.argv)
    main_window = MainWindow()
    print(f"{main_window.status=}")
    main_window.status = "Application started ..."
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    gui()
