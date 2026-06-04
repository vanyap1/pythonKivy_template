import os
import select  # Потрібно для неблокуючої перевірки кнопок
import time
import json
import gpiod
from evdev import InputDevice, ecodes
from remoteCtrlServer.httpserver import start_server_in_thread
from remoteCtrlServer.udpService import UdpAsyncClient
from SH_DTO.gatewayDto import *
from SH_DTO.smartHomeUdpService import SmartHomeGatewayUdpClient
from SH_DTO.onlineChecker import OnlineCheckerService


gatewayKotelIP = "192.168.1.18"
gatewayKotelTxPort = 4031
gatewayKotelRxPort = 4030

maxMsgTimeTriggerVal = 10000 #milliseconds, if time between messages more than this value - trigger alert

DEVICE_PATH = '/dev/input/by-path/platform-gpio-keys-event'
BTN_0_CODE = 256
BTN_1_CODE = 257

dev = None
try:
    dev = InputDevice(DEVICE_PATH)
except (PermissionError, FileNotFoundError) as e:
    print(f"Попередження: Не вдалося відкрити кнопки ({e}). Запустіть від sudo.")

ON_STATE = 0
OFF_STATE = 1

CHIP = "gpiochip2"

OUTPUT_PINS = [
    ("PA0", 0),
    ("PA1", 1),
    ("PA2", 2),
    ("PA3", 3),
    ("PA4", 4),
    ("PA5", 5),
    ("PA6", 6),
    ("ERR_LED", 7)
]

INPUT_PINS = [
    ("PB0", 8),
    ("PB1", 9),
    ("PB2", 10),
    ("PB3", 11),
    ("PB4", 12),
    ("PB5", 13),
    ("PB6", 14),
    ("PB7", 15)
]


chip = gpiod.Chip(CHIP)

out_lines = {name: chip.get_line(offset) for name, offset in OUTPUT_PINS}
in_lines = {name: chip.get_line(offset) for name, offset in INPUT_PINS}

for name, line in out_lines.items():
    line.request(consumer=name, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

for name, line in in_lines.items():
    line.request(
        consumer=name,
        type=gpiod.LINE_REQ_DIR_IN,
        flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP,
    )




class Main():
    msgStopEmuTimer = 0
    def __init__(self):
        self.energyMonitor = UdpAsyncClient(self)
        self.energyMonitor.startListener(5005, self.serverUdpIncomingData)
        self.gateway = GatewayDto()
        self.kotelGateway = SmartHomeGatewayUdpClient(cbFn=self.smartHomeGatewayUdpClient, gatewayIp=gatewayKotelIP, rxPort=gatewayKotelRxPort, txPort=gatewayKotelTxPort, bufferSize=1024)
        self.kotelGateway.startListener()

        self._onlineChecker = OnlineCheckerService(gateway=self.gateway, servers=[{"192.168.1.5", "8.8.8.8"}])
        
        while True:
            self.MsgTimers = self.gateway.getLastUpdateIntervals()
            if self.MsgTimers["upsMsgInterval"] > maxMsgTimeTriggerVal or \
                self.MsgTimers["waterTankMsgInterval"] > maxMsgTimeTriggerVal or \
                self.MsgTimers["sensorUnitMsgInterval"] > maxMsgTimeTriggerVal or \
                self.MsgTimers["kotelMsgInterval"] > maxMsgTimeTriggerVal:
                
                out_lines["ERR_LED"].set_value(ON_STATE)
                time.sleep(0.5)
                self.msgStopEmuTimer = 0
            else:
                out_lines["ERR_LED"].set_value(OFF_STATE)
            
            time.sleep(0.5)
            print(f"{self.gateway.getLastUpdateIntervals()} / {self.msgStopEmuTimer}")
            self.msgStopEmuTimer += 1
    
    def serverUdpIncomingData(self, data):
        """Handle incoming Power Meter UDP data"""
        #print("Main PM:", data)
        try:
                            
            pm_data = json.loads(data) if isinstance(data, str) else data
            source = pm_data.get('source', 'AC')
            #print(f"Received PM data from: {pm_data}")
        except Exception as e:
            print(f"Error parsing PM data: {e}")

    def smartHomeGatewayUdpClient(self, can_message):
        #print(f"Received CAN message from Kotel Gateway: {can_message}")
        if self.msgStopEmuTimer < 20:
            self.gateway.canMsgParse(can_message)
        pass

    



if __name__ == "__main__":
    #KeyboardInterrupt для коректного завершення програми при натисканні Ctrl+C
    try:
        Main()
    except KeyboardInterrupt:
        print("Ending program...")
        #release all lines on exit and set to High all outputs
        for line in out_lines.values():
            line.set_value(1)
            line.release()
        for line in in_lines.values():
            line.release()