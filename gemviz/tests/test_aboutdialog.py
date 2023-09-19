from PyQt5 import QtWidgets

from .. import aboutdialog


def test_about_starts(qtbot):
    class SetStatusWidget(QtWidgets.QWidget):
        def setStatus(self, status):
            pass

    widget_with_status = SetStatusWidget()

    dialog = aboutdialog.AboutDialog(widget_with_status)
    dialog.show()
    qtbot.addWidget(dialog)
    assert dialog is not None  # basic test that widget started with no error
