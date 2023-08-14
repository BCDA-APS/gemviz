import __init__
import utils
from app_settings import settings
from PyQt5 import QtWidgets

UI_FILE = utils.getUiFileName(__file__)


class MainWindow(QtWidgets.QMainWindow):
    """The main window of the app, built in Qt designer."""

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        from filterpanel import FilterPanel
        from resultwindow import ResultWindow
        from vizpanel import VizPanel

        self.setWindowTitle(__init__.APP_TITLE)
        self.title.setText(__init__.APP_TITLE)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        self.filter_panel = FilterPanel(self)
        layout = self.filter_groupbox.layout()
        layout.addWidget(self.filter_panel)

        self.results = ResultWindow(self)
        layout = self.runs_groupbox.layout()
        layout.addWidget(self.results)

        self.viz = VizPanel(self)
        layout = self.viz_groupbox.layout()
        layout.addWidget(self.viz)

        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        settings.restoreSplitter(self.hsplitter, "mainwindow_horizontal_splitter")
        settings.restoreSplitter(self.vsplitter, "mainwindow_vertical_splitter")

    @property
    def status(self):
        return self.statusbar.currentMessage()

    @status.setter
    def status(self, text, timeout=0):
        """Write new status to the main window."""
        self.statusbar.showMessage(str(text), msecs=timeout)

    def doAboutDialog(self, *args, **kw):
        """
        Show the "About ..." dialog
        """
        from aboutdialog import AboutDialog

        about = AboutDialog(self)
        about.exec()

    def closeEvent(self, event):
        """
        User clicked the big [X] to quit.
        """
        self.doClose()
        event.accept()  # let the window close

    def doClose(self, *args, **kw):
        """
        User chose exit (or quit), or closeEvent() was called.
        """
        self.status = "Application quitting ..."

        settings.saveWindowGeometry(self, "mainwindow_geometry")
        settings.saveSplitter(self.hsplitter, "mainwindow_horizontal_splitter")
        settings.saveSplitter(self.vsplitter, "mainwindow_vertical_splitter")

        self.close()

    def doOpen(self, *args, **kw):
        """
        User chose to open (connect with) a tiled server.
        """
        from app_settings import settings
        from tiledserverdialog import TILED_SERVER_SETTINGS_KEY, TiledServerDialog

        previous_uri = settings.getKey(TILED_SERVER_SETTINGS_KEY) or ""
        server_uri = TiledServerDialog.getServer(self)
        if server_uri is None:
            self.status = "No tiled server selected."
            return
        self.status = f"selected tiled {server_uri=!r}"

        try:
            client = utils.connect_tiled_server(server_uri)
        except Exception as exc:
            self.status = f"Error for {server_uri=!r}: {exc}"
            settings.setKey(TILED_SERVER_SETTINGS_KEY, previous_uri)
            return

        self.filter_panel.setServer(client)
