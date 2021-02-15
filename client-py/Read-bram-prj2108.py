from ConnectServer import ConnectServer
from PyQt5.QtWidgets import QMainWindow, QApplication

from Plotter import CustomWidget
from PyQt5 import QtWidgets, uic
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt
import pyqtgraph as pg
import sys
import time
import struct

class llrf_graph_window(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(llrf_graph_window, self).__init__(*args, **kwargs)
        # Load the UI Page
        self.plot_time = 100 # ms

        self.ui = uic.loadUi("llrfDemo_2018.ui", self)
        self.setWindowTitle("LLRF - Soleil - expert")
        self.user_mode()
        self.set_plot_ui()
        self.btn_fct()
        self.update_time_date()
        # timer for plot
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.plot_time)

    def update_time_date(self):
        self.time_date = QtCore.QTimer()
        self.time_date.setInterval(2000)
        self.time_date.timeout.connect(self.disp_time_date)
        self.time_date.start()

    def disp_time_date(self):
        td = QDateTime.currentDateTime()
        self.current_dt.setText(td.toString())

    def btn_fct(self):
        self.button_plot.clicked.connect(self.update_graph)
        self.button_init.clicked.connect(self.connect_server)
        self.button_stop.clicked.connect(self.stop_connect)
        self.button_start.clicked.connect(self.start_draw)
        self.button_trig.clicked.connect(self.trig1_data) # server 6
        #self.button_plot.clicked.connect(self.single_plot)

    def user_mode(self):
        '''
        self.bram0_addr.hide()
        self.bram0_offset.hide()
        self.bram0_num_data.hide()
        self.offset_trig.hide()
        self.button_trig.hide()
        self.button_plot.hide()
        self.bram0_len.hide()
        self.bram0_maplen.hide()
        self.bram0_start_addr.hide()
        self.trig_addr.hide()
        self.data_offset.hide()
        '''
        self.button_expert.hide()
    def set_plot_ui(self):
        self.plt_data = self.rtplot.addPlot(
            labels={'left': 'Voltage', 'bottom': 'Bram size'})  # change here for plt_i in seperated plot
        self.bram0.setChecked(1)
        self.bram1.setChecked(1)
        self.bram2.setChecked(0)
        self.bram3.setChecked(0)

    def new_win_plot(self):
        # create a seperated window
        self.rtploter = CustomWidget()
        self.rtploter.addPlot(labels={'left': 'Voltage', 'bottom': 'Time'})

    def first_drew(self):
        line_w = 2
        #################################
        if (self.bram0.isChecked()):
            self.curve_q = self.plt_data.plot(self.buf_q[0], pen='g')
            pen = pg.mkPen(color='g', width=line_w, style=QtCore.Qt.DashLine)
            self.curve_i = self.plt_data.plot(self.buf_i[0], pen=pen)
        else:
            self.clear_plot()
        ###################################
        if (self.bram1.isChecked()):
            self.curve_q1 = self.plt_data.plot(self.buf_q[1], pen='b')
            pen = pg.mkPen(color='b', width=line_w, style=QtCore.Qt.DashLine)
            self.curve_i1 = self.plt_data.plot(self.buf_i[1], pen=pen)
        else:
            self.clear_plot()
        ######################################
        if self.bram2.isChecked():
            self.curve_q2 = self.plt_data.plot(self.buf_q[2], pen='r')
            pen = pg.mkPen(color='r', width=line_w, style=QtCore.Qt.DashLine)
            self.curve_i2 = self.plt_data.plot(self.buf_i[2], pen=pen)
        else:
            self.clear_plot()
        ######################################
        if self.bram3.isChecked():
            pen = pg.mkPen(color='y', width=line_w, style=QtCore.Qt.DashLine)
            self.curve_q3 = self.plt_data.plot(self.buf_q[3], pen='y')
            self.curve_i3 = self.plt_data.plot(self.buf_i[3], pen=pen)
        else:
            self.clear_plot()

    def start_timer(self):

        self.timer.timeout.connect(self.get_data)
        self.timer.timeout.connect(self.update_graph)
        self.timer.start()

    def connect_server(self):
        # create obj of connectserver
        obj_con_server = ConnectServer(self.server_ip.text(), int(self.server_port.text()))
        # create socket connect without bram
        self.mysocket = obj_con_server.__create__()
        # connect to bram
        obj_con_server.connect_bram(self.bram0_addr.text(), self.bram0_offset.text(), self.bram0_maplen.text(), self.trig_addr.text(), self.nbr_bram.text(), self.bram0_size.text())

        self.update_msg('Got it! \n' + 'Please select which bram you want to plot')

    def get_data(self):
        self.mysocket.send(b"1")
        self.tmp_bram = [None]*8
        i = 0
        while 1:
            msgServeur = self.mysocket.recv(4096)

            print("data from server:")
            print(msgServeur)
            print('length of msg from server:')
            print(len(msgServeur))

            if msgServeur == b'data_ok':
                break
            else:
                format_str = "h" * (int(len(msgServeur))//2)
                try:
                    print(msgServeur)
                    self.tmp_bram[i] = struct.unpack(format_str, msgServeur)
                except IndexError:
                    continue
                i = i + 1
        # processing 2 brams
        # ##########################
        # 2 bram data
        j=0
        k=0
        bram_data = [None]*4
        self.buf_q = [None]*4
        self.buf_i = [None]*4

        while j<2: # here, for 2 bram, j < 4 for 4 bram
            if self.tmp_bram[k] == 'None':
                pass
            else:
                try:
                    bram_data[j] = self.tmp_bram[k]+self.tmp_bram[k+1]
                except TypeError:
                    print('type errer')

                self.buf_q[j] = bram_data[j][0::2]
                self.buf_i[j] = bram_data[j][1::2]
                self.bram0_num_data.setText(str(len(self.buf_q[j])))

                print('q data')
                print(self.buf_q[j])
                print('data length')
                print(len(self.buf_q[j]))
                print('i data')
                print(self.buf_i[j])

                k = k + 2
                j = j + 1

    def stop_connect(self):
        self.mysocket.send(b"0")
        self.update_msg("Click 'init' to connect to the server!!!")
        self.timer.stop()
        self.clear_plot()

    def update_graph(self):
        self.clear_plot()
        if self.bram0.isChecked():
            self.curve_q.setData(self.buf_q[0])
            self.curve_i.setData(self.buf_i[0])
            self.curve_q.setPos(len(self.buf_q[0]), 0)
            self.curve_i.setPos(len(self.buf_i[0]), 0)

        if self.bram1.isChecked():
            self.curve_q1.setData(self.buf_q[1])
            self.curve_i1.setData(self.buf_i[1])
            self.curve_q1.setPos(len(self.buf_q[1]), 0)
            self.curve_i1.setPos(len(self.buf_i[1]), 0)

        if self.bram2.isChecked():
            self.curve_q2.setData(self.buf_q[2])
            self.curve_i2.setData(self.buf_i[2])
            self.curve_q2.setPos(len(self.buf_q[2]), 0)
            self.curve_i2.setPos(len(self.buf_i[2]), 0)

        if self.bram3.isChecked():
            self.curve_q3.setData(self.buf_q[3])
            self.curve_i3.setData(self.buf_i[3])
            self.curve_q3.setPos(len(self.buf_q[3]), 0)
            self.curve_i3.setPos(len(self.buf_i[3]), 0)

    def start_draw(self):
        self.get_data()
        self.first_drew()
        self.start_timer()

    def trig1_data(self):
        self.get_data()
        self.first_drew()

    def clear_plot(self):
        try:
            self.curve_q.clear()
            self.curve_i.clear()
        except AttributeError:
            pass
        try:
            self.curve_q1.clear()
            self.curve_i1.clear()
        except AttributeError:
            pass
        try:
            self.curve_q2.clear()
            self.curve_i2.clear()
        except AttributeError:
            pass
        try:
            self.curve_q3.clear()
            self.curve_i3.clear()
        except AttributeError:
            pass

    def update_msg(self, msg):
        self.msgbox.clear()
        self.msgbox.setText(msg)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = llrf_graph_window()
    myWin.show()
    sys.exit(app.exec_())