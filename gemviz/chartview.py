"""
Charting widget
"""

from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget

# from .chartmodel import CustomTableModel


class ChartView(QtWidgets.QWidget):
    def __init__(self, parent, datasets=[]):
        self.parent = parent

        super().__init__()

        size = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )

        self.plot_widget = PlotWidget()
        for ds in datasets:
            self.plot(*ds)

        # QWidget Layout
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        ## plot
        size.setHorizontalStretch(4)
        self.plot_widget.setSizePolicy(size)
        layout.addWidget(self.plot_widget)

    def plot(self, *args, **kwargs):
        return self.plot_widget.plot(*args, **kwargs)
