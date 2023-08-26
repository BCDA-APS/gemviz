import __init__
import utils
from PyQt5.QtWidgets import QDialog


class LicenseDialog(QDialog):
    """ Show license text in a GUI window."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        self.setModal(True)
        license_text = open(__init__.LICENSE_FILE, "r").read()
        self.license.setText(license_text)
