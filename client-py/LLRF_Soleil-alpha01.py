from ConnectServer import ConnectServer
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets, uic
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import QDateTime, Qt
import pyqtgraph as pg
import sys
import time
import struct
import numpy as np
import math

from xlutils.copy import copy
import xlrd
from ctypes import *
import ctypes
t = 0  # write/read config from line 0
n_bit = 4

file = 'config.xlsx'



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
        self.phase_set = CDLL('phase_set.so')
        self.phase_set.argtypes = ctypes.c_double


    def btnClicked(self):
        self.chile_Win = ChildWindow()
        self.chile_Win.show()
        self.chile_Win.exec_()

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
        wb = xlrd.open_workbook(filename=file)
        new_wb = copy(wb)
        try:
            sheet1 = new_wb.get_sheet(0)
        except IndexError:
            sheet1 = new_wb.add_sheet('set')

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
        self.update_msg('Configuration saved!!!')
    def load_config(self):
        wb = xlrd.open_workbook(filename=file)
        try:
            sheet1 = wb.sheet_by_index(0)
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
            self.ui_mag_amp.setText(sheet1.cell_value(t, 11))

        except IndexError:
            new_wb = copy(wb)
            sheet1 = new_wb.add_sheet('set')
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
            sheet1.write(t, 11, self.ui_mag_amp.text())
            new_wb.save(file)
            self.update_msg('first start')

        self.last_ch0_ph = self.ui_ph0_deg.text()
        self.last_ch1_ph = self.ui_ph1_deg.text()
        self.last_ch2_ph = self.ui_ph2_deg.text()
        self.last_ch3_ph = self.ui_ph3_deg.text()
        self.last_mag_amp = self.ui_mag_amp.text()
        self.last_reg = self.ui_reg_val.text()

        self.ui_ph0_deg.returnPressed.connect(self.check_val)
        self.ui_ph1_deg.returnPressed.connect(self.check_val)
        self.ui_ph2_deg.returnPressed.connect(self.check_val)
        self.ui_ph3_deg.returnPressed.connect(self.check_val)
        self.ui_mag_amp.returnPressed.connect(self.check_val)
        self.ui_reg_val.returnPressed.connect(self.check_val)
        self.ui_reg_add_2.returnPressed.connect(self.read_reg)

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
        self.button_SML01.clicked.connect(self.btnClicked)
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
        try:
            ph = np.float(phase)
            self.mysocket.send(b"2")
            ph = c_double(ph)
            mag_amp = np.float(self.ui_mag_amp.text())
            mag_amp = c_double(2 ** mag_amp)
            #print(mag_amp)
            phase_angle = self.phase_set.IQ_phase_shift(ph, mag_amp)
            print(addr)
            msg = str(np.uint32(phase_angle)) + ',' + addr
            #print(msg)
            self.mysocket.send(msg.encode())
            #sprint('Update channel' + str(ch) + 'phase offset')
            self.update_msg('Now, you are right, the phase updated!!')
        except ValueError:
            self.update_msg('You have enter number!!!')
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
#        self.button_phase.hide()
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
            plot.addLine(x=0,pen='r')
            plot.addLine(y=0,pen='r')
    def set_plot_ui(self):
        self.max_range = 32000
        self.plt_data = self.rtplot.addPlot(
            labels={'left': 'Level', 'bottom': 'data points'})  # change here for plt_i in seperated plot

        self.plt_ch = [0]*5
        self.plt_ch[0]= self.plt_ch0_iq.addPlot()
        self.plt_ch[0].setXRange(-self.max_range, self.max_range, padding=0)
        self.plt_ch[0].setYRange(-self.max_range, self.max_range, padding=0)

        self.plt_ch[1]= self.plt_ch1_iq.addPlot()
        self.plt_ch[1].setXRange(-self.max_range, self.max_range, padding=0)
        self.plt_ch[1].setYRange(-self.max_range, self.max_range, padding=0)

        self.plt_ch[2]= self.plt_ch2_iq.addPlot()
        self.plt_ch[2].setXRange(-self.max_range, self.max_range, padding=0)
        self.plt_ch[2].setYRange(-self.max_range, self.max_range, padding=0)

        self.plt_ch[3] = self.plt_ch3_iq.addPlot()
        self.plt_ch[3].setXRange(-self.max_range, self.max_range, padding=0)
        self.plt_ch[3].setYRange(-self.max_range, self.max_range, padding=0)

        self.bram0.setChecked(1)
        self.bram1.setChecked(1)
        self.bram2.setChecked(1)
        self.bram3.setChecked(1)
        self.bram4.setChecked(1)
        self.bram5.setChecked(1)
        self.bram6.setChecked(1)
    def fft_data(self, ch, iq):
        if iq == 'q':
            n = len(self.fft_q[ch])
            fft_q = self.fft_q[ch].np.astype(int)
            nfft = abs(fft_q[range(int(n/2)/(n))])
            print(len(nfft))
            #print(nfft)
        else:
            n = len(self.fft_i[ch])
            fft_i = int(self.fft_i[ch])
            nfft = abs(fft_i[range(int(n/2)/(n))])
        return nfft
    def first_plot(self):
        line_w = 2
        sympole_s = 5
        self.plt_curve_q = [0]*self.nbr_bram
        self.plt_curve_i = [0]*self.nbr_bram
        self.plt_scatter = [0]*self.nbr_bram
        pen=[0]*self.nbr_bram*2
        color_line =['g','b','r','y','k',(180,165,0),(128,0,128),'b', 'r']
        #**********************************************#

        k=0
        for k in range(self.nbr_bram):
            pen[k] = pg.mkPen(color=pen[k], width=line_w, style=QtCore.Qt.DashLine)
            k=k+1

        i = 0
        for i in range(self.nbr_bram):
            self.plt_curve_q[i] = self.plt_data.plot(self.buf_q[i], pen=color_line[i])
            self.plt_curve_i[i] = self.plt_data.plot(self.buf_i[i], pen=pen[i])
            if i < 4:
                n = min(len(self.buf_q[i]), len(self.buf_i[i]))
                self.plt_scatter[i] = self.plt_ch[i].plot(self.buf_i[i][0:n], self.buf_q[i][0:n], pen=None, symbol='o', symbolPen=color_line[i])
                self.plt_scatter[i].setSymbolSize(sympole_s)
                self.polar_plot(self.plt_ch[i])
            i=i+1
        self.plt_scatter[4] = self.plt_ch[0].plot(self.buf_i[4][0:n], self.buf_q[4][0:n], pen=None, symbol='o', symbolPen=color_line[4])
        self.plt_scatter[4].setSymbolSize(sympole_s)
    def write_reg(self):
        self.mysocket.send(b"3")
        msg = self.ui_reg_val.text() + ',' + self.ui_reg_add.text()
        self.mysocket.send(msg.encode())
        self.update_msg('You write '+ self.ui_reg_val.text() +' to ' + self.ui_reg_add.text())
    def read_reg(self):
        self.mysocket.send(b"4")
        time.sleep(0.1)
        self.mysocket.send(self.ui_reg_add_2.text().encode())
        time.sleep(0.05)
        msgServeur = self.mysocket.recv(4096).decode()
        self.ui_reg_val_2.setText(msgServeur)
        self.update_msg('See, You get the value:' + msgServeur +' from '+ self.ui_reg_add_2.text())
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

        if (self.last_mag_amp != self.ui_mag_amp.text()) & (self.ui_mag_amp.text() != ''):
            print(int(self.ui_mag_amp.text()))
            if 0 < int(self.ui_mag_amp.text()) < 16:
                for i in range(4):
                    self.calc_phase_angle(i)
                    time.sleep(0.1)
                    print('ok, changed mag /n')
                self.last_mag_amp = self.ui_mag_amp.text()
                self.update_msg('Good boy, this time you are right!!!')
            else:
                self.update_msg('This value must between 1 and 15!!!')

        if (self.last_reg != self.ui_reg_val.text()) & (self.ui_reg_val.text() != ''):
            self.write_reg()
        time.sleep(0.01)
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
        #self.timer.timeout.connect(self.check_val)    ## check and update phase at each refresh
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
        self.tmp_bram = [None] * 2 * self.nbr_bram
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
        self.fft_q = [None] * self.nbr_bram
        self.fft_i = [None] * self.nbr_bram

        while j < self.nbr_bram:  # number of bram data bloc
            if self.tmp_bram[k] == 'None':
                pass
            else:
                try:
                    bram_data[j] = self.tmp_bram[k] + self.tmp_bram[k + 1]

                    self.buf_q[j] = bram_data[j][0::2]
                    self.buf_i[j] = bram_data[j][1::2]
                except TypeError:
                    print('type errer')
                n = len(self.buf_q[j])
                self.fft_q[j] = np.fft.fft(self.buf_q[j], n)
                self.fft_i[j] = np.fft.fft(self.buf_i[j], n)
                self.bram0_num_data.setText(str(n))
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
    def calc_amp_phase(self, Q, I,flag):
        amp=[]
        phi=[]
        if flag ==1:
            for q, i in zip(Q, I):
                amp.append(math.sqrt(np.square(q) + np.square(i)))
                phi.append(math.degrees(math.atan2(q,i)))
        else:
            amp = math.sqrt(np.square(Q) + np.square(I))
            phi = math.degrees(math.atan2(Q,I))

        return [amp, phi]
    def update_graph(self):
        self.clear_plot()

        if self.bram0.isChecked():
            self.plt_curve_q[0].setData(self.buf_q[0])
            self.plt_curve_i[0].setData(self.buf_i[0])
            self.plt_curve_q[0].setPos(len(self.buf_q[0]), 0)
            self.plt_curve_i[0].setPos(len(self.buf_i[0]), 0)

            n = min(len(self.buf_q[0]), len(self.buf_i[0]))
            self.plt_scatter[0].setData(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.I_moy0 = np.mean(self.buf_i[0])
            self.Q_moy0 = np.mean(self.buf_q[0])

            [amp_m, phi] =self.calc_amp_phase(self.Q_moy0, self.I_moy0, 0)   # calc amp and phase RMS
            self.ui_ch0_amp.setText(str(round(amp_m, 2)))
            self.ui_ch0_phi.setText(str(round(phi, n_bit)))

            [amp, phi] = self.calc_amp_phase(self.buf_q[0], self.buf_i[0], 1) # calc amp and phase std
            self.ui_ch0_amp_std.setText(str(round(np.std(amp)/amp_m, n_bit)))
            self.ui_ch0_phi_std.setText(str(round(np.std(phi), n_bit)))
        else:
            self.plt_scatter[0].clear()
        if self.bram1.isChecked():
            #self.curve_q1.setData(self.fft_q1)
            #self.curve_i1.setData(self.fft_i1)
            self.plt_curve_q[1].setData(self.buf_q[1])
            self.plt_curve_i[1].setData(self.buf_i[1])
            self.plt_curve_q[1].setPos(len(self.buf_q[1]), 0)
            self.plt_curve_i[1].setPos(len(self.buf_i[1]), 0)


            n = min(len(self.buf_q[1]), len(self.buf_i[1]))
            #self.plt_ch0.plot(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.plt_scatter[1].setData(self.buf_i[1][0:n], self.buf_q[1][0:n])
            self.I_moy1 = np.mean(self.buf_i[1])
            self.Q_moy1 = np.mean(self.buf_q[1])

            [amp_m, phi] =self.calc_amp_phase(self.Q_moy1, self.I_moy1, 0)   # calc amp and phase RMS
            self.ui_ch1_amp.setText(str(round(amp_m, 2)))
            self.ui_ch1_phi.setText(str(round(phi, n_bit)))

            [amp, phi] = self.calc_amp_phase(self.buf_q[1], self.buf_i[1], 1) # calc amp and phase std
            self.ui_ch1_amp_std.setText(str(round(np.std(amp)/amp_m, n_bit)))
            self.ui_ch1_phi_std.setText(str(round(np.std(phi), n_bit)))
        else:
            self.plt_scatter[1].clear()
        if self.bram2.isChecked():
            #self.curve_q2.setData(self.fft_q2)
            #self.curve_i2.setData(self.fft_i2)
            self.plt_curve_q[2].setData(self.buf_q[2])
            self.plt_curve_i[2].setData(self.buf_i[2])
            self.plt_curve_q[2].setPos(len(self.buf_q[2]), 0)
            self.plt_curve_i[2].setPos(len(self.buf_i[2]), 0)

            n = min(len(self.buf_q[2]), len(self.buf_i[2]))
            #self.plt_ch0.plot(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.plt_scatter[2].setData(self.buf_i[2][0:n], self.buf_q[2][0:n])
            self.I_moy2 = np.mean(self.buf_i[2])
            self.Q_moy2 = np.mean(self.buf_q[2])

            [amp_m, phi] =self.calc_amp_phase(self.Q_moy2, self.I_moy2, 0)   # calc amp and phase RMS
            self.ui_ch2_amp.setText(str(round(amp_m, 2)))
            self.ui_ch2_phi.setText(str(round(phi, n_bit)))

            [amp, phi] = self.calc_amp_phase(self.buf_q[2], self.buf_i[2], 1) # calc amp and phase std
            self.ui_ch2_amp_std.setText(str(round(np.std(amp)/amp_m, n_bit)))
            self.ui_ch2_phi_std.setText(str(round(np.std(phi), n_bit)))

            self.tmp_ch2_imoy.setText(str(round(self.I_moy2, n_bit)))
            self.tmp_ch2_qmoy.setText(str(round(self.Q_moy2, n_bit)))
        else:
            self.plt_scatter[2].clear()
        if self.bram3.isChecked():
            #self.curve_q3.setData(self.fft_q3)
            #self.curve_i3.setData(self.fft_i3)
            self.plt_curve_q[3].setData(self.buf_q[3])
            self.plt_curve_i[3].setData(self.buf_i[3])
            self.plt_curve_q[3].setPos(len(self.buf_q[3]), 0)
            self.plt_curve_i[3].setPos(len(self.buf_i[3]), 0)

            n = min(len(self.buf_q[3]), len(self.buf_i[3]))
            #self.plt_ch0.plot(self.buf_i[0][0:n], self.buf_q[0][0:n])
            self.plt_scatter[3].setData(self.buf_i[3][0:n], self.buf_q[3][0:n])
            self.I_moy3 = np.mean(self.buf_i[3])
            self.Q_moy3 = np.mean(self.buf_q[3])

            [amp_m, phi] = self.calc_amp_phase(self.Q_moy3, self.I_moy3, 0)  # calc amp and phase RMS
            self.ui_ch3_amp.setText(str(round(amp_m, 2)))
            self.ui_ch3_phi.setText(str(round(phi, n_bit)))

            [amp, phi] = self.calc_amp_phase(self.buf_q[3], self.buf_i[3], 1)  # calc amp and phase std
            self.ui_ch3_amp_std.setText(str(round(np.std(amp)/amp_m, n_bit)))
            self.ui_ch3_phi_std.setText(str(round(np.std(phi), n_bit)))

            self.tmp_ch3_imoy.setText(str(round(self.I_moy3, n_bit)))
            self.tmp_ch3_qmoy.setText(str(round(self.Q_moy3, n_bit)))
        else:
            self.plt_scatter[3].clear()
        if self.bram4.isChecked():
            # self.curve_q3.setData(self.fft_q3)
            # self.curve_i3.setData(self.fft_i3)
            try:
                self.plt_curve_q[4].setData(self.buf_q[4])
                self.plt_curve_i[4].setData(self.buf_i[4])
                self.plt_curve_q[4].setPos(len(self.buf_q[4]), 0)
                self.plt_curve_i[4].setPos(len(self.buf_i[4]), 0)
            except IndexError:
                self.update_msg('Can NOT find BRAM 4!!!')
                self.bram4.setChecked(0)
            n = min(len(self.buf_q[4]), len(self.buf_i[4]))
            self.plt_scatter[4].setData(self.buf_i[4][0:n], self.buf_q[4][0:n])
            self.I_moy4 = np.mean(self.buf_i[4])
            self.Q_moy4 = np.mean(self.buf_q[4])


            [amp_m, phi] = self.calc_amp_phase(self.Q_moy4, self.I_moy4, 0)  # calc amp and phase RMS
            self.ui_ch4_amp.setText(str(round(amp_m, 2)))
            self.ui_ch4_phi.setText(str(round(phi, n_bit)))

            [amp, phi] = self.calc_amp_phase(self.buf_q[4], self.buf_i[4], 1)  # calc amp and phase std
            self.ui_ch4_amp_std.setText(str(round(np.std(amp) / amp_m, n_bit)))
            self.ui_ch4_phi_std.setText(str(round(np.std(phi), n_bit)))

        if self.bram5.isChecked():
            # self.curve_q3.setData(self.fft_q3)
            # self.curve_i3.setData(self.fft_i3)
            try:
                self.plt_curve_q[5].setData(self.buf_q[5])
                self.plt_curve_i[5].setData(self.buf_i[5])
                self.plt_curve_q[5].setPos(len(self.buf_q[5]), 0)
                self.plt_curve_i[5].setPos(len(self.buf_i[5]), 0)
            except IndexError:
                self.update_msg('Can NOT find BRAM 5!!!')
                self.bram5.setChecked(0)

        if self.bram6.isChecked():
            # self.curve_q3.setData(self.fft_q3)
            # self.curve_i3.setData(self.fft_i3)
            try:
                self.plt_curve_q[6].setData(self.buf_q[6])
                self.plt_curve_i[6].setData(self.buf_i[6])
                self.plt_curve_q[6].setPos(len(self.buf_q[6]), 0)
                self.plt_curve_i[6].setPos(len(self.buf_i[6]), 0)
            except IndexError:
                self.update_msg('Can NOT find BRAM 6!!!')
                self.bram6.setChecked(0)
        '''
        ##################

        '''
    def clear_plot(self):
        i=0
        try:
            for i in range(self.nbr_bram):
                self.plt_curve_q[i].clear()
                self.plt_curve_i[i].clear()
                if i<4:
                    self.plt_scatter[i].clear()
                i=i+1
        except AttributeError:
            self.update_msg('Err')

    def update_msg(self, msg):
        self.msgbox.clear()
        self.msgbox.setText(msg)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = llrf_graph_window()
    myWin.show()
    sys.exit(app.exec_())
