import FUNCTIONS.functions
import socket

basics = FUNCTIONS.functions.basics()
sqlall = FUNCTIONS.SQLall.sqlall()

class BYD_Status:
    def __init__(self):
        self.BUFFER_SIZE = 1024
        self.MESSAGE_2 = "01030500001984cc" #read data

    def buf2int16SI(self, byteArray, pos): #signed
        result = byteArray[pos] * 256 + byteArray[pos + 1]
        if (result > 32768):
            result -= 65536
        return result

    def buf2int16US(self, byteArray, pos): #unsigned
        result = byteArray[pos] * 256 + byteArray[pos + 1]
        return result

    def read(self, byd_ip, byd_port):  
        try:
        
            #connection BYD
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)  # Timeout in Sekunden
            client.connect((byd_ip, byd_port))
            #message 2
            client.send(bytes.fromhex(self.MESSAGE_2))
            #read data
            data = client.recv(self.BUFFER_SIZE)
            maxvolt = self.buf2int16SI(data, 5) * 1.0 / 100.0

            client.close()

            return maxvolt
      
        except Exception as ex:
            print ("### ERROR BYD_Akku nicht erreichbar, Route, IP prüfen: ", ex)
            return 0
