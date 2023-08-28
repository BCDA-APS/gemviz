from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import APP_TITLE
from . import utils
from .app_settings import settings
from .tiledserverdialog import LOCALHOST_URL
from .tiledserverdialog import TESTING_URL
from .tiledserverdialog import TILED_SERVER_SETTINGS_KEY

# TODO: remove testing URLs before production

UI_FILE = utils.getUiFileName(__file__)


class MainWindow(QtWidgets.QMainWindow):
    """The main window of the app, built in Qt designer."""

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        self._server = None
        self._catalog = None
        self._serverList = None
        self.mvc_catalog = None

        self.setWindowTitle(APP_TITLE)
        self.setServers(None)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        self.server_uri.currentTextChanged.connect(self.connectServer)
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
        from .tiledserverdialog import TiledServerDialog

        server_uri = TiledServerDialog.getServer(self)
        if not server_uri:
            self.clearContent()
        uri_list = self.serverList()
        if uri_list[0] == "":
            uri_list[0] = server_uri
        else:
            uri_list.insert(0, server_uri)
        self.setServers(uri_list)

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
        self.clearContent(clear_cat=False)

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

    def clearContent(self, clear_cat=True):
        layout = self.groupbox.layout()
        utils.removeAllLayoutWidgets(layout)
        if clear_cat:
            self.catalogs.clear()

    def serverList(self):
        return self._serverList

    def setServerList(self, uri_list=None):
        """Set the list of server URIs and remove duplicate"""
        unique_uris = set()
        new_server_list = []

        if not uri_list:
            previous_uri = settings.getKey(TILED_SERVER_SETTINGS_KEY)
            candidate_uris = ["", previous_uri, TESTING_URL, LOCALHOST_URL, "Other..."]
        else:
            candidate_uris = uri_list
        for uri in candidate_uris:
            if uri not in unique_uris:  # Check for duplicates
                unique_uris.add(uri)
                new_server_list.append(uri)
        self._serverList = new_server_list

    def setServers(self, uri_list):
        """Set the server URIs in the pop-up list"""
        self.setServerList(uri_list)
        uri_list = self.serverList()
        self.server_uri.clear()
        self.server_uri.addItems(uri_list)

    def connectServer(self, server_uri):
        """Connect to the server URI and return URI and client"""
        self.clearContent()
        if server_uri == "Other...":
            self.doOpen()
        else:
            # check the value
            url = QtCore.QUrl(server_uri)
            # print(f"{url=} {url.isValid()=} {url.isRelative()=}")
            if url.isValid() and not url.isRelative():
                settings.setKey(TILED_SERVER_SETTINGS_KEY, server_uri)
            else:
                return
            previous_uri = settings.getKey(TILED_SERVER_SETTINGS_KEY) or ""
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

    def server(self):
        return self._server

    def setServer(self, uri, server):
        """Define the tiled server URI."""
        self._server = server
        self.setCatalogs(list(server))
