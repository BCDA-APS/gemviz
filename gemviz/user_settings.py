"""
Interface to support user-specific application settings.

Use this for remembering:

* window positions and geometry
* user preferences


The name of the settings file is given in the main window.
Note, the settings file may have the suffix ".ini" on some operating systems.
Remove the settings file to clear any settings.
There is also a menu item to clear this file and reset it to defaults.

This module uses QtCore.QSettings.
(https://doc.qt.io/qtforpython-5/PySide2/QtCore/QSettings.html#qsettings)

..  note:: Multi-monitor support : method restoreWindowGeometry()

    On multi-monitor systems such as laptops, window may be
    restored to offscreen position.  Here is how it happens:

    * geo was saved while window was on 2nd screen while docked
    * now re-opened on laptop display and window is off-screen

    For now, keep the windows on the main screen
    or learn how to edit the settings file.

.. see:: https://github.com/prjemian/assign_gup/blob/master/src/Assign_GUP/settings.py

.. autosummary::

    ~ApplicationQSettings
    ~settings
"""

import datetime
import logging

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import __package_name__
from . import __settings_orgName__

GLOBAL_GROUP = "___global___"
logger = logging.getLogger(__name__)


class ApplicationQSettings(QtCore.QSettings):
    """
    Manage and preserve settings for this application using QSettings.

    Use the .ini file format and save under user directory.

    .. autosummary::

        ~to_dict
        ~init_global_keys
        ~_keySplit_
        ~keyExists
        ~getKey
        ~setKey
        ~resetDefaults
        ~updateTimeStamp
        ~saveWindowGeometry
        ~restoreWindowGeometry
        ~saveSplitter
        ~restoreSplitter
    """

    def __init__(self, orgName, appName):
        QtCore.QSettings.__init__(
            self,
            QtCore.QSettings.IniFormat,
            QtCore.QSettings.UserScope,
            orgName,
            appName,
        )
        self.init_global_keys()

    def __repr__(self):
        keys = "fileName applicationName organizationName status".split()
        d = {k: getattr(self, k)() for k in keys}
        d.update(self.to_dict())
        dl = ", ".join([f"{k}={v!r}" for k, v in d.items()])
        return f"{self.__class__.__name__}({dl})"

    def to_dict(self):
        """Return a dict with all the settings."""
        return {k: self.getKey(k) for k in self.allKeys()}

    def init_global_keys(self):
        logger.debug("fileName=%s", self.fileName)
        d = dict(
            this_file=self.fileName(),  # the .ini file, that is
            version=1.0,  #
            timestamp=str(datetime.datetime.now()),
        )
        for k, v in d.items():
            key = f"{GLOBAL_GROUP}/{k}"
            if self.getKey(key) in ("", None):
                self.setValue(key, v)

    def _keySplit_(self, full_key):
        """
        split full_key into (group, key) tuple

        :param str full_key: either `key` or `group/key`, default group (unspecified) is GLOBAL_GROUP
        """
        if len(full_key) == 0:
            raise KeyError("must supply a key")
        parts = full_key.split("/")
        if len(parts) > 2:
            raise KeyError('too many "/" separators: ' + full_key)
        if len(parts) == 1:
            group, key = GLOBAL_GROUP, str(parts[0])
        elif len(parts) == 2:
            group, key = map(str, parts)
        return group, key

    def keyExists(self, key):
        """does the named key exist?"""
        return key in self.allKeys()

    def getKey(self, key):
        """
        Return the Python object of key or None if not found.
        """
        if "/" not in key and not self.keyExists(key):
            key = f"{GLOBAL_GROUP}/{key}"
        return self.value(key)

    def setKey(self, key, value):
        """
        Set the value of a configuration key, creates the key if it does not exist.

        :param str key: either `key` or `group/key`

        Complement:  self.value(key)  returns value of key
        """
        # ?WHY? if not self.keyExists(key):
        group, k = self._keySplit_(key)
        if group is None:
            group = GLOBAL_GROUP
        self.remove(key)
        self.beginGroup(group)
        self.setValue(k, value)
        self.endGroup()
        if key != "timestamp":
            self.updateTimeStamp()

    def resetDefaults(self):
        """
        Reset all application settings to default values.
        """
        for key in self.allKeys():
            self.remove(key)
        self.init_global_keys()

    def updateTimeStamp(self):
        """ """
        self.setKey("timestamp", str(datetime.datetime.now()))

    def saveWindowGeometry(self, window, label):
        """
        Remember the window's location.

        :param obj window: instance of QWidget
        :param str label: group name to use in settings file
        """
        geo = window.geometry()
        self.setKey(f"{label}/x", geo.x())
        self.setKey(f"{label}/y", geo.y())
        self.setKey(f"{label}/width", geo.width())
        self.setKey(f"{label}/height", geo.height())

    def restoreWindowGeometry(self, window, label):
        """
        Put the window back in place.

        :param obj window: instance of QWidget
        :param str label: group name to use in settings file
        """
        width = self.getKey(f"{label}/width")
        height = self.getKey(f"{label}/height")
        if width is None or height is None:
            return
        window.resize(QtCore.QSize(int(width), int(height)))

        x = self.getKey(f"{label}/x")
        y = self.getKey(f"{label}/y")
        if x is None or y is None:
            return

        # is this window on any available screen?
        qdw = QtWidgets.QDesktopWidget()
        x_onscreen = False
        y_onscreen = False
        for screen_num in range(qdw.screenCount()):
            # find the "available" screen dimensions
            # (excludes docks, menu bars, ...)
            available_rect = qdw.availableGeometry(screen_num)
            if (
                available_rect.x()
                <= int(x)
                < available_rect.x() + available_rect.width()
            ):
                x_onscreen = True
            if (
                available_rect.y()
                <= int(y)
                < available_rect.y() + available_rect.height()
            ):
                y_onscreen = True

        # Move the window to the primary window if it would otherwise be drawn off screen
        available_rect = qdw.availableGeometry(qdw.primaryScreen())
        if not x_onscreen:
            offset = available_rect.x() + available_rect.width() / 10
            x = available_rect.x() + offset
            width = min(int(width), available_rect.width())
        if not y_onscreen:
            offset = available_rect.y() + available_rect.height() / 10
            y = available_rect.y() + offset
            height = min(int(height), available_rect.height())

        window.setGeometry(QtCore.QRect(int(x), int(y), int(width), int(height)))

    def saveSplitter(self, splitter, label):
        """
        remember where the splitter was

        :param obj splitter: instance of QSplitter
        :param str label: group name to use in settings file
        """
        sizes = map(int, splitter.sizes())
        self.setKey(f"{label}/sizes", " ".join(map(str, sizes)))

    def restoreSplitter(self, splitter, label):
        """
        put the splitter back where it was

        :param obj splitter: instance of QSplitter
        :param str label: group name to use in settings file
        """
        sizes = self.getKey(f"{label}/sizes")
        if sizes is not None:
            splitter.setSizes(map(int, str(sizes).split()))


# create _the_ singleton object
settings = ApplicationQSettings(__settings_orgName__, __package_name__)


def main():
    ss = settings
    print(f"{ss=}")

    print(f"{ss.fileName()=}")
    print(f"{ss.applicationName()=}")
    print(f"{ss.organizationName()=}")
    print(f"{ss.status()=}")
    ss.setKey("billy/goat", "gruff")
    for key in ss.allKeys():
        print(f"{key=} {ss.getKey(key)=} {ss._keySplit_(key)=}")
    print(f"{ss.getKey(None)=}")
    ss.resetDefaults()


if __name__ == "__main__":
    main()
