import os
import subprocess
import time
import re
import json
import glob
from threading import Thread
from smbus2 import SMBus, i2c_msg
import platform
import subprocess
import shlex



from remoteCtrlServer.httpserver import start_server_in_thread
remCtrlPort = 8080
NOTES_FILE = "notes.txt"
i2cBus = 2


class Main:
    def __init__(self):
        print("Run app...")
        self.server, self.server_thread = start_server_in_thread(remCtrlPort, self.remCtrlCB, self) #Start remote control server
        self.bus = SMBus(i2cBus)
        self.notes = "empty"
        self.run()
    def run(self):
        while(True):
            time.sleep(1)
            pass
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


    def remCtrlCB(self, arg):                           #Remote control callback
        #['', 'slot', '0', 'status']
        if(not arg.startswith("exec")):
            request = arg.split("/")
        else:
            request = [arg]                       #Split request to array
        print("CB arg-", request )
        if request[0].startswith("i2c-write"):
            cmdStr = request[0].split(";")
            print("cmdStr-", cmdStr)
            if len(cmdStr) < 5:
                return "Error: Invalid command"
            if cmdStr[4] == "":
                return "Error: Empty byte array"
    
            try:
                addr = int(cmdStr[1], 16)  # Device address
                reg = int(cmdStr[2], 16)   # Register address
                hex_string = cmdStr[4]
                print("Data bytes-", hex_string)
                data_bytes = bytes.fromhex(hex_string)

                # Build the byte array
                byte_array = bytes([reg]) + data_bytes
                print("Byte array-", byte_array)
            except ValueError as e:
                return "Error converting to byte array"
    
            try:
                write = i2c_msg.write(addr, byte_array)
                self.bus.i2c_rdwr(write)
                return "Write successful"
            except Exception as e:
                print("Error writing to i2c:", e)
                return "Error writing to i2c"

        if request[0].startswith("i2c-read"):
            cmdStr = request[0].split(";")
            print("cmdStr-", cmdStr)
            
            try:
                addr = int(cmdStr[1], 16)
                reg = int(cmdStr[2], 16)
                #read = i2c_msg.read(addr, int(cmdStr[2]))
                #self.bus.i2c_rdwr(read)
                print("addr-", addr)
                print("reg-" , reg)
                print("len-" , cmdStr[3])    
                read = self.bus.read_i2c_block_data(addr, reg, int(cmdStr[3]))
                print("Read-", read)

                return " ".join(f"{byte:02X}" for byte in list(read))
            except Exception as e:
                return ("Error reading from i2c")
        if request[0].startswith("exec"):
            print(f"Executing system command: {request[0]}")
            return self.execute_system_command(request[0].split("=")[1])
            

        if request[0].startswith("getNotes"):
            self.notes = self.load_notes_from_file()
            return self.notes

        if request[0].startswith("saveNotes"):
            notesContent = request[0].replace("saveNotes:", "", 1)
            self.save_notes_to_file(notesContent)
            return "OK"

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


if __name__ == "__main__":
    Main()