from PyQt5 import QtWidgets

from . import utils
from .app_settings import settings

UI_FILE = utils.getUiFileName(__file__)


class MainWindow(QtWidgets.QMainWindow):
    """The main window of the app, built in Qt designer."""

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        from . import APP_TITLE

        self._server = None
        self._catalog = None
        self.mvc_catalog = None

        self.setWindowTitle(APP_TITLE)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        self.catalogs.currentTextChanged.connect(self.setCatalog)

        settings.restoreWindowGeometry(self, "mainwindow_geometry")

    @property
    def status(self):
        return self.statusbar.currentMessage()

    def setStatus(self, text, timeout=0):
        """Write new status to the main window."""
        self.statusbar.showMessage(str(text), msecs=timeout)
        # TODO: log the text

    def doAboutDialog(self, *args, **kw):
        """
        Show the "About ..." dialog
        """
        from .aboutdialog import AboutDialog

        about = AboutDialog(self)
        about.open()

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
        self.setStatus("Application quitting ...")

        settings.saveWindowGeometry(self, "mainwindow_geometry")

        self.close()

    def doOpen(self, *args, **kw):
        """
        User chose to open (connect with) a tiled server.
        """
        from .tiledserverdialog import TILED_SERVER_SETTINGS_KEY, TiledServerDialog

        previous_uri = settings.getKey(TILED_SERVER_SETTINGS_KEY) or ""
        server_uri = TiledServerDialog.getServer(self)
        if server_uri is None:
            self.setStatus("No tiled server selected.")
            return
        self.setStatus(f"selected tiled {server_uri=!r}")

        try:
            client = utils.connect_tiled_server(server_uri)
        except Exception as exc:
            self.setStatus(f"Error for {server_uri=!r}: {exc}")
            settings.setKey(TILED_SERVER_SETTINGS_KEY, previous_uri)
            return

        self.setServer(server_uri, client)

    def catalog(self):
        return self._catalog

    def catalogType(self):
        catalog = self.catalog()
        specs = catalog.specs
        # print(f"{specs=}")
        # print(f'{catalog.item["attributes"]["structure_family"]=}')
        try:
            spec = specs[0]
            spec_name = f"{spec.name}, v{spec.version}"
        except IndexError:
            spec_name = "not supported now"
        return spec_name

    def catalogName(self):
        return self._catalogName

    def setCatalog(self, catalog_name):
        """A catalog was selected (from the pop-up menu)."""
        self.setStatus(f"Selected catalog {catalog_name!r}.")
        if len(catalog_name) == 0 or catalog_name not in self.server():
            if len(catalog_name) > 0:
                self.setStatus(f"Catalog {catalog_name!r} is not supported now.")
            return
        self._catalogName = catalog_name
        self._catalog = self.server()[catalog_name]

        spec_name = self.catalogType()
        self.spec_name.setText(spec_name)
        self.setStatus(f"catalog {catalog_name!r} is {spec_name!r}")

        layout = self.groupbox.layout()
        utils.removeAllLayoutWidgets(layout)

        if spec_name == "CatalogOfBlueskyRuns, v1":
            from .bluesky_runs_catalog import BRC_MVC

            self.mvc_catalog = BRC_MVC(self)
            layout.addWidget(self.mvc_catalog)
        else:
            self.mvc_catalog = None
            layout.addWidget(QtWidgets.QWidget())  # nothing to show

    def setCatalogs(self, catalogs):
        """Set the names (of server's catalogs) in the pop-up list."""
        self.catalogs.clear()
        self.catalogs.addItems(catalogs)

    def server(self):
        return self._server

    def setServer(self, uri, server):
        """Define the tiled server URI."""
        self._server = server
        self.server_uri.setText(f"tiled server: {uri}")
        self.setCatalogs(list(server))
