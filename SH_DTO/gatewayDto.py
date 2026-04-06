from datetime import datetime
import struct
from typing import List

class GatewayDto:
    def __init__(self):
        # Основні дані
        self.digitalIn: List[bool] = [False, False]
        self.digitalOut: List[bool] = [False, False]
        
        # Timestamps
        self.upsMsgTimestamp: int = 0
        self.waterTankMsgTimestamp: int = 0
        self.sensorUnitMsgTimestamp: int = 0
        self.kotelMsgTimestamp: int = 0
        
        # Intervals
        self.upsMsgInterval: int = 0
        self.waterTankMsgInterval: int = 0
        self.sensorUnitMsgInterval: int = 0
        self.kotelMsgInterval: int = 0
        
        # Sensor unit section
        self.mainCirkulationPumpTemp: float = 0
        self.boilerTemperature: float = 0
        self.solarCollectorTemp: float = 0
        self.coolantTemperature: float = 0
        self.lightLevel: float = 0
        self.auxAdcValue: float = 0
        
        # UPS section
        self.batVoltage: float = 0.0
        self.batCurrent: float = 0.0
        self.batEnergyf: float = 0.0
        self.batEnergy: int = 0
        self.currentState: int = 0
        self.currentSource: str = "AC"
        
        # Circulation Pump
        self.pumpCurrent: int = 0
        self.pumpMode: str = "OFF"
        
        # Water tank values
        self.waterTankDIN: int = 0
        self.waterTankDOUT: int = 0
        self.waterPress: int = 0
        self.waterPressLoLim: int = 0
        self.waterPressDelta: int = 0
        self.waterLevel: int = 0
        
        # Kotel values
        self.kotelActTemp: float = 0.0
        self.kotelStatus: int = 0
        self.kotelTemLo: int = 0
        self.kotelTemHi: int = 0
        self.kotelTemRun: int = 0
        self.kotelTemStop: int = 0
        self.kotelTemDelta: int = 0

        # Main Inverter values
        self.inverterPower: float = 0.0 
        self.inverterSoc: int = 0
        self.inverterTemp: int = 0
        self.inverterStatus: int = 0
        self.inverterCurrent: float = 0.0
        self.inverterVoltage: float = 0.0


    def canMsgParse(self, can_message):
        # Відомі CAN ID
        known_ids = [0x069, 0x247, 0x033, 0x043, 0x301, 0x070, 0x080]
        if(can_message.can_id == 0x080):
            import time
            self.sensorUnitMsgTimestamp = int(time.time() * 1000)

            # Parse as 4 signed 16-bit integers (little-endian)
            temps = struct.unpack('<hhhh', bytes(can_message.data[:8]))

            # Divide by 10 to get actual temperature in Celsius
            self.mainCirkulationPumpTemp = temps[0] / 10.0
            self.boilerTemperature = temps[1] / 10.0
            self.coolantTemperature = temps[2] / 10.0
            self.solarCollectorTemp = temps[3] / 10.0

        if(can_message.can_id == 0x069):
            import time
            current_time = int(time.time() * 1000)
    
            # Якщо 0x080 не приходили >10 сек або взагалі не було, беремо температури з 0x069
            if self.sensorUnitMsgTimestamp == 0 or (current_time - self.sensorUnitMsgTimestamp) > 10000:
                if self.sensorUnitMsgTimestamp != 0:  # Якщо були раніше
                    print(f"Warning: 0x080 stale ({(current_time - self.sensorUnitMsgTimestamp) / 1000:.1f}s), using 0x069 fallback")
        
                self.sensorUnitMsgTimestamp = current_time
                # Табличні температури - байти як є (0-255)
                self.mainCirkulationPumpTemp = float(can_message.data[0])
                self.boilerTemperature = float(can_message.data[1])
                self.coolantTemperature = float(can_message.data[2])
                self.solarCollectorTemp = float(can_message.data[3])
        
            # lightLevel і auxAdcValue завжди оновлюються з 0x069
            self.lightLevel = can_message.data[4]
            self.auxAdcValue = can_message.data[5]
    
        elif(can_message.can_id == 0x247):
            import time
            self.kotelMsgTimestamp = int(time.time() * 1000)
            self.kotelStatus = can_message.data[0]
            self.kotelActTemp = (can_message.data[1] << 8) | can_message.data[2]
            self.kotelTemHi = can_message.data[3]
            self.kotelTemLo = can_message.data[4]
            self.kotelTemRun = can_message.data[5]
            self.kotelTemStop = can_message.data[6]
            self.kotelTemDelta = can_message.data[7]
            #print(f"Kotel: Status={self.kotelStatus}, ActTemp={self.kotelActTemp}, TemHi={self.kotelTemHi}, TemLo={self.kotelTemLo}, TemRun={self.kotelTemRun}, TemStop={self.kotelTemStop}, TemDelta={self.kotelTemDelta}")
    
        elif(can_message.can_id == 0x033):
            import time
            self.upsMsgTimestamp = int(time.time() * 1000)
            self.batVoltage = can_message.data[0] / 10.0
            self.batCurrent = (can_message.data[1] << 8) | can_message.data[2] 
            if self.batCurrent > 32767:
                self.batCurrent -= 65536
            self.batEnergy = (can_message.data[3] << 24) | (can_message.data[4] << 16) | (can_message.data[5] << 8) | can_message.data[6]
            self.batEnergyf = self.batEnergy / 1000.0
            self.currentSource = "DC" if self.batCurrent <= 0 else "AC"
            self.currentState = can_message.data[7]
            #print(f"UPS: Voltage={self.batVoltage}, Current={self.batCurrent}, Energyf={self.batEnergyf}, Energy={self.batEnergy}, Source={self.currentSource}, State={self.currentState}")
    
        elif(can_message.can_id == 0x043):
            self.pumpCurrent = can_message.data[0]
            #print(f"Pump: Current={self.pumpCurrent}")
    
        elif(can_message.can_id == 0x301):
            import time
            self.waterTankMsgTimestamp = int(time.time() * 1000)  # timestamp в мілісекундах
            self.waterTankDIN = can_message.data[0]
            self.waterTankDOUT = can_message.data[1]
            self.waterPress = (can_message.data[2] << 8) | can_message.data[3]
            self.waterPressLoLim = (can_message.data[4] << 8) | can_message.data[5]
            self.waterPressDelta = can_message.data[6]
            self.waterLevel = can_message.data[7]

        elif(can_message.can_id == 0x070):
            import time
            from datetime import datetime
    
            # Декодування цифрових входів та виходів
            digital_io_byte = can_message.data[0]
            self.digitalIn[0] = bool(digital_io_byte & 0x01)  # біт 0
            self.digitalIn[1] = bool(digital_io_byte & 0x02)  # біт 1
    
            digital_out_byte = can_message.data[1]
            self.digitalOut[0] = bool(digital_out_byte & 0x01)  # біт 0
            self.digitalOut[1] = bool(digital_out_byte & 0x02)  # біт 1
    
            # Декодування RTC даних
            rtc_date = can_message.data[2]
            rtc_month = can_message.data[3]
            rtc_year = can_message.data[4] + 2000  # припускаємо, що рік передається як offset від 2000
            rtc_hour = can_message.data[5]
            rtc_minute = can_message.data[6]
            rtc_second = can_message.data[7]
    
            try:
                # Створюємо datetime об'єкт з RTC даних
                rtc_datetime = datetime(rtc_year, rtc_month, rtc_date, rtc_hour, rtc_minute, rtc_second)
                # Конвертуємо у timestamp в мілісекундах
                self.rtcTimestamp = int(rtc_datetime.timestamp() * 1000)
                self.rtcDateTimeStr = rtc_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Якщо дата некоректна, використовуємо поточний час
                self.rtcTimestamp = int(time.time() * 1000)
                self.rtcDateTimeStr = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"Invalid RTC data: {rtc_year}-{rtc_month}-{rtc_date} {rtc_hour}:{rtc_minute}:{rtc_second}")
    
            #print(f"RTC: DIN={self.digitalIn}, DOUT={self.digitalOut}, DateTime={self.rtcDateTimeStr}")

        else:
            # Логування невідомих CAN ID у файл
            self.logUnknownCanId(can_message)

    def logUnknownCanId(self, can_message):
        """Записує невідомі CAN повідомлення у файл"""
        import time
        from datetime import datetime
    
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            data_hex = ' '.join([f'{byte:02X}' for byte in can_message.data])
        
            log_entry = f"{timestamp} | ID: 0x{can_message.can_id:03X} | Data: {data_hex}\n"
        
            with open('unknown_can_messages.log', 'a', encoding='utf-8') as f:
                f.write(log_entry)
                f.flush()
        except Exception as e:
            print(f"Error logging unknown CAN message: {e}")



    def generateKotelUpdateQuery(self) -> str:
        """
        Генерує SQL-запит UPDATE для таблиці kotel на основі поточних даних
        """
        import time
        from datetime import datetime
    
        # Отримуємо поточний час
        now = datetime.now()
        datestamp = now.strftime('%Y-%m-%d')
        timestamp = now.strftime('%H:%M:%S')
    
        # Визначаємо джерело живлення як число (0 = AC, 1 = DC)
        pw_source = 1 if self.currentSource == "DC" else 0
    
        query = f"""UPDATE kotel SET 
            temperature = '{self.kotelActTemp/10}',
            date = '{datestamp}',
            time = '{timestamp}',
            battery_u = '{self.batVoltage*1000}',
            battery_i = '{self.batCurrent}',
            battery_p = '{self.batEnergy}',
            pw_source = '{self.currentSource}',
            pump = '{self.pumpCurrent}',
            tZone1 = '{self.boilerTemperature*10}',
            tZone2 = '{self.coolantTemperature*10}',
            tZone3 = '{self.solarCollectorTemp*10}',
            lightLevel = '{self.lightLevel}',
            adcCh5 = '{self.auxAdcValue}'"""
        return query
    def generateKotelLogInsertQuery(self, room_temp: int = 0, door_temp: str = "+000") -> str:
        """
        Генерує SQL-запит INSERT для таблиці kotel_log на основі поточних даних
    
        Args:
            room_temp: температура кімнати (додатковий параметр)
            door_temp: температура дверей (додатковий параметр)
        """
        from datetime import datetime
    
        # Отримуємо поточний час
        now = datetime.now()
        datestamp = now.strftime('%Y-%m-%d')
        timestamp = now.strftime('%H:%M:%S')
    
        query = f"""INSERT INTO kotel_log (date, time, temperature, battery_u, battery_i, battery_p, pump, room_temp, door_temp, tZone1, tZone2, tZone3, lightLevel, adcCh5) 
        VALUES ('{datestamp}', '{timestamp}', '{self.kotelActTemp/10}', '{self.batVoltage*1000}', '{self.batCurrent}', '{self.batEnergy}', '{self.pumpCurrent}', '{int(room_temp)}', '{door_temp}', '{self.boilerTemperature*10}', '{self.coolantTemperature*10}', '{self.solarCollectorTemp*10}', '{self.lightLevel}', '{self.auxAdcValue}')"""
    
        return query
    def generateWaterInsertQuery(self) -> str:
        """
        Генерує SQL-запит INSERT для таблиці water на основі поточних даних
        """
        from datetime import datetime
    
        # Отримуємо поточний час
        now = datetime.now()
        datestamp = now.strftime('%Y-%m-%d')
        timestamp = now.strftime('%H:%M:%S')
    
        query = f"""INSERT INTO water (date, time, water_pressure, water_press_lim, water_press_delta, water_tank_level, data_valid) 
        VALUES ('{datestamp}', '{timestamp}', '{self.waterPress}', '{self.waterPressLoLim}', '{self.waterPressDelta}', '{self.waterLevel}', '1')"""
    
        return query
    def updateTimestamp(self):
        """Оновити поточний timestamp
            + 247 kotel
            301 water Tank
            043 pump mode
            033 ups
            + 069 sensor unit
            int(time.time() * 1000)
        """
        pass
        
    
    def setDigitalIn(self, index: int, value: bool):
        """Встановити значення digitalIn[index]"""
        if 0 <= index < len(self.digitalIn):
            self.digitalIn[index] = value
    
    def setDigitalOut(self, index: int, value: bool):
        """Встановити значення digitalOut[index]"""
        if 0 <= index < len(self.digitalOut):
            self.digitalOut[index] = value
    
    def getAll(self) -> dict:
        """Повернути всі дані у вигляді словника"""
        return {
            "timeStamp": self.timeStamp,
            "digitalIn": self.digitalIn,
            "digitalOut": self.digitalOut,
            "upsMsgTimestamp": self.upsMsgTimestamp,
            "waterTankMsgTimestamp": self.waterTankMsgTimestamp,
            "sensorUnitMsgTimestamp": self.sensorUnitMsgTimestamp,
            "kotelMsgTimestamp": self.kotelMsgTimestamp,
            "upsMsgInterval": self.upsMsgInterval,
            "waterTankMsgInterval": self.waterTankMsgInterval,
            "sensorUnitMsgInterval": self.sensorUnitMsgInterval,
            "kotelMsgInterval": self.kotelMsgInterval,
            "boilerTemperature": self.boilerTemperature,
            "solarCollectorTemp": self.solarCollectorTemp,
            "coolantTemperature": self.coolantTemperature,
            "lightLevel": self.lightLevel,
            "auxAdcValue": self.auxAdcValue,
            "batVoltage": self.batVoltage,
            "batCurrent": self.batCurrent,
            "batEnergyf": self.batEnergyf,
            "batEnergy": self.batEnergy,
            "currentState": self.currentState,
            "currentSource": self.currentSource,
            "pumpCurrent": self.pumpCurrent,
            "pumpMode": self.pumpMode,
            "waterTankDIN": self.waterTankDIN,
            "waterTankDOUT": self.waterTankDOUT,
            "waterPress": self.waterPress,
            "waterPressLoLim": self.waterPressLoLim,
            "waterPressDelta": self.waterPressDelta,
            "waterLevel": self.waterLevel,
            "kotelActTemp": self.kotelActTemp,
            "kotelStatus": self.kotelStatus,
            "kotelTemLo": self.kotelTemLo,
            "kotelTemHi": self.kotelTemHi,
            "kotelTemRun": self.kotelTemRun,
            "kotelTemStop": self.kotelTemStop,
            "kotelTemDelta": self.kotelTemDelta
        }
    
    def __str__(self) -> str:
        """Строкове представлення об'єкта"""
        return f"GatewayDto(timestamp={self.timeStamp}, batVoltage={self.batVoltage}, kotelStatus={self.kotelStatus})"