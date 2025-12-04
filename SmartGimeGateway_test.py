from threading import Thread
import time
import json  # Додайте цей імпорт
from smartHomeUdpService import SmartHomeGatewayUdpClient

class MainApp():
    def __init__(self):
        print("Initializing MainApp...")
        self.name = "SmartGimeGateway"
        self.udpClient = SmartHomeGatewayUdpClient(cbFn=self.serverUdpIncomingData, gatewayIp="192.168.1.18", rxPort=4030, txPort=4031, bufferSize=1024)
        
        self.udpClient.startListener()
        
        while True:
            time.sleep(1)
            self.udpClient.sendCanMessage(can_id=0x100, data_bytes=[0x0, 0x0, 0x64, 0x00, 0x3E, 0x26, 0x00, 0x00])

            time.sleep(1)
            self.udpClient.sendCanMessage(can_id=0x100, data_bytes=[0x0, 0x01, 0x64, 0x00, 0x3E, 0x26, 0x00, 0x00])

            time.sleep(1)
            self.udpClient.sendCanMessage(can_id=0x100, data_bytes=[0x01, 0x0, 0x64, 0x00, 0x3E, 0x26, 0x00, 0x00])

            time.sleep(1)
            self.udpClient.sendCanMessage(can_id=0x100, data_bytes=[0x01, 0x01, 0x64, 0x00, 0x3E, 0x26, 0x00, 0x00])

            
    def serverUdpIncomingData(self, can_message):

        device_id = can_message.device_id      # Байт 0
        command = can_message.command          # Байт 1  
        id_type = can_message.id_type         # Байт 2
        can_id = can_message.can_id           # Байти 3-6 (як 32-бітне число)
        dlc = can_message.dlc                 # Байт 7
        data_bytes = can_message.data         # Байти 8-15 (тільки значущі)

        if(can_id == 0x69):
            print(f"dalas Temp:{can_message.data[0]}, zone1: {can_message.data[1]}, zone2: {can_message.data[2]}, zone3: {can_message.data[3]}")

        # Виводимо інформацію
        #print(f"  Device ID: {device_id}")
        #print(f"  Command: {command}")
        #print(f"  ID Type: {id_type}")
        #print(f"  CAN ID: 0x{can_id:08X}")
        #print(f"  Data Length: {dlc}")
        #print(f"  Data bytes: {[hex(b) for b in data_bytes]}")
        
        

if __name__ == "__main__":
    app = MainApp()