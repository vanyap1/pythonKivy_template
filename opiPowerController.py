import time, serial, json
from threading import Thread

'''
requirements
- install apt install python3-serial
'''
class OpiPSU(Thread):
    def __init__(self, ttyPort = "/dev/ttyS2", ttyBaudRate = 19200, cbErrorFn = None):
        super().__init__()
        self._running = True
        self.ttyPort = ttyPort
        self.ttyBaudRate = ttyBaudRate
        self.cbErrorFn = cbErrorFn
        self.port = None
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
        
    def run(self):
        while self._running:
            print("OpiPSU thread running")
            if self.port is None:
                if not self.portInit():
                    print("OpiPSU port init failed, retrying in 2s")
                    time.sleep(2)
                    continue
            try:
                #self.port.write(b"*idn?\n")
                #print("Wrote *idn?")
                dat = self.port.readline()
                print(dat)
            except Exception as e:
                if self.cbErrorFn:
                    self.cbErrorFn(f"Error reading serial port {self.ttyPort}: {e}")
                self.port = None
            time.sleep(.1)




if __name__ == "__main__":
    def error_callback(msg):
        print(f"Error: {msg}")

    psu = OpiPSU("/dev/ttyS2", 250000, error_callback)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    