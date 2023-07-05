from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QDialog

import __init__
import textwindow
import utils


class AboutDialog(QDialog):
    """Load a generic About... Dialog as a .ui file."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.license_box = None
        self.settings = None  # TODO

        super().__init__(mainwindow)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        import os

        pid = os.getpid()

        self.setWindowTitle(f"About ... {__init__.APP_TITLE}")
        self.title.setText(__init__.APP_TITLE)
        self.version.setText(f"version {__init__.VERSION}")
        self.description.setText(__init__.APP_DESC)
        self.authors.setText(", ".join(__init__.AUTHOR_LIST))
        self.copyright.setText(__init__.COPYRIGHT_TEXT)

        self.mainwindow.status = f"About {__init__.APP_TITLE}, {pid=}"

        # handle the push buttons
        self.docs_pb.setToolTip(__init__.DOCS_URL)
        self.issues_pb.setToolTip(__init__.ISSUES_URL)
        self.docs_pb.clicked.connect(self.doDocsUrl)
        self.issues_pb.clicked.connect(self.doIssuesUrl)
        self.license_pb.clicked.connect(self.doLicense)

        self.setModal(False)

    def closeEvent(self, event):
        """
        called when user clicks the big [X] to quit
        """
        if self.license_box is not None:
            self.license_box.close()
        event.accept()  # let the window close

    def doUrl(self, url):
        """opening URL in default browser"""
        url = QtCore.QUrl(url)
        service = QtGui.QDesktopServices()
        service.openUrl(url)

    def doDocsUrl(self):
        """opening documentation URL in default browser"""
        self.mainwindow.status = "opening documentation URL in default browser"
        self.doUrl(__init__.DOCS_URL)

    def doIssuesUrl(self):
        """opening issues URL in default browser"""
        self.mainwindow.status = "opening issues URL in default browser"
        self.doUrl(__init__.ISSUES_URL)

    def doLicense(self):
        """show the license"""
        if self.license_box is None:
            self.mainwindow.status = "opening License in new window"
            license_text = open(__init__.LICENSE_FILE, "r").read()
            # history.addLog('DEBUG: ' + license_text)
            # FIXME: Since "About" is now modal, cannot close this license window!
            # Only closes when About closes.
            ui = textwindow.TextWindow(None, "LICENSE", license_text)
            ui.setMinimumSize(700, 500)
            self.license_box = ui
        self.license_box.show()
