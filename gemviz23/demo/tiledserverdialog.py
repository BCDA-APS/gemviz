from PyQt5.QtWidgets import QDialog

import utils

UI_FILE = utils.getUiFileName(__file__)
TILED_SERVER_URL = "http://otz.xray.aps.anl.gov:5000"  # TODO: use settings file


class TiledServerDialog(QDialog):
    """User chooses which tiled server from a few options."""

    def __init__(self, mainwindow):
        self.mainwindow = mainwindow

        super().__init__(mainwindow)
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup()
        self.setModal(True)

    def setup(self):
        pass

    # static method to create the dialog and return selected server URL
    @staticmethod
    def getServer(parent, default=None):
        choices = {
            dialog.localhost_button : "http://localhost:5000",
            dialog.url_button : TILED_SERVER_URL,
        }

        dialog = TiledServerDialog(parent)
        dialog.localhost_button.setChecked(True)  # TODO: consider default param
        dialog.url_button.setText(TILED_SERVER_URL)

        parent.status = "Choose which tiled server to use ..."
        result = dialog.exec_()

        parent.status = f"{(result == QDialog.Accepted)=}"
        selected = None
        for button, server in choices.items():
            if button.isChecked():
                selected = server

        return selected


