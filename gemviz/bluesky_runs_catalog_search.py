"""
Search criteria for tiled "CatalogOfBlueskyRuns".

BRC: BlueskyRunsCatalog
"""

import logging

from PyQt5 import QtWidgets

from . import tapi
from . import utils

logger = logging.getLogger(__name__)


class BRCSearchPanel(QtWidgets.QWidget):
    """The panel to search a catalog for runs."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent
        self._server = None

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)

    def catalog(self):
        return self.parent.catalog()

    def setupCatalog(self, catalog_name, *args, **kwargs):
        from .date_time_range_slider import DAY

        def getStartTime(uid):
            return utils.ts2iso(tapi.get_md(cat[uid], "start", "time"))

        cat = self.catalog()
        if len(cat) == 0:
            self.setStatus(f"Catalog {catalog_name!r} has no runs.")
            return
        start_times = [
            getStartTime(cat.keys().first()),
            getStartTime(cat.keys().last()),
        ]
        t_low = min(start_times)
        t_high = max(start_times)
        t_high = utils.ts2iso(utils.iso2ts(t_high) + DAY)

        self.date_time_widget.setLimits(t_low, t_high)

    def enableDateRange(self, permission):
        self.date_time_widget.setEnabled(permission)

    def filteredCatalog(self):
        import tiled.queries

        cat = self.catalog()

        since = self.date_time_widget.low()
        until = self.date_time_widget.high()
        cat = tapi.get_tiled_runs(cat, since=since, until=until)
        logger.debug("since=%s, until=%s", since, until)

        plan_name = self.plan_name.text().strip()
        if len(plan_name) > 0:
            cat = tapi.get_tiled_runs(cat, plan_name=plan_name)

        scan_id = self.scan_id.text().strip()
        if len(scan_id) > 0:
            try:
                cat = tapi.get_tiled_runs(cat, scan_id=int(scan_id))
            except ValueError:
                self.setStatus("Invalid entry: scan_id must be an integer.")
                pass
                # TODO: PR #145 https://github.com/BCDA-APS/gemviz/pull/145
                # after updating tiled is updated (issue #53), we should try this:
                # import tiled.catalogs
                # empty_catalog = tiled.catalogs.Catalog.from_dict({})
                # return empty_catalog

        motors = self.positioners.text().strip()
        if len(motors) > 0:
            for motor in motors.split(","):
                cat = cat.search(tiled.queries.Contains("motors", motor.strip()))

        detectors = self.detectors.text().strip()
        if len(detectors) > 0:
            for detector in detectors.split(","):
                cat = cat.search(tiled.queries.Contains("detectors", detector.strip()))

        # TODO: exit status filtering

        logger.debug("filteredCatalog=%s", cat)
        return cat

    def setStatus(self, text):
        self.parent.setStatus(text)
