import socket
import json
import threading
import struct
import time
"""
Usage example:
self.udpClient = UdpAsyncClient(self)
self.udpClient.startListener(5005, self.serverUdpIncomingData)

def serverUdpIncomingData(self, data):
        print("UDP data-", data)
        pass
"""
class CanMessage:
    def __init__(self, payload_bytes):
        """
        Парсить payload (16 байтів) у структуру CAN повідомлення.
        
        Структура payload:
        - Байт 0: deviceId
        - Байт 1: command  
        - Байт 2: idType
        - Байти 3-6: canId (4 байти, little-endian)
        - Байт 7: dlc
        - Байти 8-15: data[8] (8 байтів)
        """
        if len(payload_bytes) != 16:
            raise ValueError(f"Payload must be 16 bytes, got {len(payload_bytes)}")
        
        self.device_id = payload_bytes[0]
        self.command = payload_bytes[1]
        self.id_type = payload_bytes[2]
        
        # Розпаковуємо canId як 32-бітне число (little-endian)
        self.can_id = struct.unpack('<I', payload_bytes[3:7])[0]
        
        self.dlc = payload_bytes[7]
        
        # Витягуємо тільки значущі байти даних (dlc байтів)
        self.data = payload_bytes[8:8+min(self.dlc, 8)]
        
    def __str__(self):
        data_hex = ' '.join(f'{b:02X}' for b in self.data)
        return (f"CAN Message: ID=0x{self.can_id:08X}, "
                f"DLC={self.dlc}, Data=[{data_hex}], "
                f"DeviceID={self.device_id}, Command={self.command}")
    
class SmartHomeGatewayUdpClient:
    def __init__(self,  cbFn=None, gatewayIp=None, rxPort=4030, txPort=4031, bufferSize=1024):
        self.parrentCb = cbFn 
        self.gatewayIp = gatewayIp
        self.txPort = txPort
        self.rxPort = rxPort
        self.bufferSize = bufferSize
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listener_thread = None
        self.listening = False

    def startListener(self):
        """
        Запускає прослуховування UDP-портів в окремому потоці.
        
        Parameters:
        port (int): Порт для прослуховування.
        cbFunction (function): Функція зворотного виклику для обробки отриманих даних.
        """
        self.listening = True
        self.listener_thread = threading.Thread(target=self.run)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def run(self):
        self.sock.bind(('', self.rxPort))
        while self.listening:
            try:
                data, _ = self.sock.recvfrom(self.bufferSize)
                #message = data.decode('utf-8')
                if len(data) >= 21:
                    if (data[0] == 0xAA and data[1] == 0x11 and 
                    data[2] == 0x22 and data[3] == 0xBB):
                        if data[20] == 0x55:
                            payload = data[4:20]

                            try:
                                can_message = CanMessage(payload)
                                self.parrentCb(can_message)
                            except ValueError as e:
                                print(f"Error parsing CAN message: {e}")
                        else:
                            print("Invalid end marker")
                    else:
                        print("Invalid header")     
                else:
                    print(f"Packet too short: {len(data)} bytes")
                
            except Exception as e:
                print(f"Error in UDP listener: {e}")
                pass

    def stopListener(self):
        self.listening = False
        if self.listener_thread:
            self.listener_thread.join()

    def send_data(self, data, ip, port):
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            self.sock.sendto(data, (self.gatewayIp, self.txPort))
        except Exception as e:
            print(f"Error sending data: {e}")

    def sendCanMessage(self, deviceId=0, msgType=1, idType=1, can_id=0, data_bytes=[0]*8):
        """
        Відправляє CAN повідомлення у форматі пакету.
    
        Parameters:
        device_id (int): ID пристрою (0-255)
        command (int): Команда (0-255)
        id_type (int): Тип ID (0=standard, 1=extended)
        can_id (int): CAN ID (32-бітне число)
        data_bytes (list): Масив байтів даних (максимум 8 байтів)
        * Byte [0..3]    : uint32_t  msgHeader     (Must be 0xAA1122BB)
        * Byte [4]       : uint8_t   deviceId      (0 = local device)
        * Byte [5]       : uint8_t   msgType       (e.g. LOCAL_CMD, CAN_CMD)
        * Byte [6]       : uint8_t   idType        (0 = standard, 1 = extended)
        * Byte [7..10]   : uint32_t  canId         (CAN message ID)
        * Byte [11]      : uint8_t   dlc           (CAN data length: 0–8)
        * Byte [12..19]  : uint8_t   data[8]       (CAN data payload)
        * Byte [20]      : uint8_t   endMarker     (Must be 0x55)
        """
        try:
            # Перевіряємо довжину даних
            if len(data_bytes) > 8:
                raise ValueError("Data length cannot exceed 8 bytes")
            if(can_id == 0):
                raise ValueError("CAN ID cannot be zero")
            # Будуємо пакет
            packet = bytearray()
        
            # Заголовок (4 байти): 0xAA1122BB
            packet.extend([0xAA, 0x11, 0x22, 0xBB])
        
            # Payload (16 байтів)
            packet.append(deviceId & 0xFF)          # Байт 4: deviceId
            packet.append(msgType & 0xFF)            # Байт 5: command
            packet.append(idType & 0xFF)            # Байт 6: idType
        
            # Байти 7-10: canId (32-бітне число, little-endian)
            can_id_bytes = struct.pack('<I', can_id)
            packet.extend(can_id_bytes)
        
            # Байт 11: dlc (довжина даних)
            dlc = len(data_bytes)
            packet.append(dlc)
        
            # Байти 12-19: data (8 байтів, доповнюємо нулями якщо потрібно)
            data_padded = data_bytes + [0] * (8 - len(data_bytes))
            packet.extend(data_padded)
        
            # Байт 20: кінцевий маркер 0x55
            packet.append(0x55)
        
            # Відправляємо пакет
            if self.gatewayIp:
                self.sock.sendto(packet, (self.gatewayIp, self.txPort))
                #print(f"Sent CAN packet: ID=0x{can_id:08X}, DLC={dlc}, Data={data_bytes}, IP={self.gatewayIp}, Port={self.txPort}")
                #hex_string = ' '.join(f'{b:02X}' for b in packet)
                #print(f"Packet hex: {hex_string}")
            else:
                print("Gateway IP not set")
            
        except Exception as e:
            print(f"Error sending CAN data: {e}")


