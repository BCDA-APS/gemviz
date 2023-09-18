"""
Visualize content of a Bluesky run.

* BRC: BlueskyRunsCatalog

.. autosummary::

    ~BRCRunVisualization
"""

from PyQt5 import QtWidgets

from . import utils


class BRCRunVisualization(QtWidgets.QWidget):
    """The panel to show the contents of a run."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__()
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        pass

    def setMetadata(self, text, *args, **kwargs):
        self.metadata.setText(text)

    def setData(self, text, *args, **kwargs):
        self.data.setText(text)

    def setPlot(self, plot_widget):
        layout = self.plotPage.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(plot_widget)
        self.tabWidget.setCurrentWidget(self.plotPage)

    def setStatus(self, text):
        self.parent.setStatus(text)
