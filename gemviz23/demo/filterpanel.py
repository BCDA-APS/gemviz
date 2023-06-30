from PyQt5.QtWidgets import QGroupBox

import utils

# UI file name matches this module, different extension
UI_FILE = utils.getUiFileName(__file__)


class FilterPanel(QGroupBox):
    """The panel to name a catalog and search it for runs."""

    def __init__(self, mainwindow):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        pass  # TODO: lots more to do
