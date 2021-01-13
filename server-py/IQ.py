# Ce serveur attend la connexion d'un client, pour entamer un dialogue avec lui

import os
import socket
import sys
import time
from pathlib import Path
import subprocess
import rw_mio
import struct
import math

ip_server = '172.16.6.85'
port_server = 50003

'''
bram_size_in_8b  = 8192  # for two bram total 8k=8*1024
bram_size_in_16b = bram_size_in_8b/2 # 4096
one_bram_size_in_16b = int(bram_size_in_16b/2)  # for two bram block
one_bram_size_in_8b = int(bram_size_in_8b/2)
'''
class server_socket(object):

    def __init__(self,ip_server,port_server):
        #Source Server IP
        self.HOST = ip_server # '172.16.6.85'
        self.PORT = port_server
        # self.__create__()
        # self.__wait__(mySocket)

    def __create__(self):
        # 1) création du socket :
        #socket.setdefaulttimeout(30)
        self.mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.mysocket.bind((self.HOST, self.PORT))
        except socket.error:
            print ("Socket Failed!!!")
            sys.exit()

        ##########################
    def close_connect(self):
            # 6) Fermeture de la connexion :
            self.connexion.close()
            print ("Disconnected.")
    def chunks(self,arr,n):
        return [arr[i:i+n] for i in range(0, len(arr), n)]
    def get_data(self):

        '''
        one BRAM = 4K
        for nbr_bram = 2

        print(self.data_size)
        print(self.nbr_bram)
        print('************')
        '''
        txt = self.rw_bram.read(self.bram_offset, self.data_size*self.nbr_bram)
        #print("bram total length:")
        #print(len(txt))

        ''' divid data by one size of bram(one value presented by 8bits) '''
        self.bram_data = self.chunks(txt, int(self.data_size/2))

        #print('bram block num:')
        #print(len(self.bram_data))
        '''
        print('data length:')
        print(len(self.bram_data[0]))
        print('data:')
        print(self.bram_data[0])
        #print('type bram_data')
        #print(type(self.bram_data[0]))
        '''
    def send_data(self):
        # Send message to client
        for msgServeur in self.bram_data:

            #print('length str data ')
            #print(len(str(msgServeur)))
            #msgServeur = str(msg).encode()
            #print('send data size:')
            #print(len(msgServeur))
            '''
            print('data from server:')
            format_str = "h" * (int(len(msgServeur))//2)
            msg = struct.unpack(format_str,msgServeur)
            print('converted data length:')
            print(len(msg))
            '''
            self.connexion.send(msgServeur)
            time.sleep(0.01)
        self.connexion.send(b"data_ok")
    def trig_data_send(self, offset_trig_addr):
        reg_val=self.rw_bram.read8(offset_trig_addr)
        reg_val = reg_val | 1        # mask = 1
        self.rw_bram.write8(offset_trig_addr,reg_val)
        time.sleep(0.02)
        self.get_data()
        self.send_data()
        self.bram_data=[]
        reg_val = reg_val & (reg_val-1)
        self.rw_bram.write8(offset_trig_addr,reg_val)
    def mem_cmd(self,msg_str):
        self.bram_addr = int(msg_str[4:14],0)
        '''data offset'''
        index_offset_fin = msg_str.find('bram_len')
        index_offset = msg_str.find('offset')
        self.bram_offset = int(msg_str[index_offset+6:index_offset_fin],0)

        '''trigger address'''
        index_trig = msg_str.find('trig')
        index_trig_fin = msg_str.find('nbrBram')
        self.offset_trig = int(msg_str[(index_trig+4):index_trig_fin],0)

        ''' BRAM map length '''
        index_addrLen = msg_str.find('bram_len')
        index_addrLen_fin = msg_str.find('trig')
        self.bram_len = int(msg_str[(index_addrLen+8):index_addrLen_fin],16)

        ''' One bram size '''
        index_dataSize = msg_str.find('1bramSize')
        self.data_size = int(msg_str[(index_dataSize+9):-1],10)

        ''' nb. of bram 2 or 4 '''
        index_nbrBram = msg_str.find('nbrBram')
        #print(msg_str[(index_nbrBram+7):(index_dataSize)])
        #print('****')
        self.nbr_bram = int(msg_str[(index_nbrBram+7):(index_dataSize)],)

        '''
        Number of values is presented by 16 bits
        BRAM size is presented by 8 bits
        '''
        self.num_val = int(self.data_size*self.nbr_bram/2)
        '''
        print('trigger addr:')
        print(self.offset_trig)
        print('bram address:')
        print(self.bram_addr)
        print('self.bram_offset:')
        print(self.bram_offset)
        print('self.bram_addr:')
        print(self.bram_addr)
        '''

    def phase_cmd(self):
        msgClient = self.connexion.recv(16384)
        msg = msgClient.decode().split(',')
        try:
            print(msg)
            print('phase')
            print(msg[0])
            print('address')
            print(msg[1])
            phase_angle = int(msg[0])
            offset_phase_addr = int(msg[1],16)

            print(hex(phase_angle))
            print(hex(offset_phase_addr))

            if str(hex(offset_phase_addr)) in ['0xc','0x10','0x14','0x18']:
                self.rw_bram.write32(offset_phase_addr,phase_angle)
                print('phase updated')
        except IndexError:
            print('index error')
            pass

    def __processing__(self):
        while 1:
            # 3) Attente de la requête de connexion d'un client :
            print ("Server ready, waiting for requests ...")
            self.mysocket.listen(1)
            # 4) Etablissement de la connexion :
            self.connexion, self.adresse = self.mysocket.accept()
            print ("Client connected, adresse IP %s, port %s" % (self.adresse[0], self.adresse[1]))
            '''
            Memory config. from client
            connected to BRAM and send message to client
            '''
            #self.mysocket.setdefaulttimeout = 60
            msgClient = self.connexion.recv(16384)
            msg_str = msgClient.decode()
            print(msg_str)
            self.mem_cmd(msg_str)
            self.rw_bram = rw_mio.MMIO(self.bram_addr, self.bram_len)
            self.connexion.send(b'Mem ok')

            '''
             Trigger
             Get data from BRAM
             Send to client
            '''
            while 1:
                '''
                    offset for trigger
                '''
                msgClient = self.connexion.recv(16384)
                #print(msgClient)
                '''
                    phase changed ?
                '''
                if msgClient.decode() == "2":  # To read data from BRAM
                    '''
                    Phase config. from Client
                    '''
                    self.phase_cmd()

                '''
                    Continued signal
                '''
                if msgClient.decode() == "1":  # To read data from BRAM
                    self.trig_data_send(self.offset_trig)

                '''
                    Stop
                '''
                if msgClient.decode()== "0":
                    self.close_connect()
                    break

myserver = server_socket(ip_server, port_server)
print('Connected to server '+ ip_server +' '+ str(port_server))
myserver.__create__()
myserver.__processing__()
