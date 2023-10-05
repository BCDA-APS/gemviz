from PyQt5 import QtWidgets

from .. import aboutdialog


def test_about_starts(qtbot):
    """About dialog should start with no errors."""

    class SetStatusWidget(QtWidgets.QWidget):
        """Test class with setStatus() method."""

        def setStatus(self, status):
            pass

    fake_main_window = SetStatusWidget()

    dialog = aboutdialog.AboutDialog(fake_main_window)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog is not None
