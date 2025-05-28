import subprocess

import time
import shlex
import pty
import os, socket, re
import random
import json
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
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty, ListProperty
from datetime import datetime, date, timedelta
from collections import namedtuple
from kivy.uix.popup import Popup
from kivy.config import Config
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.uix.actionbar import ActionBar

from remoteCtrlServer.httpserver import start_server_in_thread
from remoteCtrlServer.udpService import UdpAsyncClient


from backgroundServices.backgroundProcessor import BackgroundWorker


class SystemParamObject:
    """A class to represent a system parameter."""
    systime = "00:00:00"
    def __init__(self, name, value):
        self.name = name
        self.value = value

remCtrlPort = 8080

Builder.load_file('kv/bottomBar.kv')
Builder.load_file('kv/popUp.kv')
Builder.load_file('kv/actionBar.kv')



class udpReportService():
    ip = '192.168.1.255'
    rx_port = 5006
    tx_port = 55006

class BottomBar(BoxLayout):
    def show_menu(self):
        self.menu = PopupMenu()
        self.popup = Popup(content=self.menu, size_hint=(None, None), size=(500, 500), title='Settings')
        self.menu.popup_ref = self.popup # <-- передаємо посилання
        self.popup.open()

class PopupMenu(BoxLayout):
    popup_ref = ObjectProperty(None)
    def save_parameters(self):
        # Додайте логіку для збереження параметрів
        print("Parameters saved")
        self.dismiss()

    def dismiss(self):
        print("Popup dismissed")
        if self.popup_ref:
            self.popup_ref.dismiss()

class MyActionBar(ActionBar):
    sysTime = StringProperty("00:00:00")
    volume_icons = [
        'atlas://data/images/defaulttheme/audio-volume-muted',
        'atlas://data/images/defaulttheme/audio-volume-low',
        'atlas://data/images/defaulttheme/audio-volume-medium',
        'atlas://data/images/defaulttheme/audio-volume-high'
    ]
    volume_index = 1
    icon_state = StringProperty(volume_icons[volume_index])
    
    check_state = BooleanProperty(False)
    
    selected_mode = StringProperty("Mode 1")
    mode_color = ListProperty([0, 1, 0, 1])  # Зелений за замовчуванням

    def on_btn_press(self, btn_text):
        print(f"Натиснута кнопка: {btn_text}")

    def on_check_press(self, btn):
        self.check_state = not self.check_state
        btn.icon = (
            'atlas://data/images/defaulttheme/checkbox_on'
            if self.check_state else
            'atlas://data/images/defaulttheme/checkbox_off'
        )

    def switch_icon(self, btn):
        self.volume_index = (self.volume_index + 1) % len(self.volume_icons)
        self.icon_state = self.volume_icons[self.volume_index]
        btn.icon = self.icon_state

    def select_mode(self, mode):
        self.selected_mode = mode
        if mode == "Mode 1":
            self.mode_color = [0, 1, 0, 1]  # Зелений
        else:
            self.mode_color = [1, 0, 0, 1]  # Червоний


class MainScreen(FloatLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.SystemParam = SystemParamObject("System", "Default")
        self.backProc = BackgroundWorker()
        self.backProc.startProc()
        
        
        self.background_image = Image(source='images/bg_d.jpg', size=self.size)
        self.add_widget(self.background_image)
        
        self.action_bar = MyActionBar()
        
        self.add_widget(self.action_bar)

        self.bottom_bar = BottomBar()
        self.add_widget(self.bottom_bar)

        

        ## Server start
        self.server, self.server_thread = start_server_in_thread(remCtrlPort, self.remCtrlCB, self)
        self.udpClient = UdpAsyncClient(self)
        self.udpClient.startListener(udpReportService.rx_port, self.serverUdpIncomingData)
        
        Clock.schedule_interval(lambda dt: self.update_time(), 1)

    
        self.clock = Label(text='[color=ffffff]22:30:38[/color]', markup = True, font_size=100, pos=(-600, 400) , font_name='fonts/hemi_head_bd_it.ttf')
        self.add_widget(self.clock)

        self.servReport = Label(text='[color=00ffcc]No data[/color]', markup=True, font_size=50, pos=(-100, 300), font_name='fonts/hemi_head_bd_it.ttf', halign='left')
        self.add_widget(self.servReport)


        self.button1 = Button(text='', size_hint=(None, None), size=(192, 192), pos_hint={'center_x': .3, 'center_y': .5},
                              background_normal='images/switch3_off.png', background_down='images/switch3.png')
        self.button1.bind(on_release=lambda instance: self.on_button_release("spn:dune:1"))
        self.add_widget(self.button1)

        self.button2 = Button(text='', size_hint=(None, None), size=(192, 192), pos_hint={'center_x': .7, 'center_y': .5},
                              background_normal='images/switch3_off.png', background_down='images/switch3.png')
        self.button2.bind(on_release=lambda instance: self.on_button_release("spn:dune:0"))
        self.add_widget(self.button2)

    def on_button_release(self, message):
        self.udpClient.send_data(message, udpReportService.ip, udpReportService.tx_port)



    def update_time(self):
        #print(self.gpio.pinRead(self.jigSw))
        

        self.clock.text='[color=0099ff]'+datetime.now().strftime('%H:%M:%S')+'[/color]'
        self.SystemParam.systime = datetime.now().strftime('%H:%M:%S')
        self.action_bar.sysTime = self.SystemParam.systime
        #self.udpClient.send_text("Hello", udpReportService.ip, udpReportService.port)
        #print(self.backProc.getStatus())

    def serverUdpIncomingData(self, data):
        try:
            #gtaData = data.split(":")
            #gtaSpd = gtaData[2].split(";")
            json_data = json.loads(data)
            gtaSpd = data
            self.servReport.text = f"[color=00ffcc]{json_data['socStatusLoad'][0]} %, {json_data['socVoltage']/100} V, {json_data['socTemperature']/10} °C[/color]"
            print(json_data)
            pass
        except:
            print("Error in udp data")
    ##server handler CB function
    def remCtrlCB(self, arg):
        #['', 'slot', '0', 'status']
        request = arg.lower().split("/")
        print("CB arg-", request )
        if(request[0] == "run"):
            ##self.backProc.setCmd("run")
            self.backProc.startProc()
            return self.backProc.getStatus()
        elif(request[0] == "stop"):
             self.backProc.stopProc()
             #self.backProc.setCmd("stop")
             return self.backProc.getStatus()  
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
