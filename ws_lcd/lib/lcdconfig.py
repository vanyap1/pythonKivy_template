# /*****************************************************************************
# * | File        :	  epdconfig.py
# * | Author      :   Waveshare team
# * | Function    :   Hardware underlying interface
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2019-06-21
# * | Info        :   
# ******************************************************************************
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import os
import sys
import time
import spidev
import logging
import numpy as np
import gpiod

class RaspberryPi:
    def __init__(self,spi=spidev.SpiDev(1,1),spi_freq=25000000):
        self.np=np
        self.INPUT = False
        self.OUTPUT = True

        self.SPEED =spi_freq

        self.gpioChip0 = gpiod.Chip("gpiochip0") # GPIOL11
        self.gpioChip1 = gpiod.Chip("gpiochip1") # GPIOG11


        self.spi_CS = self.gpioChip0.get_line(203)  # GPIOG11
        self.DC_PIN = self.gpioChip1.get_line(11)  # GPIOL11

        self.spi_CS.request(consumer="test", type=gpiod.LINE_REQ_DIR_OUT)
        self.DC_PIN.request(consumer="test", type=gpiod.LINE_REQ_DIR_OUT)

        self.bl_DutyCycle(0)
        
        #Initialize SPI
        self.spi = spi
        self.spi.open(1, 1)           # bus=3, device=0 або device=1
        self.spi.max_speed_hz = spi_freq
        self.spi.mode = 0 


    def setDC(self,dc):
        self.DC_PIN.set_value(dc)

    def gpio_mode(self,Pin,Mode,pull_up = None,active_state = True):
        return 1

    
        

    

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def gpio_pwm(self,Pin):
        return 1

    def spi_writebyte(self, data):
        if self.spi!=None :
            self.spi_CS.set_value(0)  # CS LOW
            self.spi.xfer2(data) 
            #time.sleep(0.1)
            self.spi_CS.set_value(1)  # CS HIGH    

    def bl_DutyCycle(self, duty):
        pass
        
    def bl_Frequency(self,freq):# Hz
        pass
           
    def module_init(self):
        
        return 0

    def module_exit(self):
        logging.debug("spi end")
        if self.spi!=None :
            self.spi.close()
        
        logging.debug("gpio cleanup...")
        #self.digital_write(self.RST_PIN, 1)
        #self.digital_write(self.DC_PIN, 0)   
        #self.BL_PIN.close()
        time.sleep(0.001)



'''
if os.path.exists('/sys/bus/platform/drivers/gpiomem-bcm2835'):
    implementation = RaspberryPi()

for func in [x for x in dir(implementation) if not x.startswith('_')]:
    setattr(sys.modules[__name__], func, getattr(implementation, func))
'''

### END OF FILE ###
