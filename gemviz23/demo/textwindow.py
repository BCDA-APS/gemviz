"""
Show text in a GUI window.
"""

from PyQt5.QtWidgets import QWidget

import utils


class TextWindow(QWidget):
    """
    Show text in a GUI window.

    :param obj parent: instance of QWidget
    :param str title: to be used as the window title
    :param str text: window content
    """

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, title="window title", text=""):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup(text, title)

    def setup(self, text, title):
        self.setText(text)
        self.setTitle(title)

    def setText(self, text):
        """Set the window content (the text)."""
        self.plainTextEdit.setPlainText(text)

    def setTitle(self, title):
        """Set the window's title."""
        self.setWindowTitle(title)
