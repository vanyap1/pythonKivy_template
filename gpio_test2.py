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
    ("REL_GATEWAY", 8),
    ("REL_SWITCH", 9),
    ("REL3", 10),
    ("REL4", 11),
    ("MAINTENANCE_LED", 12),
    ("UNDEFINED_LED", 13),
    ("PA6", 14),
    ("ERR_LED", 15)
]

INPUT_PINS = [
    ("MAINTENANCE_BTN", 0),
    ("UNDEFINED_BTN", 1),
    ("PB2", 2),
    ("PB3", 3),
    ("PB4", 4),
    ("PB5", 5),
    ("PB6", 6),
    ("PB7", 7)
]


chip = gpiod.Chip(CHIP)

out_lines = {name: chip.get_line(offset) for name, offset in OUTPUT_PINS}
in_lines = {name: chip.get_line(offset) for name, offset in INPUT_PINS}

for name, line in out_lines.items():
    line.request(consumer=name, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[1])

for name, line in in_lines.items():
    line.request(
        consumer=name,
        type=gpiod.LINE_REQ_DIR_IN,
        flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP,
    )




class Main():
    msgStopEmuTimer = 0
    def __init__(self):
        
        self.relState = 0
        while True:
            
            out_lines["REL3"].set_value(ON_STATE if in_lines['MAINTENANCE_BTN'].get_value() == 0 else OFF_STATE)
            out_lines["MAINTENANCE_LED"].set_value(ON_STATE if in_lines['MAINTENANCE_BTN'].get_value() == 0 else OFF_STATE)
            out_lines["UNDEFINED_LED"].set_value(ON_STATE if in_lines['UNDEFINED_BTN'].get_value() == 0 else OFF_STATE)

            if in_lines['UNDEFINED_BTN'].get_value() == 0:
                print("UNDEFINED_BTN pressed!")
            if in_lines['MAINTENANCE_BTN'].get_value() == 0:
                print("MAINTENANCE_BTN pressed!")

            print(f"{in_lines['MAINTENANCE_BTN'].get_value()} {in_lines['UNDEFINED_BTN'].get_value()}, {self.relState}")
            
            time.sleep(0.5)
    
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