import threading
import socket
import time


GOOGLE_DNS = '8.8.8.8'
# Порти для перевірки (перший що відповів — хост онлайн)
CHECK_PORTS = [53, 80, 443, 22]


class OnlineCheckerService:
    def __init__(self, gateway, servers):
        self.gateway = gateway

        # Flatten: підтримує список IP або список sets/lists
        self.servers = []
        for item in servers:
            if isinstance(item, (set, list, tuple)):
                self.servers.extend(item)
            else:
                self.servers.append(item)

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _is_online(self, host) -> bool:
        for port in CHECK_PORTS:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.0)
                    s.connect((host, port))
                    return True
            except ConnectionRefusedError:
                # Порт закритий, але хост відповідає — значить онлайн
                return True
            except (socket.timeout, OSError):
                continue
        return False

    def _run(self):
        while True:
            for server in self.servers:
                try:
                    if self._is_online(server):
                        ts = int(time.time() * 1000)
                        if server == GOOGLE_DNS:
                            self.gateway.googlePingLastTimestamp = ts
                        else:
                            self.gateway.serverLastPingTimestamp = ts
                except Exception as e:
                    print(f"OnlineChecker error for {server}: {e}")
            time.sleep(5)
