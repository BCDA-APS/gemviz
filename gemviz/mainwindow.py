"""
gemviz main window
"""

# TODO: remove testing URLs before production

import logging

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import APP_TITLE
from . import tapi
from . import utils
from .tiledserverdialog import LOCALHOST_URL
from .tiledserverdialog import TILED_SERVER_SETTINGS_KEY
from .user_settings import settings

TESTING_URLS = [LOCALHOST_URL]
MAX_RECENT_URI = 5
UI_FILE = utils.getUiFileName(__file__)
SORT_ASCENDING = 1
SORT_DESCENDING = -SORT_ASCENDING
SORT_DIRECTION = SORT_ASCENDING
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

        # Sort preference: load the setting and set checked state
        newest_first = self._getSortPreference()
        self.actionSortNewestFirst.setChecked(newest_first)
        self.actionSortNewestFirst.triggered.connect(self.toggleSortOrder)

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

    def _getSortPreference(self):
        """Get the sort preference setting as a boolean."""
        newest_first = settings.getKey("catalog_sort_newest_first")
        if newest_first is None:
            return True  # Default to newest first
        elif isinstance(newest_first, str):
            return newest_first.lower() in ("true", "1", "yes")
        return bool(newest_first)

    def toggleSortOrder(self):
        """Toggle the sort order preference and refresh the catalog."""
        newest_first = self.actionSortNewestFirst.isChecked()
        settings.setKey("catalog_sort_newest_first", newest_first)

        # Refresh the current catalog with new sort order
        if self._catalogName:
            self.setStatus(
                f"Sort order changed to {'newest first' if newest_first else 'oldest first'}"
            )
            self.setCatalog(self._catalogName)

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
            spec_name = f"{spec.name}"
        except IndexError:
            spec_name = "not supported now"
        return spec_name

    def catalogName(self):
        return self._catalogName

    def setCatalog(self, catalog_name, sort_direction=SORT_DIRECTION):
        """A catalog was selected (from the pop-up menu)."""
        self.setStatus(f"Selected catalog {catalog_name!r}.")
        if len(catalog_name) == 0:
            return
        try:
            # Try to access the catalog (works for both top-level and nested paths)
            catalog_node = self.server()[catalog_name]
        except (KeyError, ValueError) as exc:
            self.setStatus(f"Catalog {catalog_name!r} is not accessible: {exc}")
            return
        self._catalogName = catalog_name

        # Detect version
        version = None
        try:
            if hasattr(catalog_node, "specs") and len(catalog_node.specs) > 0:
                spec = catalog_node.specs[0]
                if tapi.is_catalog_of_bluesky_runs(catalog_node):
                    version = spec.version
        except Exception:
            pass

        # Sort by time - use user preference for sort order
        newest_first = self._getSortPreference()
        sort_direction = -1 if newest_first else 1

        # Choose sort field based on version
        if version == "1":
            sort_field = "time"  # old server (0.1.0)
        else:
            sort_field = "start.time"  # new server (0.2.2)

        logger.debug(
            f"Sort preference: newest_first={newest_first}, sort_direction={sort_direction}, "
            f"version={version}, sort_field={sort_field}"
        )
        self._catalog = catalog_node.sort((sort_field, sort_direction))

        spec_name = self.catalogType()
        self.spec_name.setText(spec_name)
        self.setStatus(f"catalog {catalog_name!r} is {spec_name!r}")

        layout = self.groupbox.layout()
        self.clearContent(clear_cat=False)

        if spec_name == "CatalogOfBlueskyRuns":
            from .bluesky_runs_catalog import BRC_MVC

            self.mvc_catalog = BRC_MVC(self)
            layout.addWidget(self.mvc_catalog)
        else:
            # Not expected to run this branch since cannot select
            # catalog we cannot handle.
            self.mvc_catalog = None
            layout.addWidget(QtWidgets.QWidget())  # nothing to show

    def setCatalogs(self, catalogs):
        """
        Set the names (of server's catalogs) in the pop-up list.

        Recursively discovers all CatalogOfBlueskyRuns, including nested ones.
        """
        self.catalogs.clear()
        server = self.server()

        # Check version
        version = None
        try:
            for key in catalogs:
                node = server[key]
                if tapi.is_catalog_of_bluesky_runs(node):
                    spec = node.specs[0]
                    version = spec.version
                    break
        except Exception:
            pass

        if version == "1":
            # Old server - just check top-level items
            for key in catalogs:
                try:
                    node = server[key]
                    if tapi.is_catalog_of_bluesky_runs(node):
                        self.catalogs.addItem(key)
                except Exception:
                    continue
        else:
            # New server - use nested discovery
            discovered = tapi.discover_catalogs(server, deep_search=False)
            for path, _ in discovered:
                self.catalogs.addItem(path)

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
            # if no server selected in open dialog,
            # keep the first pull down menu value to ""
            final_uri_list = [""] + recent_uris_list[:MAX_RECENT_URI]
        final_uri_list += TESTING_URLS
        final_uri_list.append("Other...")
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
            # Update recent servers list
            self.setServerList(server_uri)

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


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
