from PyQt5.QtWidgets import QHBoxLayout, QMainWindow

import utils

UI_FILE = utils.getUiFileName(__file__)


class MainWindow(QMainWindow):
    """The main window of the app, built in Qt designer."""

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        from filterpanel import FilterPanel

        self.title.setText(utils.APP_TITLE)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

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

    def doOpen(self, *args, **kw):
        """
        User chose to open (connect with) a tiled server.
        """
        from tiledserverdialog import TiledServerDialog

        self.status = "TODO: Open connection with a tiled server ..."
        self.status = "before"
        server = TiledServerDialog.getServer(self)
        self.status = "after"
        print(f"{server=}")
