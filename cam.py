
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
xMax = 10000
xMin = 0
yMax = 10000
yMin = 0


class Main:
    def __init__(self):
        self.start()
        
    
    def start(self):
        self.server, self.server_thread = start_server_in_thread(8080, self.httpServerCbFn, self)
        self.camXpos = 0
        self.camYpos = 1000
        self.home = False
        self.ser = serial.Serial(port="/dev/ttyS1",baudrate=115200, timeout=1)
        while True:
            #print("cam running...")
            if (self.home):   
                #self.ser.write(f"G1 X{self.camXpos} Y{self.camYpos}\n".encode())
                #response = self.ser.readline().decode().strip()
                print(f"G1 X{self.camXpos} Y{self.camYpos}\n")
            time.sleep(1)




    def httpServerCbFn(self, arg):
        #['', 'slot', '0', 'status']

        if(not arg.startswith("exec")):
            request = arg.split("/")
        else:
            request = [arg]                       #Split request to array
        print("CB arg-", request )
        if(request[0] == "test"):
            return self.servReport.text
        
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