from ConnectServer import ConnectServer
from PyQt5.QtWidgets import QMainWindow, QApplication

import matplotlib as plt
from Plotter import CustomWidget
from PyQt5 import QtWidgets, uic
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt
import pyqtgraph as pg
import sys
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import struct
import numpy as np
import math

from xlutils.copy import copy
import xlrd
from ctypes import *
import ctypes
t = 0  # write/read config from line 0

class llrf_graph_window(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(llrf_graph_window, self).__init__(*args, **kwargs)
        # Load the UI Page
        self.plot_time = 1000
        self.ui = uic.loadUi("UI_llrf_Soleil.ui", self)
        self.setWindowTitle("LLRF - Soleil - expert")
        self.user_mode()
        self.set_plot_ui()
        self.btn_fct()
        self.update_time_date()
        # timer for plot
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.plot_time)
        self.load_config()
        self.phase_set = CDLL('./phase_set.so')
        self.phase_set.argtypes = ctypes.c_double

    def read_mapping(self):
        file = self.excel_path.text()
        wb = xlrd.open_workbook(filename=file)
        # print(wb.sheet_names())
        sheet1 = wb.sheet_by_index(0)
        self.cell = sheet1.col_values(0)
        self.base_name = sheet1.col_values(2)
        self.offset_addr = sheet1.col_values(3)
        self.size = sheet1.col_values(4)
        self.high_addr = sheet1.col_values(5)

        print(self.cell)
        print(self.base_name)
        print(self.offset_addr)

        '''
        Number of BRAM data bloc
        '''
        self.nbr_bram = self.base_name.count('Mem0')
        self.ui_nbr_bram.setText(str(self.nbr_bram))

        '''
        BRAM data start address and one bloc size
        '''
        try:
            row_bram0_addr = self.cell.index('BRAM_MGT/axi_bram_ctrl_0')
        except ValueError:
            row_bram0_addr = self.cell.index('/BRAM_MGT/axi_bram_ctrl_0')
        # print(row_bram0_addr)
        self.bram0_addr = self.offset_addr[row_bram0_addr]
        #print(self.bram0_addr)
        self.bram0_size = self.size[row_bram0_addr]
        #print(self.bram0_size)
        if self.bram0_size == '16K':
            self.bram0_size = 16 * 1024
        if self.bram0_size == '8K':
            self.bram0_size = 8 * 1024
        if self.bram0_size == '4K':
            self.bram0_size = 4 * 1024
        if self.bram0_size == '2K':
            self.bram0_size = 2 * 1024
        if self.bram0_size == '1K':
            self.bram0_size = 1024

        self.ui_bram0_size.setText(str(self.bram0_size))
        '''
            BRAM data start address
        '''
        self.bram0_addr = self.bram0_addr.replace('_', '')
        self.bram0_addr = int(self.bram0_addr, 16)
        # print(self.bram0_addr)

        '''
        BRAM map start address
        '''
        #print('start addr:')
        #print(self.offset_addr)
        start_addr_list = self.format_str(self.offset_addr)
        #print(start_addr_list)
        self.bram_map_start = min(start_addr_list)
        #print('Map start address')
        #print(hex(self.bram_map_start))

        self.ui_bram0_addr.setText(str(hex(self.bram_map_start)))
        '''
         BRAM map end address
        '''
        high_addr_list = self.format_str(self.high_addr)
        self.bram_map_end = max(high_addr_list)
        # print(self.bram_map_end)

        '''
        MAP length
        '''
        self.bram0_maplen = self.bram_map_end - self.bram_map_start + 0x0000F000  # + value F000
        #print(self.bram0_maplen)
        self.ui_bram0_maplen.setText(str(hex(self.bram0_maplen)))

        '''
        BRAM data offset
        '''
        self.bram0_offset = self.bram0_addr - self.bram_map_start
        self.ui_bram0_offset.setText(str(hex(self.bram0_offset)))

        '''
        Trigger offset refer to map start
        '''
        index_trig_addr = self.base_name.index('reg0')
        self.trig_addr = self.offset_addr[index_trig_addr]
        self.trig_addr = int(self.trig_addr.replace('_', ''), 16)
        '''
        trigger offset = trigger address - map start address
        '''
        self.ui_trig_addr.setText(str(hex(self.trig_addr - self.bram_map_start)))


        '''
        print(sheet1.cell(1, 0).value)
        print(sheet1.cell_value(1, 0))
        print(sheet1.row(1)[0].value)
        '''
    def save_config(self):
        file = self.excel_path.text()
        wb = xlrd.open_workbook(filename=file)
        new_wb = copy(wb)
        sheet1 = new_wb.get_sheet(1)

        sheet1.write(t, 0, self.server_ip.text())
        sheet1.write(t, 1, self.server_port.text())
        sheet1.write(t, 2, self.ui_ph0_deg.text())
        sheet1.write(t, 3, self.ui_ph0_add.text())
        sheet1.write(t, 4, self.ui_ph1_deg.text())
        sheet1.write(t, 5, self.ui_ph1_add.text())
        sheet1.write(t, 6, self.ui_ph2_deg.text())
        sheet1.write(t, 7, self.ui_ph2_add.text())
        sheet1.write(t, 8, self.ui_ph3_deg.text())
        sheet1.write(t, 9, self.ui_ph3_add.text())
        sheet1.write(t, 10, self.excel_path.text())
        new_wb.save(file)
        print('Configuration saved!!!')
    def load_config(self):
        file = self.excel_path.text()
        wb = xlrd.open_workbook(filename=file)
        try:
            sheet1 = wb.sheet_by_index(1)
            self.server_ip.setText(sheet1.cell_value(t, 0))
            self.server_port.setText(sheet1.cell_value(t, 1))
            self.ui_ph0_deg.setText(sheet1.cell_value(t, 2))
            self.ui_ph0_add.setText(sheet1.cell_value(t, 3))
            self.ui_ph1_deg.setText(sheet1.cell_value(t, 4))
            self.ui_ph1_add.setText(sheet1.cell_value(t, 5))
            self.ui_ph2_deg.setText(sheet1.cell_value(t, 6))
            self.ui_ph2_add.setText(sheet1.cell_value(t, 7))
            self.ui_ph3_deg.setText(sheet1.cell_value(t, 8))
            self.ui_ph3_add.setText(sheet1.cell_value(t, 9))
            self.excel_path.setText(sheet1.cell_value(t, 10))

        except IndexError:
            new_wb = copy(wb)
            sheet1 = new_wb.add_sheet('config')

            sheet1.write(t, 0, self.server_ip.text())
            sheet1.write(t, 1, self.server_port.text())
            sheet1.write(t, 2, self.ui_ph0_deg.text())
            sheet1.write(t, 3, self.ui_ph0_add.text())
            sheet1.write(t, 4, self.ui_ph1_deg.text())
            sheet1.write(t, 5, self.ui_ph1_add.text())
            sheet1.write(t, 6, self.ui_ph2_deg.text())
            sheet1.write(t, 7, self.ui_ph2_add.text())
            sheet1.write(t, 8, self.ui_ph3_deg.text())
            sheet1.write(t, 9, self.ui_ph3_add.text())
            sheet1.write(t, 10, self.excel_path.text())

            new_wb.save(file)
            print('first start')

        self.last_ch0_ph = self.ui_ph0_deg.text()
        self.last_ch1_ph = self.ui_ph1_deg.text()
        self.last_ch2_ph = self.ui_ph2_deg.text()
        self.last_ch3_ph = self.ui_ph3_deg.text()

    def format_str(self, str):
        i = 0
        index_addr = str.count('') + 1
        #print('nbr:')
        #print(len(str))
        tt = ["" for x in range(len(str)-index_addr)]
        for t in str[index_addr:]:
            rm_ = t.replace('_', '')
            #print(rm_)
            tt[i] = int(rm_, 16)  # hex to dec
            i = i + 1
        return tt
    def update_time_date(self):
        self.time_date = QtCore.QTimer()
        self.time_date.setInterval(1000)
        self.time_date.timeout.connect(self.disp_time_date)
        self.time_date.start()

    def disp_time_date(self):
        td = QDateTime.currentDateTime()
        self.current_dt.setText(td.toString())

    def btn_fct(self):
        self.button_init.clicked.connect(self.connect_server)
        self.button_stop.clicked.connect(self.stop_connect)
        self.button_start.clicked.connect(self.start_acq)
        self.button_set_bram.clicked.connect(self.read_mapping)
        # self.button_phase.clicked.connect(self.set_phase)
        self.button_save_config.clicked.connect(self.save_config)

    def calc_phase_angle(self, ch):

        if ch == 0:
            phase = self.ui_ph0_deg.text()
            addr = self.ui_ph0_add.text()
        elif ch == 1:
            phase = self.ui_ph1_deg.text()
            addr = self.ui_ph1_add.text()
        elif ch == 2:
            phase = self.ui_ph2_deg.text()
            addr = self.ui_ph2_add.text()
        elif ch == 3:
            phase = self.ui_ph3_deg.text()
            addr = self.ui_ph3_add.text()

        ph = int(phase)
        self.mysocket.send(b"2")
        ph = c_double(ph)
        phase_angle = self.phase_set.IQ_phase_shift(ph)
        #print(hex(np.uint32(phase_angle)))
        msg = str(np.uint32(phase_angle)) + ',' + addr
        self.mysocket.send(msg.encode())
        # print('Update channel' + str(ch) + 'phase offset')
        self.update_msg('Now, you are right, the phase updated!!')



    def user_mode(self):
        '''
        self.bram0_addr.hide()
        self.bram0_offset.hide()
        self.bram0_num_data.hide()
        self.offset_trig.hide()
        self.button_trig.hide()
        self.bram0_len.hide()
        self.bram0_maplen.hide()
        self.bram0_start_addr.hide()
        self.trig_addr.hide()
        self.data_offset.hide()
        '''
        self.button_phase.hide()
        self.button_init.hide()
        self.button_start.hide()
        self.button_stop.hide()
        self.button_expert.hide()
    def polar_plot(self,plot):
        # Add polar grid lines
        for r in range(-self.max_range, 1, self.max_range):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            plot.addItem(circle)
    def set_plot_ui(self):
        self.max_range = 32000
        self.plt_data = self.rtplot.addPlot(
            labels={'left': 'Level', 'bottom': 'data points'})  # change here for plt_i in seperated plot
        self.plt_ch0= self.plt_ch0_iq.addPlot()
        self.plt_ch0.setXRange(-self.max_range, self.max_range, padding=0)
        self.plt_ch0.setYRange(-self.max_range, self.max_range, padding=0)

        self.plt_ch1= self.plt_ch1_iq.addPlot()
        self.plt_ch1.setXRange(-self.max_range, self.max_range, padding=0)
        self.plt_ch1.setYRange(-self.max_range, self.max_range, padding=0)

        self.plt_ch2= self.plt_ch2_iq.addPlot()
        self.plt_ch2.setXRange(-self.max_range, self.max_range, padding=0)
        self.plt_ch2.setYRange(-self.max_range, self.max_range, padding=0)

        self.plt_ch3= self.plt_ch3_iq.addPlot()
        self.plt_ch3.setXRange(-self.max_range, self.max_range, padding=0)
        self.plt_ch3.setYRange(-self.max_range, self.max_range, padding=0)

        self.bram0.setChecked(1)
        self.bram1.setChecked(1)
        self.bram2.setChecked(1)
        self.bram3.setChecked(1)


    def first_plot(self):
        line_w = 2
        sympole_s = 5
    #################################
        self.curve_q = self.plt_data.plot(self.buf_q[0], pen='g')
        pen = pg.mkPen(color='g', width=line_w, style=QtCore.Qt.DashLine)
        self.curve_i = self.plt_data.plot(self.buf_i[0], pen=pen)

        n = min(len(self.buf_q[0]), len(self.buf_i[0]))
        self.ch0_scatter = self.plt_ch0.plot(self.buf_i[0][0:n], self.buf_q[0][0:n], pen=None, symbol='o',symbolPen = 'g')
        self.ch0_scatter.setSymbolSize(sympole_s)
        self.polar_plot(self.plt_ch0)

    ######################
        self.curve_q1 = self.plt_data.plot(self.buf_q[1], pen='b')
        pen = pg.mkPen(color='b', width=line_w, style=QtCore.Qt.DashLine)
        self.curve_i1 = self.plt_data.plot(self.buf_i[1], pen=pen)


        n = min(len(self.buf_q[1]), len(self.buf_i[1]))
        self.ch1_scatter = self.plt_ch1.plot(self.buf_i[1][0:n], self.buf_q[1][0:n], pen=None, symbol='o', symbolPen = 'b')
        self.ch1_scatter.setSymbolSize(sympole_s)
        self.polar_plot(self.plt_ch1)

    #######################
        self.curve_q2 = self.plt_data.plot(self.buf_q[2], pen='r')
        pen = pg.mkPen(color='r', width=line_w, style=QtCore.Qt.DashLine)
        self.curve_i2 = self.plt_data.plot(self.buf_i[2], pen=pen)

        n = min(len(self.buf_q[2]), len(self.buf_i[2]))
        self.ch2_scatter = self.plt_ch2.plot(self.buf_i[2][0:n], self.buf_q[2][0:n], pen=None, symbol='o',symbolPen = 'r')
        self.ch2_scatter.setSymbolSize(sympole_s)
        self.polar_plot(self.plt_ch2)
    ######################################
        pen = pg.mkPen(color='y', width=line_w, style=QtCore.Qt.DashLine)
        self.curve_q3 = self.plt_data.plot(self.buf_q[3], pen='y')
        self.curve_i3 = self.plt_data.plot(self.buf_i[3], pen=pen)

        n = min(len(self.buf_q[3]), len(self.buf_i[3]))
        self.ch3_scatter = self.plt_ch3.plot(self.buf_i[3][0:n], self.buf_q[3][0:n], pen=None, symbol='o', symbolPen = 'y')
        self.ch3_scatter.setSymbolSize(sympole_s)
        self.polar_plot(self.plt_ch3)
        '''
        try:
            self.ui_ph0_deg.returnPressed.connect(self.check_val(0))
            self.ui_ph1_deg.returnPressed.connect(self.check_val(1))
            self.ui_ph2_deg.returnPressed.connect(self.check_val(2))
            self.ui_ph3_deg.returnPressed.connect(self.check_val(3))
        except TypeError:
            pass
        '''
    def check_val(self):
        if (self.last_ch0_ph != self.ui_ph0_deg.text()) & (self.ui_ph0_deg.text()!=''):
            self.calc_phase_angle(0)
            self.last_ch0_ph = self.ui_ph0_deg.text()

        if (self.last_ch1_ph != self.ui_ph1_deg.text()) & (self.ui_ph1_deg.text()!=''):
            self.calc_phase_angle(1)
            self.last_ch1_ph = self.ui_ph1_deg.text()

        if (self.last_ch2_ph != self.ui_ph2_deg.text()) & (self.ui_ph2_deg.text()!=''):
            self.calc_phase_angle(2)
            self.last_ch2_ph = self.ui_ph2_deg.text()

        if (self.last_ch3_ph != self.ui_ph3_deg.text()) & (self.ui_ph3_deg.text()!=''):
            self.calc_phase_angle(3)
            self.last_ch3_ph = self.ui_ph3_deg.text()

    def update_refresh_time(self):
        try:
            t =int(self.refresh_time.text())
            if (t & t > 0):
                self.timer.setInterval(t)
        except ValueError:
                pass

        if (t & t > 0):
            self.timer.setInterval(t)

    def update_plot(self):
        self.timer.timeout.connect(self.get_data)
        self.timer.timeout.connect(self.update_graph)
        self.timer.timeout.connect(self.check_val)
        self.timer.timeout.connect(self.update_refresh_time)
        self.timer.start()
    def start_acq(self):
        for i in range(4):
            self.calc_phase_angle(i)
            time.sleep(0.1)
        self.get_data()
        self.first_plot()
        self.update_plot()
        self.update_msg('Data acquisition started!!')

    def connect_server(self):
        # create obj of connectserver
        try:
            obj_con_server = ConnectServer(self.server_ip.text(), int(self.server_port.text()))

        # create socket connect without bram
            self.mysocket = obj_con_server.__create__()
            # connect to bram
            obj_con_server.connect_bram(self.ui_bram0_addr.text(), self.ui_bram0_offset.text(), self.ui_bram0_maplen.text(),
                                        self.ui_trig_addr.text(), self.ui_nbr_bram.text(), self.ui_bram0_size.text())

            self.update_msg('BRAVO!!! \n' + 'Now, you can start the acquisition.')
        except ConnectionRefusedError:
            self.update_msg('First, you must start the server !!!')

    def get_data(self):
        self.mysocket.send(b"1")
        self.tmp_bram = [None] * 8
        i = 0
        while 1:
            msgServeur = self.mysocket.recv(4096)
            '''
            print("data from server:")
            print(msgServeur)
            print('length of msg from server:')
            print(len(msgServeur))
            '''
            if msgServeur == b'data_ok':
                break
            else:
                format_str = "h" * (int(len(msgServeur)) // 2)
                try:
                    #print(msgServeur)
                    self.tmp_bram[i] = struct.unpack(format_str, msgServeur)
                except IndexError:
                    continue
                i = i + 1
        # processing brams
        # ##########################
        # bram data
        j = 0
        k = 0
        bram_data = [None] * self.nbr_bram
        self.buf_q = [None] * self.nbr_bram
        self.buf_i = [None] * self.nbr_bram

        while j < self.nbr_bram:  # number of bram data bloc
            if self.tmp_bram[k] == 'None':
                pass
            else:
                try:
                    bram_data[j] = self.tmp_bram[k] + self.tmp_bram[k + 1]
                except TypeError:
                    print('type errer')

                self.buf_q[j] = bram_data[j][0::2]
                self.buf_i[j] = bram_data[j][1::2]
                self.bram0_num_data.setText(str(len(self.buf_q[j])))
                '''
                print('q data')
                print(self.buf_q[j])
                print('data length')
                print(len(self.buf_q[j]))
                print('i data')
                print(self.buf_i[j])
                '''
                k = k + 2
                j = j + 1

    def stop_connect(self):
        self.mysocket.send(b'0')
        self.update_msg("Stopped!! Click 'init. connect ' to connect to the server!!!")
        self.timer.stop()
        self.clear_plot()


    def update_graph(self):
        self.clear_plot()
        if self.bram0.isChecked():
            self.curve_q.setData(self.buf_q[0])
            self.curve_i.setData(self.buf_i[0])
            self.curve_q.setPos(len(self.buf_q[0]), 0)
            self.curve_i.setPos(len(self.buf_i[0]), 0)

            n = min(len(self.buf_q[0]), len(self.buf_i[0]))
            #self.plt_ch0.plot(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.ch0_scatter.setData(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.I_moy0 = np.mean(self.buf_i[0])
            self.Q_moy0 = np.mean(self.buf_q[0])
            amp = math.sqrt(np.square(self.I_moy0)+np.square(self.Q_moy0))
            try:
                phi = math.atan(self.Q_moy0/self.I_moy0)
                phi = math.degrees(phi)
            except RuntimeWarning:
                print('No')
            self.ui_ch0_amp.setText(str(round(amp,2)))
            self.ui_ch0_phi.setText(str(round(phi,4)))

        if self.bram1.isChecked():
            self.curve_q1.setData(self.buf_q[1])
            self.curve_i1.setData(self.buf_i[1])
            self.curve_q1.setPos(len(self.buf_q[1]), 0)
            self.curve_i1.setPos(len(self.buf_i[1]), 0)


            n = min(len(self.buf_q[1]), len(self.buf_i[1]))
            #self.plt_ch0.plot(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.ch1_scatter.setData(self.buf_i[1][0:n], self.buf_q[1][0:n])
            self.I_moy1 = np.mean(self.buf_i[1])
            self.Q_moy1 = np.mean(self.buf_q[1])

        if self.bram2.isChecked():
            self.curve_q2.setData(self.buf_q[2])
            self.curve_i2.setData(self.buf_i[2])
            self.curve_q2.setPos(len(self.buf_q[2]), 0)
            self.curve_i2.setPos(len(self.buf_i[2]), 0)

            n = min(len(self.buf_q[2]), len(self.buf_i[2]))
            #self.plt_ch0.plot(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.ch2_scatter.setData(self.buf_i[2][0:n], self.buf_q[2][0:n])
            self.I_moy2 = np.mean(self.buf_i[2])
            self.Q_moy2 = np.mean(self.buf_q[2])

        if self.bram3.isChecked():
            self.curve_q3.setData(self.buf_q[3])
            self.curve_i3.setData(self.buf_i[3])
            self.curve_q3.setPos(len(self.buf_q[3]), 0)
            self.curve_i3.setPos(len(self.buf_i[3]), 0)


            n = min(len(self.buf_q[3]), len(self.buf_i[3]))
            #self.plt_ch0.plot(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.ch3_scatter.setData(self.buf_i[3][0:n], self.buf_q[3][0:n])
            self.I_moy3 = np.mean(self.buf_i[3])
            self.Q_moy3 = np.mean(self.buf_q[3])


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
