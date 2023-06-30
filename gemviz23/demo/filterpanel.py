from PyQt5.QtWidgets import QGroupBox

from utils import myLoadUi

UI_FILE = "filterpanel.ui"


class FilterPanel(QGroupBox):
    """The panel to name a catalog and search it for runs."""

    def __init__(self, mainwindow):
        super().__init__()
        myLoadUi(UI_FILE, baseinstance=self)
        self.setup()

    def setup(self):
        pass  # TODO: lots more to do
