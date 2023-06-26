### I want to inport the information from the test database filter through and find key words and info

from test_infomation_database import test_catalog_2

def test_function():
    return (test_catalog_2)

### Run the "mainwindow.ui" file within the python file
import pathlib
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

# this is not going to change:
def myLoadUi(ui_file, baseinstance=None, **kw):
    """
    function to call for UI file
    """
    return loadUi(ui_file, baseinstance=baseinstance, **kw)





# this is what we customize:
class MyMainWindow(QMainWindow):
    def __init__(self):
        self.max_num_of_entries = 100
        super().__init__()
        #import UI file
        ui_file = pathlib.Path(__file__).parent / "Filter_Window.ui"
        myLoadUi(ui_file, self)
        self.add_catalog_names()
        self.InputBox1.activated.connect(self.show_selected_catalog)
        self.InputBox2.activated.connect(self.show_selected_catalog_scan)



    def add_catalog_names(self):    # write to the pull down menu
        self.tf = test_function()
        print(f"\n{self.tf.keys() = }")
        print(f"{self.InputBox1 = }")
        self.InputBox1.clear()
        self.InputBox1.addItems(self.tf.keys())

    def show_selected_catalog(self, itemnumber):    # read selected value from pull down menu
        #print(f"\n{itemnumber = }") 
        #print(f"{self.InputBox1.currentText() = }") 
        key = self.InputBox1.currentText()  
        #print(f"{self.tf[key] = }") 
        num_entries = len(self.tf[key])
        self.statusbar.showMessage("There are " +str(num_entries) + " entries")

        # ib2 = self.InputBox1.currentText()
        # entries = self.tf[ib2]
        # self.statusbar.showMessage(str(entries))

        if num_entries <= self.max_num_of_entries:
            self.show_selected_catalog_scan_id()
            self.show_selected_catalog_scan_uid()
            self.show_selected_catalog_status()
            self.show_selected_catalog_plan()
        else:
            self.InputBox2.clear()
            self.InputBox3.clear()
            self.InputBox4.clear()
            self.InputBox18.clear()      
    
    def show_selected_catalog_scan(self, itemnumber):
        print(f"\n{itemnumber = }") 
        print(f"{self.InputBox2.currentText() = }") 
        IB2 = self.InputBox2.currentText()
        #print(f"{self.tf[IB2] = }")
        print(f"{IB2}")
        print(f"{type(IB2)= }")
        #IB2_entires = str(self.tf[IB2])
        self.statusbar.showMessage("Scan ID is " + IB2)

    

    def show_selected_catalog_scan_id(self):   
        selected_catalog_key = self.InputBox1.currentText()  
        selected_catalog_value = self.tf[selected_catalog_key]
        scan_id_list=[str(selected_catalog_value[k]['scan_id']) for k in selected_catalog_value.keys()]
        self.InputBox2.clear()
        self.InputBox2.addItems([""] + scan_id_list)

    def show_selected_catalog_scan_uid(self):   
        selected_catalog_key = self.InputBox1.currentText()  
        selected_catalog_value = self.tf[selected_catalog_key]
        scan_uid_list=[str(selected_catalog_value[k]['uid']) for k in selected_catalog_value.keys()]
        self.InputBox3.clear()
        self.InputBox3.addItems([""] + scan_uid_list)

    def show_selected_catalog_status(self):   
        selected_catalog_key = self.InputBox1.currentText()  
        selected_catalog_value = self.tf[selected_catalog_key]
        scan_status_list=[str(selected_catalog_value[k]['status']) for k in selected_catalog_value.keys()]
        self.InputBox18.clear()
        self.InputBox18.addItems([""] + scan_status_list)

    def show_selected_catalog_plan(self):   
        selected_catalog_key = self.InputBox1.currentText()  
        selected_catalog_value = self.tf[selected_catalog_key]
        scan_plan_list=[str(selected_catalog_value[k]['plan']) for k in selected_catalog_value.keys()]
        self.InputBox4.clear()
        self.InputBox4.addItems([""] + scan_plan_list)







# this is not going to change:
def gui():
    """display the main widget"""
    app = QApplication(sys.argv)
    main_window = MyMainWindow()
    #print(f"{main_window.tf = }")
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    gui()