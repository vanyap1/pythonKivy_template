from pymodbus.client import ModbusSerialClient
import time
from threading import Thread
'''
requirements
- pip install pymodbus==3.8.6 --break-system-packages
- pip install pyserial --break-system-packages
- json
- threading
- time
'''
class PhaseData:
    def __init__(self, voltage=0.0, current=0.0, power=0.0, pf=0.0):
        self.voltage = voltage
        self.current = current
        self.power = power
        self.power_factor = pf

    def __repr__(self):
        return f"U={self.voltage:.2f}V, I={self.current:.2f}A, P={self.power:.2f}W, PF={self.power_factor:.3f}"

class KWS306LStatus:
    def __init__(self, registers):
        # розбираємо по фазах
        self.phaseA = PhaseData(
            voltage=registers[0] / 100.0,
            current=registers[4] / 1000.0,
            power=registers[12] / 10,
            pf=registers[34] / 1000.0
        )
        self.phaseB = PhaseData(
            voltage=registers[1] / 100.0,
            current=registers[6] / 1000.0,
            power=registers[14] / 10,
            pf=registers[35] / 1000.0
        )
        self.phaseC = PhaseData(
            voltage=registers[2] / 100.0,
            current=registers[8] / 1000.0,
            power=registers[16] / 10,
            pf=registers[36] / 1000.0
        )

        self.total_power = registers[10] / 10
        self.temperature = registers[46]
        self.frequency = registers[37] / 100.0
        self.energyActive = registers[45] / 100.0
        self.energyReactive = registers[40] / 100.0
        self.energySym = registers[39] / 100.0
        self.relayStatus = registers[49]

    def __repr__(self):
        return (
            f"A: {self.phaseA}\n"
            f"B: {self.phaseB}\n"
            f"C: {self.phaseC}\n"
            f"Total Power={self.total_power}W, "
            f"Temp={self.temperature}°C, "
            f"Freq={self.frequency:.2f}Hz, "
            f"Energy Active={self.energyActive:.2f}kWh, "
            f"Energy Reactive={self.energyReactive:.2f}kWh, "
            f"Energy Sym={self.energySym:.2f}kWh, "
            f"Relay Status={self.relayStatus}"
        )

import json
# ...existing code...

class WS306LSReader(Thread):
    def __init__(self, ttyPort, cbFn):
        super().__init__()
        self.ttyPort = ttyPort
        self.callback = cbFn
        self.client = None
        self._running = True
        self.start()

    def connect(self):
        try:
            self.client = ModbusSerialClient(port=self.ttyPort, baudrate=9600,
                                             parity="N", stopbits=1, bytesize=8, timeout=1)
            if not self.client.connect():
                self.client = None
        except Exception as e:
            self.client = None

    def run(self):
        while self._running:
            if self.client is None:
                self.connect()
                if self.client is None:
                    self.callback(json.dumps({"status": "error", "error": "No RS485 adapter"}))
                    time.sleep(2)
                    continue

            try:
                res = self.client.read_holding_registers(address=0x000E, count=75, slave=1)
                if res is None or res.isError():
                    self.callback(json.dumps({"status": "error", "error": str(res)}))
                else:
                    status = KWS306LStatus(res.registers)
                    self.callback(json.dumps({
                        "status": "ok",
                        "A": status.phaseA.__dict__,
                        "B": status.phaseB.__dict__,
                        "C": status.phaseC.__dict__,
                        "total_power": status.total_power,
                        "temperature": status.temperature,
                        "frequency": status.frequency,
                        "energyActive": status.energyActive,
                        "energyReactive": status.energyReactive,
                        "energySym": status.energySym,
                        "relayStatus": status.relayStatus
                    }))
                time.sleep(1)
            except Exception as e:
                self.callback(json.dumps({"status": "error", "error": "PM is offline"}))
                try:
                    if self.client:
                        self.client.close()
                except:
                    pass
                self.client = None
                time.sleep(2)
        if self.client:
            self.client.close()


if __name__ == "__main__":
    def mainCb(res):
        #pass
        print(res)

    reader = WS306LSReader("/dev/ttyUSB0", mainCb)

    
    