import spidev
import time
import gpiod


'''

sudo apt install python3-spidev

'''
gpioChip0 = gpiod.Chip("gpiochip0") # GPIOL11
gpioChip1 = gpiod.Chip("gpiochip1") # GPIOG11


spi_CS = gpioChip0.get_line(203)  # GPIOG11
spi_DC = gpioChip1.get_line(11)  # GPIOL11

spi_CS.request(consumer="test", type=gpiod.LINE_REQ_DIR_OUT)
spi_DC.request(consumer="test", type=gpiod.LINE_REQ_DIR_OUT)

def spi_write(bus, device, data, speed_hz=500000):
    spi = spidev.SpiDev()
    spi.open(bus, device)           # bus=3, device=0 або device=1
    spi.max_speed_hz = speed_hz
    spi.mode = 0                   # SPI mode 0 (CPOL=0, CPHA=0), при потребі змінити
    try:
        print(f"Writing to SPI bus {bus} device {device}: {data}")
        resp = spi.xfer2(data)     # одночасно записує і читає, resp - прочитані байти
        print(f"Received: {resp}")
    finally:
        spi.close()

if __name__ == "__main__":
    # Приклад даних для запису (масив байтів)
    
    data_to_write = [0x01, 0x02, 0x03, 0x04, 0x05]

    # Записуємо через CS0 (/dev/spidev3.0)
    while True:
        spi_DC.set_value(1)
        time.sleep(0.1)
        spi_DC.set_value(0)

        spi_write(1, 1, data_to_write)
        time.sleep(0.1)


    # Записуємо через CS1 (/dev/spidev3.1)
    #spi_write(3, 1, data_to_write)
