from PyQt5 import QtWidgets

from .. import aboutdialog


def test_about_starts(qtbot):
    """About dialog should start with no errors."""

    class SetStatusWidget(QtWidgets.QWidget):
        """Test class with setStatus() method."""

        def setStatus(self, status):
            pass

    widget_with_status = SetStatusWidget()

    dialog = aboutdialog.AboutDialog(widget_with_status)
    dialog.show()
    qtbot.addWidget(dialog)
    assert dialog is not None
