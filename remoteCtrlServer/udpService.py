import socket
import json
import threading

class UdpAsyncClient(threading.Thread):
    def __init__(self, mainLoopInstance, cbFn, port=5005, bufferSize=1024):
        self.mainLoop = mainLoopInstance
        self.parrentCb = cbFn 
        self.port = port
        self.bufferSize = bufferSize
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(('', self.port))
        threading.Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                data, _ = self.sock.recvfrom(self.bufferSize)
                message = data.decode('utf-8')
                
                try:
                    json_data = json.loads(message)
                    self.parrentCb(json_data)
                except json.JSONDecodeError as e:
                    self.parrentCb("err") 
                
            except Exception as e:
                pass
                #self.parrentCb("err") 
    
    def send_bytes(self, data, ip, port):
        try:
            self.sock.sendto(data, (ip, port))
        except Exception as e:
            print(f"Error sending bytes: {e}")

    def send_text(self, text, ip, port):
        try:
            data = text.encode('utf-8')
            self.send_bytes(data, ip, port)
        except Exception as e:
            print(f"Error sending text: {e}")