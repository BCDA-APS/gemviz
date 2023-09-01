#!/usr/bin/env python

"""
gemviz: Python Qt5 application to visualize Bluesky data from tiled server.
"""

import sys


def gui(*args, **kwargs):
    """Display the main window"""
    from PyQt5 import QtWidgets

    from .mainwindow import MainWindow

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.setStatus("Application started ...")
    main_window.show()
    sys.exit(app.exec())


def command_line_interface():
    import argparse
    from . import __version__

    doc = __doc__.strip().splitlines()[0]
    parser = argparse.ArgumentParser(description=doc)

    parser.add_argument(
        "-v", "--version", action="version", version=__version__
    )

    return parser.parse_args()


def main():  # for future command-line options
    options = command_line_interface()
    # print(f"{options=}")
    gui()


if __name__ == "__main__":
    main()