def serverUdpIncomingData(can_message):

        device_id = can_message.device_id      # Байт 0
        command = can_message.command          # Байт 1  
        id_type = can_message.id_type         # Байт 2
        can_id = can_message.can_id           # Байти 3-6 (як 32-бітне число)
        dlc = can_message.dlc                 # Байт 7
        data_bytes = can_message.data         # Байти 8-15 (тільки значущі)

        if(can_id == 0x69):
            print(f"CAN ID: 0x{can_id:08X}, dalas Temp:{can_message.data[0]}, zone1: {can_message.data[1]}, zone2: {can_message.data[2]}, zone3: {can_message.data[3]}")
        if(can_id == 0x70):
            print(f"CAN ID: 0x{can_id:08X}, REL: {can_message.data[0]}, IN: {can_message.data[1]}; {can_message.data[2]}-{can_message.data[3]}-{can_message.data[4]}; {can_message.data[5]}:{can_message.data[6]}:{can_message.data[7]}")


if __name__ == "__main__":
    udpClient = SmartHomeGatewayUdpClient(cbFn=serverUdpIncomingData, gatewayIp="192.168.1.18", rxPort=4030, txPort=4031, bufferSize=1024)
    udpClient.startListener()

    while True:
        time.sleep(1)
        udpClient.sendCanMessage(can_id=0x100, data_bytes=[0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0], msgType=1)

        #time.sleep(1)
        #print("set 1")
        #udpClient.sendCanMessage(can_id=0x100, data_bytes=[0x01, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0])

        #time.sleep(1)
        #print("set 2")
        #udpClient.sendCanMessage(can_id=0x100, data_bytes=[0x02, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0])

        #time.sleep(1)
        #print("set 3")
        #udpClient.sendCanMessage(can_id=0x100, data_bytes=[0x03, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0])