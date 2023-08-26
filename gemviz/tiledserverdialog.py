from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QDialog

from . import utils
from .app_settings import settings

LOCALHOST_URL = "http://localhost:5000"
TILED_SERVER_SETTINGS_KEY = "tiled_server"


class TiledServerDialog(QDialog):
    """User chooses which tiled server from a few options."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent

        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        self.setModal(True)
        self.other_button.toggled.connect(self.enableOther)

    def enableOther(self):
        self.other_url.setEnabled(self.other_button.isChecked())

    # static method to create the dialog and return selected server URL
    # ref: https://stackoverflow.com/questions/18196799
    # How can I show a PyQt modal dialog and get data
    # out of its controls once it's closed?
    @staticmethod
    def getServer(parent):
        dialog = TiledServerDialog(parent)
        server = settings.getKey(TILED_SERVER_SETTINGS_KEY) or ""
        if server != "":
            dialog.url_button.setText(server)
            dialog.url_button.setChecked(True)
        else:
            dialog.url_button.setEnabled(False)
            dialog.localhost_button.setChecked(True)

        choices = {
            dialog.localhost_button: LOCALHOST_URL,
            dialog.url_button: server,
        }

        parent.setStatus("Choose which tiled server to use ...")
        ok_selected = dialog.exec()

        selected = None
        if not ok_selected:
            return
        for button, server in choices.items():
            if button.isChecked():
                selected = server
                break
        if selected is None and dialog.other_button.isChecked():
            selected = dialog.other_url.text()

        # check the value before accepting it
        url = QUrl(selected)
        # print(f"{url=} {url.isValid()=} {url.isRelative()=}")
        if url.isValid() and not url.isRelative():
            settings.setKey(TILED_SERVER_SETTINGS_KEY, selected)
        else:
            return

        return selected
