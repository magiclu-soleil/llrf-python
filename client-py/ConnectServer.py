import socket


class ConnectServer:
    def __init__(self, host_server, port_server):
        self.host_server = host_server    # By default 172.161.6.85
        self.port_server = port_server    # By default 50000
        # 1) création du socket :
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def __create__(self):
        # 2) envoi d'une requête de connexion au serveur :
        self.my_socket.connect((self.host_server, self.port_server))
        #sys.exit()
        print("Server connected.")
        return self.my_socket

    def connect_bram(self, addr0, offset_data, addr_len, offset_trig, nbr_bram, bram_size):
        '''
        self.bram_addr = addr0
        self.offset = offset_data
        self.size = size
        self.offset_trig = offset_trig
        '''
        str_msg = 'addr' + addr0 +'offset' + offset_data + 'bram_len' + addr_len + 'trig' + offset_trig + 'nbrBram' + nbr_bram + '1bramSize' + bram_size +'!'
        print(str_msg)
        self.my_socket.send(str_msg.encode())


