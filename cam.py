
import subprocess

import time
import shlex
import pty
import os, socket, re
import random
import json
import platform
import subprocess
import shlex
from urllib import request
from remoteCtrlServer.httpserver import start_server_in_thread
import serial

NOTES_FILE = "notesCam.txt"
CAM_COORDINATES_FILE = "cam_coordinates.json"
xMax = 10000
xMin = 0
yMax = 10000
yMin = 0



cameraPositions = {
    "0": (3700, 2120),
    "1": (0, 0),
    "2": (7400, 0),
    "3": (0, 4240),
    "4": (7400, 4240),
    "5": (3700, 2120),
    "6": (0, 0),
    "7": (7400, 0),
    "8": (0, 4240)
}



# Camera center positions:
# X 3700
# Y 2120

class Main:
    def __init__(self):
        self.start()
        
    
    def start(self):
        if os.path.exists(CAM_COORDINATES_FILE):
            try:
                with open(CAM_COORDINATES_FILE, "r", encoding="utf-8") as file:
                    loaded_data = json.load(file)
                    # Конвертуємо масиви з JSON назад у кортежі
                    cameraPositions = {key: tuple(value) if isinstance(value, list) else value 
                                   for key, value in loaded_data.items()}
                    print("Loaded camera coordinates:", cameraPositions)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading camera coordinates: {e}. Using default positions.")
                self._save_camera_positions()
        else:
            print("Camera coordinates file not found. Creating with default positions.")
            self._save_camera_positions()

        
        self.server, self.server_thread = start_server_in_thread(8080, self.httpServerCbFn, self)
        self.camXpos = 0
        self.camYpos = 1000
        self.home = False
        self.setMemFlg = False
        self.ser = serial.Serial(port="/dev/ttyS1",baudrate=115200, timeout=1)
        
        print("Camera houming controller running...")
        self.ser.write("G28\n".encode())
        #time.sleep(5)
        print("Camera run to center position...")
        self.camXpos = 3700
        self.camYpos = 2120
        self.ser.write(f"G1 X{self.camXpos} Y{self.camYpos}\n".encode())
        self.home = True
        
        while True:
            #if (self.home):   
            #    print(f"G1 X{self.camXpos} Y{self.camYpos}")
            time.sleep(0.25)


    
    def _save_camera_positions(self):
        """Зберігає поточні позиції камери у файл."""
        with open(CAM_COORDINATES_FILE, "w", encoding="utf-8") as file:
            json.dump(cameraPositions, file, indent=4, ensure_ascii=False)
            print("Saved camera coordinates to file.")
    
    def setMemory(self, slotNum):
        print("Set memory:", slotNum)
        cameraPositions[slotNum] = (self.camXpos, self.camYpos)
        self._save_camera_positions()
        return "Complete. Saved position: " + str(cameraPositions[slotNum])



    def httpServerCbFn(self, arg):
        #['', 'slot', '0', 'status']

        if(not arg.startswith("exec")):
            request = arg.split("/")
        else:
            request = [arg]                       #Split request to array
        print("CB arg-", request )
        if(request[0] == "test"):
            return self.servReport.text
        
        elif(request[0].startswith("mem")):
            memSlot = request[0].split(":")[1]
            if (self.setMemFlg):
                self.setMemory(memSlot)
                self.setMemFlg = False
                return f"Memory slot {memSlot} saved"
            else:

                pos = cameraPositions.get(memSlot, (0,0))
                print("Moving to position:", pos)
                self.camXpos, self.camYpos = pos
                self.ser.write(f"G1 X{self.camXpos} Y{self.camYpos}\n".encode())
                return f"Camera moved to memory slot {memSlot} position: X={self.camXpos}, Y={self.camYpos}"
            
        elif(request[0].startswith("setMem")):
            self.setMemFlg = not self.setMemFlg
            if (self.setMemFlg):
                return "Select memory slot to save current position"
            else:
                return "Memory saving cancelled"

        elif(request[0].startswith("X+")):
            if self.camXpos + int(request[0].replace("X+", "", 1)) <= xMax:
                self.camXpos += int(request[0].replace("X+", "", 1))
                self.ser.write(f"G1 X{self.camXpos} Y{self.camYpos}\n".encode())
            return f"X position: {self.camXpos}, Y position: {self.camYpos}"
        elif(request[0].startswith("X-")):
            if self.camXpos - int(request[0].replace("X-", "", 1)) >= xMin:
                self.camXpos -= int(request[0].replace("X-", "", 1))
                self.ser.write(f"G1 X{self.camXpos} Y{self.camYpos}\n".encode())
            return f"X position: {self.camXpos}, Y position: {self.camYpos}"
        elif(request[0].startswith("Y+")):
            if self.camYpos + int(request[0].replace("Y+", "", 1)) <= yMax:
                self.camYpos += int(request[0].replace("Y+", "", 1))
                self.ser.write(f"G1 X{self.camXpos} Y{self.camYpos}\n".encode())
            return f"X position: {self.camXpos}, Y position: {self.camYpos}"
        elif(request[0].startswith("Y-")):
            if self.camYpos - int(request[0].replace("Y-", "", 1)) >= yMin:
                self.camYpos -= int(request[0].replace("Y-", "", 1))
                self.ser.write(f"G1 X{self.camXpos} Y{self.camYpos}\n".encode())
            return f"X position: {self.camXpos}, Y position: {self.camYpos}"
        elif(request[0] == "HOME"):
            self.home = False
            self.camXpos, self.camYpos = 0, 0
            self.ser.write("G28\n".encode())
            time.sleep(5)
            self.home = True
            return f"X position: {self.camXpos}, Y position: {self.camYpos}"


        elif(request[0] == "stop"):
             self.backProc.stopProc()
             #self.backProc.setCmd("stop")
             return self.backProc.getStatus()
        elif request[0].startswith("getNotes"):
            self.notes = self.load_notes_from_file()
            return self.notes

        elif request[0].startswith("saveNotes"):
            notesContent = request[0].replace("saveNotes:", "", 1)
            self.save_notes_to_file(notesContent)
            return "OK"
        elif request[0].startswith("exec"):
            try:
                return self.execute_system_command(request[0].split(":")[1])
            except Exception as e:
                return f"Error executing command: {str(e)}"
    
        return "ERR 400: Undefined instruction"
    
    def execute_system_command(self, command):
        '''
        Runs a system command on Linux.
        '''
        if platform.system().lower() != 'linux':
            return "Error: Commands can only be executed on Linux systems"
        if not command or command.strip() == "":
            return "Error: Empty command"
        forbidden_commands = ['rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs', 'dd', 'sudo', 'su']
        first_word = command.strip().split()[0]
        if first_word in forbidden_commands:
            return f"Error: Command '{first_word}' is forbidden for security reasons"
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            output = ""
            if result.stdout:
                output += f"{result.stdout}\n"
            if result.stderr:
                output += f"{result.stderr}\n"
            output += f"Return code: {result.returncode}"
            return output
        except subprocess.TimeoutExpired:
            return "Error: Command timed out (30 seconds limit)"
        except FileNotFoundError:
            return f"Error: Command '{first_word}' not found"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def load_notes_from_file(self):
        """Завантажує нотатки з файлу, якщо файл існує."""
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r", encoding="utf-8") as file:
                return file.read()
        return "empty"

    def save_notes_to_file(self, notes):
        """Зберігає нотатки у файл."""
        with open(NOTES_FILE, "w", encoding="utf-8") as file:
            file.write(notes)

if __name__ == '__main__':
    Main()
