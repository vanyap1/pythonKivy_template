import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import Qt, QTimer
from remoteCtrlServer.udpService import UdpAsyncClient


# pip install PyQt5 --break-system-packages
# or
# sudo apt install python3-pyqt5
# python3 qt_demo.py -platform linuxfb

class udpReportService():
    ip = '192.168.1.255'
    rx_port = 5006
    tx_port = 55006

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.udp_Client = UdpAsyncClient(self)
        self.udp_Client.startListener(udpReportService.rx_port, self.udpClient)
        self.counter = 0

        self.indicator = QLabel('OFF')
        self.indicator.setStyleSheet('background-color: black; color: white; font-size: 20px;')
        
        self.indicator2 = QLabel('OFF')
        self.indicator2.setStyleSheet('background-color: black; color: white; font-size: 20px;')
        
        self.button = QPushButton('Toggle Indicator')
        self.button.clicked.connect(self.toggle_indicator)

        self.counter_label = QLabel('Counter: 0')
        self.counter_field = QLineEdit('0')
        self.counter_field.setReadOnly(True)

        self.loop_button = QPushButton('Start Counter Loop')
        self.loop_button.clicked.connect(self.start_counter_loop)

        layout = QVBoxLayout()
        layout.addWidget(self.indicator)
        layout.addWidget(self.indicator2)
        layout.addWidget(self.button)
        layout.addWidget(self.counter_label)
        layout.addWidget(self.counter_field)
        layout.addWidget(self.loop_button)
        self.setLayout(layout)

        
        
    def udpClient(self, data):
        print(f'Sending UDP data: {data}')
        self.indicator.setText(data)


    def toggle_indicator(self):
        if self.indicator.text() == 'OFF':
            self.indicator.setText('ON')
            self.indicator.setStyleSheet('background-color: green; color: white; font-size: 20px;')
        else:
            self.indicator.setText('OFF')
            self.indicator.setStyleSheet('background-color: red; color: white; font-size: 20px;')

    def start_counter_loop(self):
        self.counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_counter)
        self.timer.start(500)  # 500 ms

    def update_counter(self):
        self.counter += 1
        self.counter_label.setText(f'Counter: {self.counter}')
        self.counter_field.setText(str(self.counter))
        print(f"Counter value: {self.counter}")
        if self.counter >= 10:
            self.timer.stop()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.setWindowTitle('Qt5 Test Project')
    window.show()
    sys.exit(app.exec_())