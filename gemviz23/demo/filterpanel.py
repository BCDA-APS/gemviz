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

    def catalog(self):
        server=self.server()
        catalog_name=self._catalogSelected
        return server[catalog_name]
    
    def filteredCatalog(self):
        cat=self.catalog()
        
        plan_name=self.plan_name.text().strip()
        if len(plan_name) > 0:
            cat = utils.get_tiled_runs(cat, plan_name=plan_name)
        
        scan_id=self.scan_id.text().strip()
        if len(scan_id) > 0:
            cat = utils.get_tiled_runs(cat, scan_id=int(scan_id))

        motors=self.positioner.text().strip()
        if len(motors) > 0: 
            for motor in motors.split(" "):
                cat = utils.get_tiled_runs(cat, motors=motor)


        # TODO: status filtering

        print(f"filteredCatalog: {cat=}")
        return cat
        
