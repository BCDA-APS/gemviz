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
    # ref: https://stackoverflow.com/questions/18196799
    # How can I show a PyQt modal dialog and get data
    # out of its controls once it's closed?
    @staticmethod
    def getServer(parent, default=None):
        dialog = TiledServerDialog(parent)
        if default not in ("localhost", None):
            dialog.url_button.setChecked(True)
        else:
            dialog.localhost_button.setChecked(True)
        dialog.url_button.setText(TILED_SERVER_URL)

        choices = {
            dialog.localhost_button: "http://localhost:5000",
            dialog.url_button: TILED_SERVER_URL,
        }

        parent.status = "Choose which tiled server to use ..."
        result = dialog.exec_()
        # FIXME: Is this truly modal?

        selected = None
        for button, server in choices.items():
            if button.isChecked():
                selected = server

        return selected
