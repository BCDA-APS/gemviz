from PyQt5.QtWidgets import QMainWindow

from app_settings import settings
import __init__
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

        self.title.setText(__init__.APP_TITLE)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        self.filter_scroll.setWidget(FilterPanel(self))

        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        settings.restoreSplitterDetails(self.hsplitter, "mainwindow_horizontal_splitter")
        settings.restoreSplitterDetails(self.vsplitter, "mainwindow_vertical_splitter")

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
        about.exec()

    def doClose(self, *args, **kw):
        """
        User chose exit (or quit), or closeEvent() was called.
        """
        # FIXME: Close the window with the X did not get here.
        self.status = "Application quitting ..."
        # history.addLog('application exit requested', False)
        # if self.cannotProceed():
        #     if self.confirmAbandonChangesNotOk():
        #         return

        settings.saveWindowGeometry(self, "mainwindow_geometry")
        settings.saveSplitterDetails(self.hsplitter, "mainwindow_horizontal_splitter")
        settings.saveSplitterDetails(self.vsplitter, "mainwindow_vertical_splitter")
        # self.closeSubwindows()
        self.close()

    def doOpen(self, *args, **kw):
        """
        User chose to open (connect with) a tiled server.
        """
        from tiledserverdialog import TiledServerDialog

        server = TiledServerDialog.getServer(self)
        if server is None:
            self.status = "No tiled server selected."
        else:
            self.status = f"tiled {server=!r}"
            # TODO: do something, such as connect with the server
