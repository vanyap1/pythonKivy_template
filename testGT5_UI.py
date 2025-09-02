import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5 import uic
from remoteCtrlServer.udpService import UdpAsyncClient

class udpReportService():
    ip = '192.168.1.255'
    rx_port = 5006
    tx_port = 55006

class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("test.ui", self)
        self.udp_Client = UdpAsyncClient(self)
        self.udp_Client.startListener(udpReportService.rx_port, self.udpClient)
        self.counter = 0

        # Приклад: підключення кнопки
        if hasattr(self, "pushButton"):
            self.pushButton.clicked.connect(self.toggle_indicator)
        if hasattr(self, "loopButton"):
            self.loopButton.clicked.connect(self.start_counter_loop)
        # Додаємо таймер для лічильника
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_counter)

    def udpClient(self, data):
        print(f'Sending UDP data: {data}')
        if hasattr(self, "indicator"):
            self.indicator.setText(data)

    def toggle_indicator(self):
        if hasattr(self, "indicator"):
            if self.indicator.text() == 'OFF':
                self.indicator.setText('ON')
                self.indicator.setStyleSheet('background-color: green; color: white; font-size: 20px;')
            else:
                self.indicator.setText('OFF')
                self.indicator.setStyleSheet('background-color: red; color: white; font-size: 20px;')

    def start_counter_loop(self):
        self.counter = 0
        self.timer.start(500)  # 500 ms

    def update_counter(self):
        self.counter += 1
        if hasattr(self, "counter_label"):
            self.counter_label.setText(f'Counter: {self.counter}')
        if hasattr(self, "counter_field"):
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