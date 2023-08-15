from PyQt5 import QtWidgets

import utils


class BlueskyRunsCatalogMVC(QtWidgets.QWidget):
    """MVC class for CatalogOfBlueskyRuns."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        # TODO: restore splitter settings (and save when ...)
        # settings.restoreSplitter(self.hsplitter, "blueskyrunscatalogmvc_horizontal_splitter")
        # settings.restoreSplitter(self.vsplitter, "blueskyrunscatalogmvc_vertical_splitter")
        pass
