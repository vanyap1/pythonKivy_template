import spidev
import time
'''

sudo apt install python3-spidev

'''
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
        spi_write(3, 0, data_to_write)
        time.sleep(0.1)


    # Записуємо через CS1 (/dev/spidev3.1)
    #spi_write(3, 1, data_to_write)
