

import os
import time
from smbus import SMBus

DEV_ADDR = 0x48
adc_channel = 0b1000010 # 0x42 (вход AIN2 + включенный DAC)
dac_channel = 0b1000000 # 0x40

bus = SMBus(1)          # 1 for RPi model B rev.2
tmp = 0

while(1):
    os.system('clear')
    print("Press Ctrl C to stop...\n")
    # read ADC value
    bus.write_byte(DEV_ADDR, adc_channel)
    bus.read_byte(DEV_ADDR)
    bus.read_byte(DEV_ADDR)
    value = bus.read_byte(DEV_ADDR)
    print 'AIN value = ' + str(value)
    # set value in DAC
    bus.write_byte_data(DEV_ADDR, dac_channel, value)
    time.sleep(0.1)