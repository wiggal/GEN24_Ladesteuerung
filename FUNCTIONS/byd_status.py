import socket

class BYD_Status:
    def __init__(self):
        self.BUFFER_SIZE = 1024
        self.MESSAGE_2 = "01030500001984cc" #read data

    def buf2int16SI(self, byteArray, pos): #signed
        result = byteArray[pos] * 256 + byteArray[pos + 1]
        if (result >= 32768):
            result -= 65536
        return result

    def buf2int16US(self, byteArray, pos): #unsigned
        result = byteArray[pos] * 256 + byteArray[pos + 1]
        return result

    def read(self, byd_ip, byd_port):  
        client = None
        try:
        
            #connection BYD
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)  # Timeout in Sekunden
            client.connect((byd_ip, byd_port))
            #message 2
            client.sendall(bytes.fromhex(self.MESSAGE_2))
            #read data: Die Antwort kann in mehreren TCP-Paketen ankommen (z.B. bei seriell-Ethernet-Wandlern),
            # deshalb lesen, bis die für den Wert benötigten 7 Bytes da sind
            data = b''
            while len(data) < 7:
                chunk = client.recv(self.BUFFER_SIZE)
                if not chunk:
                    break   # Gegenstelle hat die Verbindung geschlossen
                data += chunk
            if len(data) < 7:
                raise ValueError("Antwort zu kurz (" + str(len(data)) + " Bytes)")
            maxvolt = self.buf2int16SI(data, 5) * 1.0 / 100.0

            return maxvolt

        except Exception as ex:
            # Verbindung/Timeout, unvollständige Antwort oder ungültige IP: Wert 0 liefern, wie bisher
            print ("### ERROR BYD_Akku nicht erreichbar oder ungültige Antwort, Route, IP prüfen: ", ex)
            return 0
        finally:
            # Socket auch im Fehlerfall schließen
            if client is not None:
                client.close()
