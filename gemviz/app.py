#!/usr/bin/env python

"""
gemviz: Python Qt5 application to visualize Bluesky data from tiled server.
"""

import logging
import sys

logger = None  # to be set by main() from command line option


def gui():
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

    # fmt: off
    parser.add_argument(
        "--log",
        default="warning",
        help=(
            "Provide logging level. "
            "Example '--log debug'. "
            "Default level: 'warning'"),
        choices=[k.lower() for k in logging.getLevelNamesMapping()],
    )
    # fmt: on

    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser.parse_args()


def main():
    """Command-line entry point."""
    global logger

    options = command_line_interface()

    logging.basicConfig(level=options.log.upper())
    logger = logging.getLogger(__name__)
    logger.info("Logging level: %s", options.log)

    # set warning log level for (noisy) support packages
    for package in "httpcore httpx PyQt5 tiled".split():
        logging.getLogger(package).setLevel(logging.WARNING)

    gui()


if __name__ == "__main__":
    main()
