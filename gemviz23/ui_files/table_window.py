'''
This is just 'table_windown.ui' file written in python code.
This is not relevant to the use of the GUI as we will be using python to run the ui file
This was just exercise for Olliver (GEM 2023) to work on code
Hope this file help others to understand the code of the GUI and learn more
'''
import typing
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *  
from PyQt5.QtGui import *
import sys


from PyQt5.QtWidgets import QWidget


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(469, 346)
        self.tableView = QTableView(Form)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setGeometry(QRect(20, 20, 431, 301))
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setEnabled(True)
        self.frame.setGeometry(QRect(10, 10, 451, 321))
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setLineWidth(2)
        self.frame.setMidLineWidth(5)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
    # retranslateUi

