from PyQt5.QtWidgets import QWidget

import utils


class FilterPanel(QWidget):
    """The panel to name a catalog and search it for runs."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        pass  # TODO: lots more to do
