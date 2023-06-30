from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QDialog

import textwindow
import utils

# UI file name matches this module, different extension
UI_FILE = utils.getUiFileName(__file__)


class AboutDialog(QDialog):
    """loads a custom .ui file"""

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self.license_box = None
        self.settings = None  # TODO

        super().__init__(mainwindow)
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        import os

        pid = os.getpid()

        self.title.setText(utils.APP_TITLE)
        self.version.setText(f"version {utils.VERSION}")
        self.description.setText(utils.APP_DESC)
        self.authors.setText(", ".join(utils.AUTHOR_LIST))
        self.copyright.setText(utils.COPYRIGHT_TEXT)

        self.mainwindow.status = f"About {utils.APP_TITLE}, {pid=}"

        # handle the push buttons
        self.docs_pb.setToolTip(utils.DOCS_URL)
        self.issues_pb.setToolTip(utils.ISSUES_URL)
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
        self.doUrl(utils.DOCS_URL)

    def doIssuesUrl(self):
        """opening issues URL in default browser"""
        self.mainwindow.status = "opening issues URL in default browser"
        self.doUrl(utils.ISSUES_URL)

    def doLicense(self):
        """show the license"""
        if self.license_box is None:
            self.mainwindow.status = "opening License in new window"
            license_text = open(utils.LICENSE_FILE, "r").read()
            # history.addLog('DEBUG: ' + license_text)
            ui = textwindow.TextWindow(None, "LICENSE", license_text, self.settings)
            ui.setMinimumSize(700, 500)
            self.license_box = ui
        self.license_box.show()
