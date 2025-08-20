from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os
import urllib.parse
import json
import random
from datetime import datetime, timedelta


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, client_instance=None, clientCbFunction=None, **kwargs):
        self.client_instance = client_instance
        self.clientCbFunction = clientCbFunction
        super().__init__(*args, **kwargs)
    def log_message(self, format, *args):
        # No logging
        return
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
    
        file_path = os.path.join('remoteCtrlServer/html', self.path[1:])  # Remove leading '/' from path and prepend 'html/'
        #print(file_path)
        if self.client_instance:
            print(self.path)


            if self.path.startswith('/cmd:'):
                
                print("Command received:", self.path)
                command = self.path[len('/cmd:'):]
                decoded_command = urllib.parse.unquote(command)
                result = self.clientCbFunction(decoded_command)
               
               
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(result.encode('utf-8'))

            elif (self.path.startswith('/exec:') ):
                command = self.path[len('/exec:'):]
                decoded_command = urllib.parse.unquote(command)
                result = self.clientCbFunction(f"exec:{decoded_command}")
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(result.encode('utf-8'))
            
            elif(self.path.startswith('/version')):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Generate random version dynamically
                major = random.randint(1, 5)  # Major version 1-5
                minor = random.randint(0, 9)  # Minor version 0-9
                version_string = f"{major}.{minor}"
                
                version_data = {
                    "version": version_string
                }
                
                self.wfile.write(json.dumps(version_data).encode('utf-8'))
                
            elif(self.path.startswith('/temperature')):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
    
                # Generate random temperature values
                rfic_temp = random.randint(15, 25)  # Temperature range 15-25°C
                vgnd = round(random.uniform(95.0, 105.0), 14)  # Voltage ground reference
                vtemp = round(random.uniform(1400.0, 1450.0), 9)  # Temperature voltage
                vtemp_ref = round(random.uniform(1.8, 2.0), 16)  # Temperature reference voltage
                
                temperature_data = {
                    "data": {
                        "rfic_temp": rfic_temp,
                        "vgnd": vgnd,
                        "vtemp": vtemp,
                        "vtemp_ref": vtemp_ref
                        },
                    "status": "ok"
                    }
                self.wfile.write(json.dumps(temperature_data).encode('utf-8'))


            elif(self.path.startswith('/idn')):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Generate random values with same structure
                serial_num = f"SF{random.randint(10000000, 99999999):08d}"
                part_num = f"GTJP{random.randint(1, 999):03d}"
                revision = f"A{random.randint(1, 99):02d}"
                
                # Random date within last year
                base_date = datetime.now()
                random_days = random.randint(0, 365)
                calib_date = (base_date - timedelta(days=random_days)).strftime("%d/%m/%Y")
                
                idn_data = {
                    "serial": serial_num,
                    "part_number": part_num,
                    "revision": revision,
                    "calib_date": calib_date
                }
                self.wfile.write(json.dumps(idn_data).encode('utf-8'))
            
            elif(self.path.startswith('/status')):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Generate random values with realistic ranges
                freq = random.randint(70000, 80000)  # Frequency range
                atten = round(random.uniform(50.0, 80.0), 3)  # Attenuation
                pout = round(random.uniform(-60.0, -40.0), 2)  # Power output
                tpc = random.randint(80, 100)  # TPC value
                output_state = random.choice([True, False])  # Random boolean
                
                status_data = {
                    "data": {
                        "calculated": {
                            "atten": atten,
                            "pout": pout
                        },
                        "raw": {
                            "freq": freq,
                            "output_state": output_state,
                            "tpc": tpc
                        }
                    },
                    "status": "ok"
                }
                
                self.wfile.write(json.dumps(status_data).encode('utf-8'))
                

            elif os.path.isfile(file_path):
                self.send_response(200)
                if file_path.endswith('.html'):
                    self.send_header('Content-type', 'text/html')
                elif file_path.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                elif file_path.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                elif file_path.endswith('.png'):
                    self.send_header('Content-type', 'image/png')
                elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                    self.send_header('Content-type', 'image/jpeg')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                with open(file_path, 'rb') as file:
                    self.wfile.write(file.read())
            
            
            
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write("File not found".encode('utf-8'))
        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write("No client instance".encode('utf-8'))



    def do_POST(self):
        if self.path == '/set_tpc':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse JSON data
                data = json.loads(post_data.decode('utf-8'))
                tpc_value = data.get('tpc')
                
                # Validate TPC value
                if tpc_value is None:
                    # Missing tpc field
                    response = {
                        "limitations": {
                            "tpc": "0-105"
                        },
                        "message": "Invalid input data",
                        "status": "nok",
                        "usage": "{\"tpc\":<ushort>}"
                    }
                elif not isinstance(tpc_value, (int, float)) or tpc_value < 0 or tpc_value > 105:
                    # TPC value out of range
                    response = {
                        "limitations": {
                            "tpc": "0-105"
                        },
                        "message": "Invalid input data",
                        "status": "nok",
                        "usage": "{\"tpc\":<ushort>}"
                    }
                else:
                    # Valid TPC value
                    response = {
                        "status": "ok"
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except json.JSONDecodeError:
                # Invalid JSON
                response = {
                    "limitations": {
                        "tpc": "0-105"
                    },
                    "message": "Invalid input data",
                    "status": "nok",
                    "usage": "{\"tpc\":<ushort>}"
                }
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/rf_output':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                state = data.get('state')
                
                if state is None or not isinstance(state, bool):
                    response = {
                        "message": "Invalid input data",
                        "status": "nok",
                        "usage": "{\"state\":<bool>}"
                    }
                else:
                    response = {
                        "status": "ok"
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except json.JSONDecodeError:
                response = {
                    "message": "Invalid JSON",
                    "status": "nok"
                }
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
        
        elif self.path == '/frequency':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                frequency = data.get('frequency')
                
                if frequency is None:
                    response = {
                        "limitations": "71000 - 86000 (MHz)",
                        "message": "Invalid input data",
                        "status": "nok",
                        "usage": "{\"frequency\":<uint>}"
                    }
                elif not isinstance(frequency, (int, float)) or frequency < 71000 or frequency > 86000:
                    response = {
                        "limitations": "71000 - 86000 (MHz)",
                        "message": "Invalid input data",
                        "status": "nok",
                        "usage": "{\"frequency\":<uint>}"
                    }
                else:
                    # Valid frequency - generate random response data
                    atten = round(random.uniform(3.0, 8.0), 3)
                    pout = round(random.uniform(3.0, 6.0), 3)
                    vco = random.randint(5, 8)
                    vtune = round(random.uniform(0.5, 1.0), 16)
                    
                    response = {
                        "data": {
                            "atten": atten,
                            "freq": frequency,
                            "pout": pout,
                            "vco": vco,
                            "vtune": vtune
                        },
                        "message": "ok",
                        "status": "ok"
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except json.JSONDecodeError:
                response = {
                    "limitations": "71000 - 86000 (MHz)",
                    "message": "Invalid input data",
                    "status": "nok",
                    "usage": "{\"frequency\":<uint>}"
                }
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
        
        elif self.path == '/set_attenuation':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                atten = data.get('atten')
                
                if atten is None or not isinstance(atten, (int, float)):
                    response = {
                        "message": "Invalid input data",
                        "status": "nok",
                        "usage": "{\"atten\":<float>}"
                    }
                elif atten > 69:
                    # Error response if attenuation > 70
                    response = {
                        "message": "Error: Attenuation out of range for the closest frequency.",
                        "status": "nok"
                    }
                else:
                    # Success response if attenuation <= 70
                    actual_atten = round(atten + random.uniform(-1.0, 1.0), 3)
                    pout = round(random.uniform(-35.0, -25.0), 3)
                    tpc = random.randint(60, 70)
                    
                    response = {
                        "data": {
                            "atten": actual_atten,
                            "pout": pout,
                            "tpc": tpc
                        },
                        "status": "ok"
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except json.JSONDecodeError:
                response = {
                    "message": "Invalid JSON",
                    "status": "nok"
                }
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
        
        elif self.path == '/upload_calib':
            content_length = int(self.headers['Content-Length'])
            content_type = self.headers.get('Content-Type', '')
            # Перевірка на multipart/form-data
            if 'multipart/form-data' in content_type and 'boundary=' in content_type:
                boundary = content_type.split("boundary=")[1].encode()
                line = self.rfile.readline()
                content_length -= len(line)
                
                if boundary in line:
                    line = self.rfile.readline()
                    content_length -= len(line)
                    # Витягуємо ім'я файлу
                    filename = line.split(b'filename=')[1].split(b'"')[1].decode()

                    # Пропускаємо заголовки
                    while line.strip():
                        line = self.rfile.readline()
                        content_length -= len(line)

                    # Зберігаємо файл
                    os.makedirs('./uploads', exist_ok=True)
                    with open(os.path.join('./uploads', filename), 'wb') as f:
                        preline = self.rfile.readline()
                        content_length -= len(preline)
                        while content_length > 0:
                            line = self.rfile.readline()
                            content_length -= len(line)
                            if boundary in line:
                                preline = preline[:-1]  # Видаляємо \r\n
                                f.write(preline)
                                break
                            else:
                                f.write(preline)
                                preline = line
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'File uploaded successfully')
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'Invalid file upload request')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid Content-Type for file upload')

class RemoteController:
    def __init__(self, port, cbFunction, main_screen_instance):
        self.port = port
        self.handler = HTTPRequestHandler
        self.server_instance = None
        self.main_screen_instance = main_screen_instance 
        self.clientCbFunction = cbFunction

    def start(self):
        server_address = ('', self.port)
        self.handler_instance = lambda *args, **kwargs: self.handler(*args, client_instance=self.main_screen_instance, clientCbFunction=self.clientCbFunction, **kwargs)
        httpd = HTTPServer(server_address, self.handler_instance)
        print(f"Serving on port {self.port}")
        self.server_instance = httpd 
        httpd.serve_forever()
    
    def shutdown(self):
        if self.server_instance:
            self.server_instance.shutdown()

def start_server_in_thread(port, cbFunction, main_screen_instance):
    server = RemoteController(port, cbFunction, main_screen_instance)
    thread = threading.Thread(target=server.start)
    thread.start()
    return server, thread