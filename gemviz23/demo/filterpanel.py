import utils
from PyQt5.QtWidgets import QWidget


class FilterPanel(QWidget):
    """The panel to name a catalog and search it for runs."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow
        self._server = None

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
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
    