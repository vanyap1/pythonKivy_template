import time, serial, json
from threading import Thread

'''
requirements
- install apt install python3-serial
'''
class PSU():
    voltage = 0.0
    temperature = 0.0
    fanRuning = False
    safeInputState = False
    safeRelayState = False
    safeRelayTimerState = False



class OpiPSU(Thread):
    def __init__(self, ttyPort = "/dev/ttyS1", ttyBaudRate = 250000, cbErrorFn = None):
        super().__init__()
        self._running = True
        self.ttyPort = ttyPort
        self.ttyBaudRate = ttyBaudRate
        self.cbErrorFn = cbErrorFn
        self.port = None
        self.timeLastRead = 0
        self.psu = PSU()
        self.txMultiplier = 0
        self.start()

    

    def portInit(self):
        try:
            self.port = serial.Serial(self.ttyPort, self.ttyBaudRate, timeout=1)
            return True
        except Exception as e:
            print(f"Error opening serial port {self.ttyPort}: {e}")
            if self.cbErrorFn:
                self.cbErrorFn(f"Error opening serial port {self.ttyPort}: {e}")
            return False
    
    getVoltage = lambda self: self.psu.voltage
    getTemperature = lambda self: self.psu.temperature
    isFanRunning = lambda self: self.psu.fanRuning
    isSafeInput = lambda self: self.psu.safeInputState
    isSafeRelay = lambda self: self.psu.safeRelayState
    isSafeRelayTimer = lambda self: self.psu.safeRelayTimerState
    

    def isDataValid(self):
        current_time = time.time()
        if current_time - self.timeLastRead > 5:
            if self.cbErrorFn:
                self.cbErrorFn("No valid data received from PSU for over 5 seconds.")
            return False
        return True
    



    def run(self):
        while self._running:
            if self.port is None:
                if not self.portInit():
                    self.cbErrorFn(f"Retrying to open serial port {self.ttyPort} in 2 seconds...")
                    time.sleep(2)
                    continue
            if (self.txMultiplier == 10):
                self.txMultiplier = 0
                try:
                    self.port.write(b"run\n")
                except Exception as e:
                    if self.cbErrorFn:
                        self.cbErrorFn(f"Error writing to serial port {self.ttyPort}: {e}")
                    self.port = None
            else:
                self.txMultiplier += 1
            
            try:
                dat = self.port.readline()
                if dat:
                    dat = dat.decode().strip()
                    if self.parse_psu_data(dat):
                        self.timeLastRead = time.time()
                    
                    self.timeLastRead = time.time()
            except Exception as e:
                if self.cbErrorFn:
                    self.cbErrorFn(f"Error reading serial port {self.ttyPort}: {e}")
                self.port = None
            time.sleep(.1)
    
    
    def parse_psu_data(self, data_string):
        """
        Parse PSU data string like: mV:13333;degC:260;sfIn:7;fan:0;
        """
        try:
            # Розділяємо на частини
            parts = data_string.strip(';').split(';')
        
            # Перевіряємо кількість елементів
            if len(parts) != 4:
                if self.cbErrorFn:
                    self.cbErrorFn(f"Invalid data format: expected 4 elements, got {len(parts)}")
                return False
        
            # Парсимо кожну частину
            data_dict = {}
            for part in parts:
                if ':' not in part:
                    if self.cbErrorFn:
                        self.cbErrorFn(f"Invalid data format: missing ':' in {part}")
                    return False
                key, value = part.split(':', 1)
                data_dict[key] = value
        
            # Перевіряємо наявність всіх необхідних ключів
            required_keys = ['mV', 'degC', 'sfIn', 'fan']
            for key in required_keys:
                if key not in data_dict:
                    if self.cbErrorFn:
                        self.cbErrorFn(f"Missing required key: {key}")
                    return False
        
            # Парсимо значення
            self.psu.voltage = float(data_dict['mV']) / 1000.0  # конвертуємо мВ в В
            self.psu.temperature = float(data_dict['degC']) / 10.0  # конвертуємо в градуси
            self.psu.fanRuning = bool(int(data_dict['fan']))
        
            # Парсимо sfIn біти
            sf_value = int(data_dict['sfIn'])
            self.psu.safeInputState = not bool(sf_value & 0x04)  # біт 2
            self.psu.safeRelayState = not bool(sf_value & 0x02)  # біт 1
            self.psu.safeRelayTimerState = not bool(sf_value & 0x01)  # біт 0
        
            return True
        except ValueError as e:
            if self.cbErrorFn:
                self.cbErrorFn(f"Error parsing numeric values: {e}")
            return False
        except Exception as e:
            if self.cbErrorFn:
                self.cbErrorFn(f"Error parsing PSU data: {e}")
            return False


if __name__ == "__main__":
    def error_callback(msg):
        print(f"{msg}")

    psu = OpiPSU("/dev/ttyS7", 250000, error_callback)
    try:
        while True:
            if(psu.isDataValid()):
                print(f"Voltage: {psu.getVoltage():.2f} V, Temp: {psu.getTemperature():.1f} C, Fan: {psu.isFanRunning()}, SafeIn: {psu.isSafeInput()}, SafeRelay: {psu.isSafeRelay()}, SafeRelayTimer: {psu.isSafeRelayTimer()}")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    