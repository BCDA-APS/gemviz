"""
QTableView of tiled "CatalogOfBlueskyRuns".

BRC: BlueskyRunsCatalog

Uses :class:`bluesky_runs_catalog_table_model.BRCTableModel`.

.. autosummary::

    ~BRCTableView
"""

import logging
from functools import partial

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import utils

logger = logging.getLogger(__name__)


class BRCTableView(QtWidgets.QWidget):
    ui_file = utils.getUiFileName(__file__)
    run_selected = QtCore.pyqtSignal(object)

    def __init__(self, parent, catalog, page_offset, page_size):
        self.parent = parent
        self._catalog = catalog
        self._catalog_length = len(catalog)
        self.run_cache = {}

        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup(page_offset, page_size)

    def setup(self, page_offset, page_size):
        """Setup the catalog view panel."""
        from .bluesky_runs_catalog_table_model import BRCTableModel

        self.model = BRCTableModel(self)
        self.tableView.setModel(self.model)

        # since we cannot set header's ResizeMode in Designer ...
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        if self.pageSize.findText(str(page_size)) == -1:
            self.pageSize.insertItem(0, str(page_size))
        self.pageSize.setCurrentText(str(page_size))
        self.setPage(page_offset, page_size)

        self.pageSize.currentTextChanged.connect(
            partial(self.doPagerButtons, "pageSize")
        )
        for button_name in "first back next last".split():
            button = getattr(self, button_name)
            # custom: pass the button name to the receiver
            button.released.connect(partial(self.doPagerButtons, button_name))

        self.parent.brc_search_panel.enableDateRange(
            len(self.parent.brc_search_panel.catalog()) > 0
        )

        self.setButtonPermissions()
        self.setPagerStatus()
        self.tableView.clicked.connect(self.doRunSelectedSlot)

    def doPagerButtons(self, action, **kwargs):
        """User clicked a button to change the page."""
        logger.debug("action=%s", action)

        if action == "first":
            self.setPage(0, self.page_size)
        elif action == "back":
            self.setPage(self.page_offset - self.page_size, self.page_size)
        elif action == "pageSize":
            self.setPage(self.page_offset, self.pageSize.currentText())
        elif action == "next":
            self.setPage(self.page_offset + self.page_size, self.page_size)
        elif action == "last":
            self.setPage(-1, self.page_size)

        self.setButtonPermissions()
        self.setPagerStatus()

    @property
    def pagerAtStart(self):
        """Is this the first page?"""
        return self.page_offset == 0

    @property
    def pagerAtEnd(self):
        """Is this the last page?"""
        # number is zero-based
        return (self.page_offset + self.page_size) >= self.catalogLength()

    def setButtonPermissions(self):
        """Enable/disable the pager buttons, depending on page in view."""
        first_page = self.pagerAtStart
        last_page = self.pagerAtEnd

        self.first.setEnabled(not first_page)
        self.back.setEnabled(not first_page)
        self.next.setEnabled(not last_page)
        self.last.setEnabled(not last_page)

    def setPage(self, offset, size):
        """Choose the page.  Update the model."""
        # user cannot edit directly, not expected to raise an exception
        offset = int(offset)
        size = int(size)

        self.page_size = max(0, min(size, self.catalogLength()))
        if offset >= 0:
            offset = min(offset, self.catalogLength() - self.page_size)
        else:
            offset = self.catalogLength() - self.page_size
        self.page_offset = max(0, offset)
        if int(self.pageSize.currentText()) != self.page_size:
            self.pageSize.setCurrentText(str(self.page_size))
        logger.debug(
            "len(catalog)=%d  offset=%d  size=%d",
            self.catalogLength(),
            self.page_offset,
            self.page_size,
        )

        # TODO: unselect row if selection is not on the page
        # see: https://stackoverflow.com/questions/64225673
        # "how-to-deselect-an-entire-qtablewidget-row"

        self.updateModelData()

    def updateModelData(self):
        """Send a new page of runs to the model."""
        from . import tapi

        # get list of metadata for each run to be shown in the table
        start = self.page_offset
        end = self.page_offset + self.page_size
        uid_list = self.catalog().keys()[start:end]

        page = {}  # the new page of run metadata
        for uid in uid_list:
            run_md = self.run_cache.get(uid)
            if run_md is None or run_md.active:
                # Get new information from the server about this run.
                run_md = tapi.RunMetadata(self.catalog(), uid)
                self.run_cache[uid] = run_md  # update the cache
            page[uid] = run_md

        # Send the page of runs to the model now.
        self.model.setRuns(page)

    def setPagerStatus(self, text=None):
        if text is None:
            total = self.catalogLength()  # filtered catalog
            if total == 0:
                text = "No runs"
            else:
                start = self.page_offset
                end = start + self.page_size
                text = f"{start + 1}-{end} of {total} runs"

        self.status.setText(text)
        self.setStatus(text)

    def doRunSelectedSlot(self, index):
        run_md = list(self.model.runs.values())[index.row()]
        self.run_selected.emit(run_md)

    def setCatalog(self, catalog):
        self._catalog = catalog  # filtered catalog
        self._catalog_length = len(catalog)

        uid = self.parent.selected_run_uid
        if uid in self.model.runs:
            offset = list(self.model.runs.keys()).index(uid)
        else:
            offset = -1
        self.setPage(offset, self.page_size)  # ... and update the model
        self.setPagerStatus()

    def catalog(self):
        return self._catalog

    def catalogLength(self):
        # Avoid a bug in the tiled client.  When the client is asked for
        # len(catalog) frequently, it will begin to return a length of ``1``
        # instead of the actual length.  After waiting a short while, the client
        # will return the actual length again.
        return self._catalog_length

    def setStatus(self, text):
        self.parent.setStatus(text)


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2024, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
