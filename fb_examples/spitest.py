#!/usr/bin/env python3
import spidev
import gpiod
import time

# GPIO chip select: PA13 = chip 0, line 13
CHIP_NAME = "gpiochip0"  # Для основного GPIO контролера (pio)
CS_LINE = 13  # PA13

class SPIWithGPIOCS:
    def __init__(self, bus=1, device=1, cs_chip="gpiochip0", cs_line=13, max_speed=10000000):
        # Ініціалізація SPI
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = max_speed
        self.spi.mode = 0  # CPOL=0, CPHA=0
        
        # Ініціалізація GPIO для CS
        self.chip = gpiod.Chip(cs_chip)
        self.cs_line = self.chip.get_line(cs_line)
        self.cs_line.request(consumer="spi_cs", type=gpiod.LINE_REQ_DIR_OUT)
        
        # CS неактивний (HIGH)
        self.cs_line.set_value(1)
    
    def transfer(self, data):
        """Передача даних з контролем CS"""
        # CS активний (LOW)
        self.cs_line.set_value(0)
        time.sleep(0.00001)  # 10us delay
        
        # Передача даних
        result = self.spi.xfer2(data)
        
        # CS неактивний (HIGH)
        time.sleep(0.00001)
        self.cs_line.set_value(1)
        
        return result
    
    def close(self):
        """Закрити SPI та GPIO"""
        self.cs_line.set_value(1)  # CS HIGH перед закриттям
        self.cs_line.release()
        self.chip.close()
        self.spi.close()

# Приклад використання
if __name__ == "__main__":
    spi = SPIWithGPIOCS(bus=1, device=0, cs_chip="gpiochip0", cs_line=13)
    
    try:
        # Приклад передачі
        tx_data = [0x01, 0x02, 0x03, 0x04]
        rx_data = spi.transfer(tx_data)
        print(f"TX: {[hex(x) for x in tx_data]}")
        print(f"RX: {[hex(x) for x in rx_data]}")
        
    finally:
        spi.close()