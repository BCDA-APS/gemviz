import utils
from PyQt5 import QtWidgets


class FilterPanel(QtWidgets.QWidget):
    """The panel to name a catalog and search it for runs."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self._server = None
        self._catalogSelected = None

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        from date_time_range_slider import DateTimeRangeSlider

        # add the date/time slider widget
        self.date_time_widget = DateTimeRangeSlider(self)
        self.TabWidgetPage1.layout().setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.date_time_widget
        )

        self.catalogs.currentTextChanged.connect(self.catalogSelected)

    def setCatalogs(self, catalogs):
        self.catalogs.clear()
        self.catalogs.addItems(catalogs)

    def server(self):
        return self._server

    def setServer(self, server):
        self._server = server
        self.setCatalogs(list(self._server))

    def catalogSelected(self, *args, **kwargs):
        print(f"catalogSelected: {args = }  {kwargs = }")
        self._catalogSelected = args[0]

        def getStartTime(uid):    
            run = cat[uid]
            start_time = run.metadata["start"]["time"]
            return utils.ts2iso(start_time)
        
        cat=self.catalog()
        start_times=[
            getStartTime(cat.keys().first()),
            getStartTime(cat.keys().last())
        ]
        t_low=min(start_times)
        t_high=max(start_times)

        self.date_time_widget.setMinimum(t_low)
        self.date_time_widget.setLow(t_low)
        self.date_time_widget.setHigh(t_high)
        self.date_time_widget.setMaximum(t_high)

        print(f"{t_low=} {t_high=}")
        
        



    def catalog(self):
        server=self.server()
        catalog_name=self._catalogSelected
        return server[catalog_name]
    
    def filteredCatalog(self):
        import tiled.queries
        cat=self.catalog()
        
        since = self.date_time_widget.low()
        until = self.date_time_widget.high()
        cat = utils.get_tiled_runs(cat, since=since, until=until)
        print(f"{since=} {until=}")

        plan_name=self.plan_name.text().strip()
        if len(plan_name) > 0:
            cat = utils.get_tiled_runs(cat, plan_name=plan_name)
        
        scan_id=self.scan_id.text().strip()
        if len(scan_id) > 0:
            cat = utils.get_tiled_runs(cat, scan_id=int(scan_id))

        motors=self.positioners.text().strip()
        if len(motors) > 0: 
            for motor in motors.split(","):
                cat = cat.search(tiled.queries.Contains("motors", motor.strip()))

        detectors=self.detectors.text().strip()
        if len(detectors) > 0: 
            for detector in detectors.split(","):
                cat = cat.search(tiled.queries.Contains("detectors", detector.strip()))

            


        # TODO: status filtering

        print(f"filteredCatalog: {cat=}")
        return cat
        
