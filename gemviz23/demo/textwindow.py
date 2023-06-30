# Copyright (c) 2009 - 2016, UChicago Argonne, LLC.
# See LICENSE file for details.

"""
show text in a GUI window
"""

from PyQt5.QtWidgets import QWidget

import utils

UI_FILE = "textwindow.ui"


class TextWindow(QWidget):
    """
    show text in a GUI window that remembers its geometry, based on supplied window title

    :param obj parent: instance of QWidget
    :param str title: to be used as the window title (and settings group name)
    :param str text: window content
    # :param obj settings: instance of settings.ApplicationQSettings
    """

    def __init__(self, parent=None, title="window title", text="", settings=None):
        self.settings = settings
        super().__init__(parent)
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setup(text, title)

    def setup(self, text, title):
        self.setText(text)
        self.setTitle(title)
        # if self.settings is not None:
        #     self.restoreWindowGeometry()

    # def settingsGroupName(self):
    #     """
    #     need a group name in the settings file to save the window geometry, based on window title
    #     """
    #     group = str(self.windowTitle()).strip()
    #     # group = group.lstrip('email: ')
    #     pattern_list = [" ", ":", ";", "(", ")", "[", "]", ".", ",", "'", '"']
    #     for pattern in pattern_list:
    #         group = group.replace(pattern, "_")
    #     return group + "_geometry"

    def setText(self, text):
        """ """
        self.plainTextEdit.setPlainText(text)

    def setTitle(self, title):
        """ """
        self.setWindowTitle(title)

    # def closeEvent(self, event):
    #     """ """
    #     self.saveWindowGeometry()
    #     event.accept()
    #     self.close()

    # def moveEvent(self, event):
    #     """ """
    #     self.saveWindowGeometry()
    #     event.accept()  # TODO: should we?

    # def saveWindowGeometry(self):
    #     """
    #     remember where the window was
    #     """
    #     if self.settings is not None:
    #         group = self.settingsGroupName()
    #         self.settings.saveWindowGeometry(self, group)

    # def restoreWindowGeometry(self):
    #     """
    #     put the window back where it was
    #     """
    #     if self.settings is not None:
    #         group = self.settingsGroupName()
    #         self.settings.restoreWindowGeometry(self, group)
