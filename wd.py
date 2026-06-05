import os
import select 
import time
import json
import socket
import threading
import logging
import gpiod
from remoteCtrlServer.httpserver import start_server_in_thread
from remoteCtrlServer.udpService import UdpAsyncClient
from SH_DTO.gatewayDto import *
from SH_DTO.smartHomeUdpService import SmartHomeGatewayUdpClient
from SH_DTO.onlineChecker import OnlineCheckerService


_hostname = socket.gethostname()
_wd_conf_path = os.path.join(os.path.dirname(__file__), "sysConf", "wd_config.json")
with open(_wd_conf_path) as _f:
    _wd_conf = json.load(_f)[_hostname]

gatewayKotelIP       = _wd_conf["gateway_kotel_ip"]
gatewayKotelTxPort   = _wd_conf["gateway_kotel_tx_port"]
gatewayKotelRxPort   = _wd_conf["gateway_kotel_rx_port"]
maxMsgTimeTriggerVal = _wd_conf["max_msg_time_trigger_ms"]
REBOOT_DURATION      = _wd_conf["reboot_duration_sec"]
REBOOT_COOLDOWN      = _wd_conf["reboot_cooldown_sec"]
STARTUP_GRACE        = _wd_conf["startup_grace_sec"]
_ONLINE_SERVERS      = _wd_conf["online_check_servers"]

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/wd.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



ON_STATE = 0
OFF_STATE = 1

CHIP = _wd_conf["chip"]
OUTPUT_PINS = [(p["name"], p["offset"]) for p in _wd_conf["output_pins"]]
INPUT_PINS  = [(p["name"], p["offset"]) for p in _wd_conf["input_pins"]]

# button presed pin state - 
# in_lines['UNDEFINED_BTN'].get_value() == 0
# in_lines['MAINTENANCE_BTN'].get_value() == 0

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
    def __init__(self):
        self.lastGatewayReboot = 0.0
        self.lastSwitchReboot = 0.0
        self.startupTime = time.time()
        self.maintenanceMode = False
        

        self.energyMonitor = UdpAsyncClient(self)
        self.energyMonitor.startListener(5005, self.serverUdpIncomingData)
        self.gateway = GatewayDto()
        self.kotelGateway = SmartHomeGatewayUdpClient(cbFn=self.smartHomeGatewayUdpClient, gatewayIp=gatewayKotelIP, rxPort=gatewayKotelRxPort, txPort=gatewayKotelTxPort, bufferSize=1024)
        self.kotelGateway.startListener()

        self._onlineChecker = OnlineCheckerService(gateway=self.gateway, servers=_ONLINE_SERVERS)

        while True:
            # --- MAINTENANCE button (latching): pressed=0 -> maintenance ON ---
            newMaintenanceMode = (in_lines["MAINTENANCE_BTN"].get_value() == 0)
            if newMaintenanceMode != self.maintenanceMode:
                self.maintenanceMode = newMaintenanceMode
                mode_str = "ON" if self.maintenanceMode else "OFF"
                logger.info(f"Maintenance mode {mode_str}")
            out_lines["MAINTENANCE_LED"].set_value(ON_STATE if self.maintenanceMode else OFF_STATE)

            # --- Alarm / reboot logic ---
            self.MsgTimers = self.gateway.getLastUpdateIntervals()
            any_alarm = False

            if not self.maintenanceMode:
                if (self.MsgTimers["upsMsgInterval"] > maxMsgTimeTriggerVal or
                        self.MsgTimers["waterTankMsgInterval"] > maxMsgTimeTriggerVal or
                        self.MsgTimers["sensorUnitMsgInterval"] > maxMsgTimeTriggerVal or
                        self.MsgTimers["kotelMsgInterval"] > maxMsgTimeTriggerVal):
                    any_alarm = True
                    self._reboot_relay("REL_GATEWAY", "lastGatewayReboot", "gateway")

                if self.MsgTimers["serverPingInterval"] > maxMsgTimeTriggerVal:
                    any_alarm = True
                    self._reboot_relay("REL_SWITCH", "lastSwitchReboot", "switch")
                    

            out_lines["ERR_LED"].set_value(ON_STATE if any_alarm else OFF_STATE)

            time.sleep(0.5)
            print(f"{self.MsgTimers}")
            

    def _reboot_relay(self, relay_name: str, last_reboot_attr: str, label: str):
        now = time.time()
        if now - self.startupTime < STARTUP_GRACE:
            return
        if now - getattr(self, last_reboot_attr) < REBOOT_COOLDOWN:
            return
        setattr(self, last_reboot_attr, now)
        logger.warning(f"Reboot triggered: {label}. Activating {relay_name} for {REBOOT_DURATION}s; Reason walue: {self.MsgTimers}")

        def do_reboot():
            out_lines[relay_name].set_value(ON_STATE)
            time.sleep(REBOOT_DURATION)
            out_lines[relay_name].set_value(OFF_STATE)
            logger.info(f"Reboot of {label} complete ({relay_name})")

        threading.Thread(target=do_reboot, daemon=True).start()
    
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
        self.gateway.canMsgParse(can_message)
        pass

    



if __name__ == "__main__":
    #KeyboardInterrupt для коректного завершення програми при натисканні Ctrl+C
    try:
        logger.info("Starting Watchdog Service...")
        Main()
    except KeyboardInterrupt:
        logger.info("Ending Watchdog Service...")
        #release all lines on exit and set to High all outputs
        for line in out_lines.values():
            line.set_value(1)
            line.release()
        for line in in_lines.values():
            line.release()