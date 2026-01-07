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
    run_double_selected = QtCore.pyqtSignal(object)

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

        self.setPage(page_offset, page_size)

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
        self.tableView.doubleClicked.connect(self.doRunDoubleClickSlot)

        # Auto-refresh for new runs
        self._len_glitch_detected = False
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self.checkForNewRuns)
        self.refresh_interval = 5000  # milliseconds (5 seconds)
        self.refresh_timer.start(self.refresh_interval)
        logger.info(f"Table auto-refresh enabled (interval: {self.refresh_interval}ms)")

        # Auto-size page based on visible rows
        self.tableView.viewport().installEventFilter(self)
        QtCore.QTimer.singleShot(100, self.updatePageSizeFromVisibleRows)

    def calculateVisibleRows(self):
        """Calculate the number of visible whole rows in the table view."""
        viewport = self.tableView.viewport()
        if viewport.height() <= 0:
            return 10  # Default fallback

        # Get available height for rows
        available_height = viewport.height()

        # Get the row height
        if self.model.rowCount() > 0:
            row_height = self.tableView.rowHeight(0)
            if row_height <= 0:
                row_height = self.tableView.verticalHeader().defaultSectionSize()
        else:
            row_height = self.tableView.verticalHeader().defaultSectionSize()

        if row_height <= 0:
            return 10

        # Calculate the number of visible whole rows
        visible_rows = max(1, available_height // row_height)
        return visible_rows

    def updatePageSizeFromVisibleRows(self):
        """Update page size based on number of visible rows."""
        visible_rows = self.calculateVisibleRows()
        if visible_rows != self.page_size:
            logger.debug(
                f"Updating page size from {self.page_size} to {visible_rows} (visible rows)"
            )
            # Preserve current offset if possible
            self.setPage(self.page_offset, visible_rows)
            self.setButtonPermissions()
            self.setPagerStatus()

    def eventFilter(self, obj, event):
        """Filter events to detect table viewport resize."""
        if obj == self.tableView.viewport() and event.type() == QtCore.QEvent.Resize:
            # Use a timer to debounce rapid resize events
            if not hasattr(self, "_resize_timer"):
                self._resize_timer = QtCore.QTimer(self)
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self.updatePageSizeFromVisibleRows)
            self._resize_timer.start(100)  # Wait 100ms after resize stops
        return super().eventFilter(obj, event)

    def doPagerButtons(self, action, **kwargs):
        """User clicked a button to change the page."""
        logger.debug("action=%s", action)

        if action == "first":
            self.setPage(0, self.page_size)
        elif action == "back":
            self.setPage(self.page_offset - self.page_size, self.page_size)
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
            else:
                # For non-active runs, still refresh occasionally to catch completed runs
                # Check if this run might have completed (refresh every 30 seconds)
                import time

                if (
                    not hasattr(run_md, "_last_refresh")
                    or time.time() - run_md._last_refresh > 30
                ):
                    run_md = tapi.RunMetadata(self.catalog(), uid)
                    run_md._last_refresh = time.time()
                    self.run_cache[uid] = run_md
            page[uid] = run_md

        # Send the page of runs to the model now.
        self.model.setRuns(page)

        # Restore selection based on selected_run_uid
        selected_uid = self.parent.selected_run_uid
        if selected_uid and selected_uid in page:
            row_index = list(page.keys()).index(selected_uid)
            self.tableView.selectRow(row_index)
        elif selected_uid:
            self.tableView.clearSelection()

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

    def doRunDoubleClickSlot(self, index):
        run_md = list(self.model.runs.values())[index.row()]
        self.run_double_selected.emit(run_md)

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

    def checkForNewRuns(self):
        """Check if new runs have been added to the catalog."""
        try:
            # Get the current catalog length
            current_length = len(self._catalog)

            # Work around a tiled client bug where len(...) occasionally returns 1.
            if current_length == 1 and self._catalog_length > 1:
                if not self._len_glitch_detected:
                    logger.debug(
                        "Ignoring transient len(catalog)==1 result (cached length=%s)",
                        self._catalog_length,
                    )
                    self._len_glitch_detected = True
                return

            self._len_glitch_detected = False

            # Only log when there's a change or every 10th check
            if not hasattr(self, "_check_count"):
                self._check_count = 0
            self._check_count += 1

            if current_length != self._catalog_length or self._check_count % 10 == 0:
                logger.debug(
                    f"Checking for new runs: current={current_length}, cached={self._catalog_length}"
                )

            if current_length != self._catalog_length:
                logger.info(
                    f"New runs detected: {self._catalog_length} -> {current_length}"
                )
                self._catalog_length = current_length

                # Always refresh the model to get new runs
                logger.info("Refreshing model with new runs")
                self.updateModelData()

                # If we're on the last page, go to the new last page
                if self.pagerAtEnd:
                    logger.info("Going to new last page to show new runs")
                    self.setPage(-1, self.page_size)  # Go to last page
                    self.setButtonPermissions()
                    self.setPagerStatus()

                    # Update status to show new runs available
                    self.setStatus(f"✨ New runs detected! Total: {current_length}")
                else:
                    # Just update the counter
                    self.setPagerStatus()
            else:
                # Even if no new runs, refresh the current page to update active runs
                # Only log every 5th refresh to reduce noise
                if self._check_count % 5 == 0:
                    logger.debug(
                        "No new runs, but refreshing current page for active run updates"
                    )
                self.updateModelData()

        except Exception as exc:
            logger.error(f"Error checking for new runs: {exc}", exc_info=True)


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
