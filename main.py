import subprocess

import time
import shlex
import pty
import os, socket, re
import random
from urllib import request
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen , ScreenManager
from threading import Thread
from kivy.clock import Clock
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from datetime import datetime, date, timedelta
from collections import namedtuple
from kivy.uix.popup import Popup
from kivy.config import Config
from kivy.core.window import Window
from kivy.factory import Factory

from remoteCtrlServer.httpserver import start_server_in_thread
from remoteCtrlServer.udpService import UdpAsyncClient
from pyIOdriver.i2c_gpio import  I2CGPIOController, IO, DIR, Expander

from analogMeterWidget.analogGaugeWidget import analog_meter

remCtrlPort = 8080
sysI2cBus = 0
expanderAddr = 0x20

class udpReportService():
    ip = '192.168.1.255'
    port = 55005



class MainScreen(FloatLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.background_image = Image(source='images/bg_d.jpg', size=self.size)
        self.add_widget(self.background_image)
        
        self.analog_display = analog_meter(do_rotation=False, do_scale=False, do_translation=False, value=0, pos=(0, 980))
        self.add_widget(self.analog_display)


        ## GPIO controller init 
        self.gpio = I2CGPIOController(sysI2cBus)
        self.gpioExpander = Expander(Expander.PCA9535)
        self.gpioExpander.addr = expanderAddr

        self.okLED =IO(expander = self.gpioExpander, portNum = 1, pinNum = 3, pinDir=DIR.OUTPUT)
        self.busyLED =IO(expander = self.gpioExpander, portNum = 1, pinNum = 4, pinDir=DIR.OUTPUT)
        self.errLED =IO(expander = self.gpioExpander, portNum = 1, pinNum = 5, pinDir=DIR.OUTPUT)
        self.jigSw = IO(expander = self.gpioExpander, portNum = 1, pinNum = 0, pinDir=DIR.INPUT)
        
        self.gpio.addExpandersInfo(self.gpioExpander)
        
        self.gpio.setPinDirection(self.jigSw, False)
        self.gpio.setPinDirection(self.busyLED, True)
        self.gpio.setPinDirection(self.okLED, False)
        self.gpio.setPinDirection(self.errLED, False)
        
        self.gpio.startController()


        ## Server start
        self.server, self.server_thread = start_server_in_thread(remCtrlPort, self.remCtrlCB, self)
        self.udpClient = UdpAsyncClient(self, self.serverUdpIncomingData, 5005)
        Clock.schedule_interval(lambda dt: self.update_time(), 1)

        
        self.clock = Label(text='[color=ffffff]22:30:38[/color]', markup = True, font_size=100, pos=(-600, 500) , font_name='fonts/hemi_head_bd_it.ttf')
        self.add_widget(self.clock)

        self.servReport = Label(text='[color=00ffcc]No data[/color]', markup=True, font_size=24, pos=(-200, 400), font_name='fonts/hemi_head_bd_it.ttf', halign='left')
        self.add_widget(self.servReport)


        self.button1 = Button(text='', size_hint=(None, None), size=(192, 192), pos_hint={'center_x': .3, 'center_y': .5},
                              background_normal='images/switch3_off.png', background_down='images/switch3.png')
        self.button1.bind(on_release=lambda instance: self.on_button_release("Message from Button 1"))
        self.add_widget(self.button1)

        self.button2 = Button(text='', size_hint=(None, None), size=(192, 192), pos_hint={'center_x': .7, 'center_y': .5},
                              background_normal='images/switch3_off.png', background_down='images/switch3.png')
        self.button2.bind(on_release=lambda instance: self.on_button_release("Message from Button 2"))
        self.add_widget(self.button2)

    def on_button_release(self, message):
        self.udpClient.send_text(message, udpReportService.ip, udpReportService.port)



    def update_time(self):
        #print(self.gpio.pinRead(self.jigSw))
        self.analog_display.value = random.randint(0,200)
        self.gpio.pinWrite(self.okLED, random.randint(0,1))

        self.clock.text='[color=0099ff]'+datetime.now().strftime('%H:%M:%S')+'[/color]'
        #self.udpClient.send_text("Hello", udpReportService.ip, udpReportService.port)

    def serverUdpIncomingData(self, data):
        try:
            self.servReport.text = f'[color=00ffcc]{data}[/color]'
            #print(data)
            pass
        except:
            print("Error in udp data")
    ##server handler CB function
    def remCtrlCB(self, arg):
        #['', 'slot', '0', 'status']
        reguest = arg.lower().split("/")
        print("CB arg-", reguest )
        return "ok" 
    def stop_server(self):
        if self.server:
            self.server.shutdown()
            self.server_thread.join()




class BoxApp(App):
    def build(self):
        self.screen = MainScreen()
        return self.screen
    
    def on_stop(self):
        self.screen.stop_server()
        pass

if __name__ == '__main__':
    BoxApp().run()
