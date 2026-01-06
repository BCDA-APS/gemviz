"""
Visualize content of a Bluesky run.

* BRC: BlueskyRunsCatalog

.. autosummary::

    ~BRCRunVisualization
"""

from PyQt5 import QtWidgets

from .chartview import ChartView
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
        self.splitter.setStretchFactor(0, 4)  # top = 4/5
        self.splitter.setStretchFactor(1, 1)  # bottom = 1/5
        # Initialize log scale state
        self._log_x_state = False
        self._log_y_state = False
        self.setupLogScaleUI()

    def setMetadata(self, text, *args, **kwargs):
        self.metadata.setText(text)

    def setData(self, text, *args, **kwargs):
        self.data.setText(text)

    def setPlot(self, plot_widget):
        layout = self.plotPage.layout()
        utils.removeAllLayoutWidgets(layout)
        layout.addWidget(plot_widget)
        self.tabWidget.setCurrentWidget(self.plotPage)

        # Enable/disable log scale checkboxes based on chart availability
        has_chart = isinstance(plot_widget, ChartView)
        self.logXCheckBox.setEnabled(has_chart)
        self.logYCheckBox.setEnabled(has_chart)

        # Apply stored log scale state to the chart
        if has_chart:
            stored_log_x, stored_log_y = self.getLogScaleState()
            plot_widget.setLogScales(stored_log_x, stored_log_y)

    def setupLogScaleUI(self):
        """Setup the log scale UI components and connections"""
        # Connect log scale checkboxes
        self.logXCheckBox.toggled.connect(self.onLogScaleChanged)
        self.logYCheckBox.toggled.connect(self.onLogScaleChanged)
        # Initially disable until a chart is available
        self.logXCheckBox.setEnabled(False)
        self.logYCheckBox.setEnabled(False)

    def getLogScaleState(self):
        """Return the current state of logX and logY checkboxes"""
        return self._log_x_state, self._log_y_state

    def onLogScaleChanged(self):
        """Handle log scale checkbox changed"""
        self._log_x_state = self.logXCheckBox.isChecked()
        self._log_y_state = self.logYCheckBox.isChecked()

        # Apply to chart if available
        layout = self.plotPage.layout()
        if layout.count() > 0:
            widget = layout.itemAt(0).widget()
            if isinstance(widget, ChartView):
                widget.setLogScales(self._log_x_state, self._log_y_state)

    def setStatus(self, text):
        self.parent.setStatus(text)


# -----------------------------------------------------------------------------
# :copyright: (c) 2023-2025, UChicago Argonne, LLC
#
# Distributed under the terms of the Argonne National Laboratory Open Source License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
