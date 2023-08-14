#!/usr/bin/env python

"""
gemviz: Python Qt5 application to visualize Bluesky data from tiled server.
"""

import sys


def gui():
    """Display the main window"""
    from mainwindow import MainWindow
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.status = "Application started ..."
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    gui()
