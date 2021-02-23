import pyvisa
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication
import sys
class signal_generator_window(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(signal_generator_window, self).__init__(*args, **kwargs)
        # Load the UI Page
        self.ui = uic.loadUi("UI_SML01.ui", self)
        self.setWindowTitle("LLRF - Soleil - SML01")
        self.btn_fct()

    def btn_fct(self):
        self.button_init.clicked.connect(self.open_dev)
        self.ui_phase.returnPressed.connect(self.change_phase)
        self.ui_amp.returnPressed.connect(self.change_pow)
        self.ui_freq.returnPressed.connect(self.change_freq)

    def open_dev(self):
        rm = pyvisa.ResourceManager()
        rm.list_resources()
        self.inst = rm.open_resource('GPIB0::12::INSTR')
        self.update_msg(self.inst.query("*IDN?"))


    def change_phase(self):
        cmd = self.ui_phase.text()
        str = 'PHASe ' + cmd
        self.inst.write(str)
        self.update_msg(str + 'degree')

    def change_pow(self):
            cmd = self.ui_amp.text()
            str = 'POW ' + cmd + 'dBm'
            self.inst.write(str)
            self.update_msg(str)

    def change_freq(self):
            cmd = self.ui_freq.text()
            str ='FREQ ' + cmd + 'MHz'

            self.inst.write(str)
            self.update_msg(str)

    def update_msg(self, msg):
        self.msgbox.clear()
        self.msgbox.setText(msg)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = signal_generator_window()
    myWin.show()
    sys.exit(app.exec_())