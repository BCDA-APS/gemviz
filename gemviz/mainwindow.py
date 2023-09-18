import logging

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import APP_TITLE
from . import tapi
from . import utils
from .tiledserverdialog import LOCALHOST_URL
from .tiledserverdialog import TESTING_URL
from .tiledserverdialog import TILED_SERVER_SETTINGS_KEY
from .user_settings import settings

# TODO: remove testing URLs before production

MAX_RECENT_URI = 5
UI_FILE = utils.getUiFileName(__file__)
logger = logging.getLogger(__name__)


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
        logger.info("Status: %s", text)

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
        self.setServers(server_uri)

    def catalog(self):
        return self._catalog

    def catalogType(self):
        catalog = self.catalog()
        specs = catalog.specs
        logger.debug("specs=%s", specs)
        logger.debug(
            "structure_family=%s", catalog.item["attributes"]["structure_family"]
        )
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

    def setServerList(self, selected_uri=None):
        """Rebuild the list of server URIs."""
        recent_uris_str = settings.getKey(TILED_SERVER_SETTINGS_KEY)
        recent_uris_list = recent_uris_str.split(",") if recent_uris_str else []
        if selected_uri and self.isValidServerUri(selected_uri):
            final_uri_list = [selected_uri] + [
                uri
                for uri in recent_uris_list[: MAX_RECENT_URI - 1]
                if uri != selected_uri
            ]
            settings.setKey(TILED_SERVER_SETTINGS_KEY, ",".join(final_uri_list))
        else:
            # if no server selected in open dialog, keep the first pull down menu value to ""
            final_uri_list = [""] + recent_uris_list[:MAX_RECENT_URI]
        final_uri_list = [*final_uri_list, TESTING_URL, LOCALHOST_URL, "Other..."]
        self._serverList = final_uri_list

    def setServers(self, selected_uri):
        """Set the server URIs in the pop-up list"""
        self.setServerList(selected_uri)
        uri_list = self.serverList()
        self.server_uri.clear()
        self.server_uri.addItems(uri_list)

    def connectServer(self, server_uri):
        """Connect to the server URI and return URI and client"""
        self.clearContent()
        if server_uri == "Other...":
            self.doOpen()
        else:
            if not self.isValidServerUri(server_uri):
                self.setStatus("Invalid server URI.")
                return
            if server_uri is None:
                self.setStatus("No tiled server selected.")
                return
            self.setStatus(f"selected tiled {server_uri=!r}")
            try:
                client = tapi.connect_tiled_server(server_uri)
            except Exception as exc:
                self.setStatus(f"Error for {server_uri=!r}: {exc}")
                return
            self.setServer(server_uri, client)

    def isValidServerUri(self, server_uri):
        """Check if the server URI is valid and absolute."""
        url = QtCore.QUrl(server_uri)
        return url.isValid() and not url.isRelative()

    def server(self):
        return self._server

    def setServer(self, uri, server):
        """Define the tiled server URI."""
        self._server = server
        self.setCatalogs(list(server))
