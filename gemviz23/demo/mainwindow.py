from PyQt5.QtWidgets import QMainWindow, QHBoxLayout

from utils import APP_TITLE, myLoadUi

UI_FILE = "mainwindow.ui"


class MainWindow(QMainWindow):
    """The main window of the app, built in Qt designer."""

    def __init__(self):
        super().__init__()
        myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        from filterpanel import FilterPanel

        self.title.setText(APP_TITLE)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionQuit.triggered.connect(self.doClose)

        self.filter_layout.addWidget(FilterPanel(self))

    @property
    def status(self):
        return self.statusbar.currentMessage()

    @status.setter
    def status(self, text, timeout=0):
        self.statusbar.showMessage(str(text), msecs=timeout)

    def doAboutDialog(self, *args, **kw):
        """
        Show the "About ..." dialog
        """
        from aboutdialog import AboutDialog

        about = AboutDialog(self)
        about.show()

    def doClose(self, *args, **kw):
        """
        User chose exit (or quit), or closeEvent() was called.
        """
        self.status = "Application quitting ..."
        # history.addLog('application exit requested', False)
        # if self.cannotProceed():
        #     if self.confirmAbandonChangesNotOk():
        #         return

        # self.saveWindowGeometry()
        # self.closeSubwindows()
        self.close()
