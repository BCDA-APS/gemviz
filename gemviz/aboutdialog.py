from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtWidgets import QDialog

from . import APP_DESC
from . import APP_TITLE
from . import AUTHOR_LIST
from . import COPYRIGHT_TEXT
from . import DOCS_URL
from . import ISSUES_URL
from . import LICENSE_FILE
from . import __version__
from . import textwindow
from . import utils


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

        self.setWindowTitle(f"About ... {APP_TITLE}")
        self.title.setText(APP_TITLE)
        self.version.setText(f"version {__version__}")
        self.description.setText(APP_DESC)
        self.authors.setText(", ".join(AUTHOR_LIST))
        self.copyright.setText(COPYRIGHT_TEXT)

        self.mainwindow.setStatus(f"About {APP_TITLE}, {pid=}")

        # handle the push buttons
        self.docs_pb.setToolTip(DOCS_URL)
        self.issues_pb.setToolTip(ISSUES_URL)
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
        self.mainwindow.setStatus("opening documentation URL in default browser")
        self.doUrl(DOCS_URL)

    def doIssuesUrl(self):
        """opening issues URL in default browser"""
        self.mainwindow.setStatus("opening issues URL in default browser")
        self.doUrl(ISSUES_URL)

    def doLicense(self):
        """show the license"""
        if self.license_box is None:
            self.mainwindow.setStatus("opening License in new window")
            license_text = open(LICENSE_FILE, "r").read()
            # history.addLog('DEBUG: ' + license_text)
            # FIXME: Since "About" is now modal, cannot close this license window!
            # Only closes when About closes.
            ui = textwindow.TextWindow(None, "LICENSE", license_text)
            ui.setMinimumSize(700, 500)
            self.license_box = ui
        self.license_box.show()
