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
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.screenmanager import Screen , ScreenManager
from threading import Thread
from kivy.clock import Clock
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty, ListProperty
from datetime import datetime, date, timedelta
from collections import namedtuple
from kivy.uix.popup import Popup
from kivy.config import Config
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.uix.actionbar import ActionBar
from kivy.utils import get_color_from_hex as rgb
from kivy.core.text import LabelBase

from remoteCtrlServer.httpserver import start_server_in_thread
from remoteCtrlServer.udpService import UdpAsyncClient

from math import sin, cos, pi
from backgroundServices.backgroundProcessor import BackgroundWorker
from garden.graph import MyGraph
from garden.gauge import Gauge
from getIp import get_active_ip_addresses, get_active_ip_addresses_simple
from SH_DTO.gatewayDto import *
from SH_DTO.smartHomeUdpService import SmartHomeGatewayUdpClient
from SH_DTO.graph import MyGraph


gatewayKotelIP = "192.168.1.18"
gatewayKotelTxPort = 4031
gatewayKotelRxPort = 4030

# Register custom font for better Unicode support
LabelBase.register(name='DejaVuSans',
                  fn_regular='fonts/DejaVuSans.ttf')


class SystemParamObject:
    """A class to represent a system parameter."""
    systime = "00:00:00"
    def __init__(self, name, value):
        self.name = name
        self.value = value


Builder.load_file('kv/popUp.kv')
Builder.load_file('kv/actionBar.kv')
Builder.load_file('kv/telemetryPanel.kv')





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
    title = StringProperty("SmarHome Sys")
    app_icon = StringProperty('images/smIcon.png')  # Власна іконка
    sysTime = StringProperty("00:00:00")
    sysIp = StringProperty("192.168.1.1\n192.168.1.2")
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
        self.new_x = 0
        self.gateway = GatewayDto()
        self.kotelGateway = SmartHomeGatewayUdpClient(cbFn=self.smartHomeGatewayUdpClient, gatewayIp=gatewayKotelIP, rxPort=gatewayKotelRxPort, txPort=gatewayKotelTxPort, bufferSize=1024)
        self.kotelGateway.startListener()
        
        self.energyMonitor = UdpAsyncClient(self)
        self.energyMonitor.startListener(5005, self.serverUdpIncomingData)
        self.invertorMonitor = UdpAsyncClient(self)
        self.invertorMonitor.startListener(5006, self.batteryUdpIncomingData)
        # Temperature plot data
        self.mainPumpTempPoints = []
        self.boilerTempPoints = []
        self.solarCollectorPoints = []
        self.coolantTempPoints = []
        self.kotelTempPoints = []
        
        # Background
        self.background_image = Image(source='images/bg_d.jpg', size=self.size)
        self.add_widget(self.background_image)
        
        # Action bar
        self.action_bar = MyActionBar()
        self.add_widget(self.action_bar)
        
        # Schedule updates
        Clock.schedule_interval(lambda dt: self.update_time(), 1)

        # === LEFT PANEL: Analog Gauges (200px wide) ===
        self.voltmeter = Gauge(value=0, size_gauge=180, size_text=12, meterType="Volt", units='V', 
                              graduation='10, 20, 30, 40, 50, 60, 70', graduationStepAngle=4.5, offset=-10)
        self.currentmeter = Gauge(value=0, size_gauge=180, size_text=12, meterType="Current", units='A', 
                                 graduation='-60, -40, -20, 0, 20, 40, 60', graduationStepAngle=2.25, offset=60)
        self.socmeter = Gauge(value=0, size_gauge=180, size_text=12, meterType="SOC", units='%', 
                              graduation='0, 20, 40, 60, 80, 100, _', graduationStepAngle=2.25)

        self.analogMetersGroup = BoxLayout(orientation='vertical', size_hint=(None, None), size=(200, 540), pos=(5, 5))
        self.analogMetersGroup.add_widget(self.voltmeter)
        self.analogMetersGroup.add_widget(self.currentmeter)
        self.analogMetersGroup.add_widget(self.socmeter)
        self.add_widget(self.analogMetersGroup)
        
        # === CENTER PANEL: Temperature Graph (550px wide) ===
        self.temperatureGraph = MyGraph(ymax=100, ymin=-20)
        self.temperatureGraph.add_horisontalLine(0, rgb('808080'))
        self.temperatureGraph.add_yPlot(self.mainPumpTempPoints, 'FF6600', label='Насос(°C)')     
        self.temperatureGraph.add_yPlot(self.boilerTempPoints, '00FF00', label='Бойлер(°C)')
        self.temperatureGraph.add_yPlot(self.solarCollectorPoints, 'FFFF00', label='Сонце(°C)')
        self.temperatureGraph.add_yPlot(self.coolantTempPoints, '00AAFF', label='Теплон.(°C)')
        self.temperatureGraph.add_yPlot(self.kotelTempPoints, 'FF00FF', label='Котел(°C)')


        self.GraphBox = FloatLayout(size_hint=(None, None), size=(550, 430), pos=(210, 115))
        self.GraphBox.add_widget(self.temperatureGraph)    
        self.add_widget(self.GraphBox)
        
        # === Power Meter Info (under graph) ===
        self.powerMeterBox = BoxLayout(orientation='horizontal', size_hint=(None, None), 
                                       size=(525, 50), pos=(220, 60), padding=5, spacing=3)
        with self.powerMeterBox.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0.1, 0.1, 0.15, 0.85)
            self.powerMeterBox.bg_rect = RoundedRectangle(pos=self.powerMeterBox.pos, 
                                                          size=self.powerMeterBox.size, radius=[8])
            Color(0.0, 1.0, 0.5, 0.5)
            self.powerMeterBox.border = Line(rounded_rectangle=(self.powerMeterBox.x, self.powerMeterBox.y,
                                                               self.powerMeterBox.width, self.powerMeterBox.height, 8), width=1.5)
        self.powerMeterBox.bind(pos=self._update_rect, size=self._update_rect)
        
       
        
        # === Inverter Info (under power meter) ===
        self.inverterBox = BoxLayout(orientation='horizontal', size_hint=(None, None), 
                                     size=(525, 50), pos=(220, 115), padding=5, spacing=3)
        with self.inverterBox.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0.1, 0.1, 0.15, 0.85)
            self.inverterBox.bg_rect = RoundedRectangle(pos=self.inverterBox.pos, 
                                                        size=self.inverterBox.size, radius=[8])
            Color(1.0, 0.5, 0.0, 0.5)
            self.inverterBox.border = Line(rounded_rectangle=(self.inverterBox.x, self.inverterBox.y,
                                                             self.inverterBox.width, self.inverterBox.height, 8), width=1.5)
        self.inverterBox.bind(pos=self._update_rect, size=self._update_rect)
        
        self.pmTime = Label(text='--:--:--', font_name='DejaVuSans', font_size=14, color=rgb('00FF88'), size_hint_x=0.15, halign='center')
        self.pmSource = Label(text='[AC]', font_name='DejaVuSans', font_size=14, color=rgb('00FF00'), markup=True, size_hint_x=0.1, halign='center')
        self.pmVoltage = Label(text='U: ---/---/--- V', font_name='DejaVuSans', font_size=14, color=rgb('DDDDDD'), size_hint_x=0.35, halign='center')
        self.pmCurrent = Label(text='I: ---/---/--- A', font_name='DejaVuSans', font_size=14, color=rgb('DDDDDD'), size_hint_x=0.35, halign='center')
        self.pmPower = Label(text='P: --- W', font_name='DejaVuSans', font_size=14, color=rgb('FFAA00'), size_hint_x=0.15, halign='center')
        
        self.powerMeterBox.add_widget(self.pmTime)
        self.powerMeterBox.add_widget(self.pmSource)
        self.powerMeterBox.add_widget(self.pmVoltage)
        self.powerMeterBox.add_widget(self.pmCurrent)
        self.powerMeterBox.add_widget(self.pmPower)
        self.add_widget(self.powerMeterBox)

        self.invType = Label(text='CAN', font_name='DejaVuSans', font_size=14, color=rgb('00AAFF'), size_hint_x=0.1, halign='center')
        self.invSoc = Label(text='SOC: --/-- %', font_name='DejaVuSans', font_size=14, color=rgb('DDDDDD'), size_hint_x=0.25, halign='center')
        self.invVoltage = Label(text='U: ---- V', font_name='DejaVuSans', font_size=14, color=rgb('DDDDDD'), size_hint_x=0.2, halign='center')
        self.invCurrent = Label(text='I: --- A', font_name='DejaVuSans', font_size=14, color=rgb('DDDDDD'), size_hint_x=0.2, halign='center')
        self.invTemp = Label(text='T: --- °C', font_name='DejaVuSans', font_size=14, color=rgb('DDDDDD'), size_hint_x=0.2, halign='center')
        
        self.inverterBox.add_widget(self.invType)
        self.inverterBox.add_widget(self.invSoc)
        self.inverterBox.add_widget(self.invVoltage)
        self.inverterBox.add_widget(self.invCurrent)
        self.inverterBox.add_widget(self.invTemp)
        self.add_widget(self.inverterBox)
        
        # === Status Indicators (bottom bar) ===
        self.statusBox = BoxLayout(orientation='horizontal', size_hint=(None, None), 
                                   size=(525, 50), pos=(220, 5), padding=5, spacing=15)
        with self.statusBox.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0.1, 0.1, 0.15, 0.85)
            self.statusBox.bg_rect = RoundedRectangle(pos=self.statusBox.pos, 
                                                      size=self.statusBox.size, radius=[8])
            Color(0.5, 0.5, 0.5, 0.5)
            self.statusBox.border = Line(rounded_rectangle=(self.statusBox.x, self.statusBox.y,
                                                           self.statusBox.width, self.statusBox.height, 8), width=1.5)
        self.statusBox.bind(pos=self._update_rect, size=self._update_rect)
        
        # CAN Section
        self.canSection = BoxLayout(orientation='horizontal', size_hint_x=0.7, spacing=3)
        self.canLabel = Label(text='[b]CAN:[/b]', font_name='DejaVuSans', font_size=13, 
                             color=rgb('00AAFF'), markup=True, size_hint_x=None, width=45, halign='right')
        self.statusKotel = Label(text='[color=00FF00]●[/color] Kotel', font_name='DejaVuSans', font_size=11, 
                                color=rgb('DDDDDD'), markup=True, halign='center')
        self.statusSensor = Label(text='[color=00FF00]●[/color] Sensor', font_name='DejaVuSans', font_size=11, 
                                 color=rgb('DDDDDD'), markup=True, halign='center')
        self.statusTank = Label(text='[color=00FF00]●[/color] Tank', font_name='DejaVuSans', font_size=11, 
                               color=rgb('DDDDDD'), markup=True, halign='center')
        self.statusUPS = Label(text='[color=00FF00]●[/color] UPS', font_name='DejaVuSans', font_size=11, 
                              color=rgb('DDDDDD'), markup=True, halign='center')
        
        self.canSection.add_widget(self.canLabel)
        self.canSection.add_widget(self.statusKotel)
        self.canSection.add_widget(self.statusSensor)
        self.canSection.add_widget(self.statusTank)
        self.canSection.add_widget(self.statusUPS)
        
        # UDP Section
        self.udpSection = BoxLayout(orientation='horizontal', size_hint_x=0.3, spacing=3)
        self.udpLabel = Label(text='[b]UDP:[/b]', font_name='DejaVuSans', font_size=13, 
                             color=rgb('00FF88'), markup=True, size_hint_x=None, width=45, halign='right')
        self.statusServer = Label(text='[color=00FF00]●[/color] Server', font_name='DejaVuSans', font_size=11, 
                                 color=rgb('DDDDDD'), markup=True, halign='center')
        
        self.udpSection.add_widget(self.udpLabel)
        self.udpSection.add_widget(self.statusServer)
        
        self.statusBox.add_widget(self.canSection)
        self.statusBox.add_widget(self.udpSection)
        self.add_widget(self.statusBox)

        # === RIGHT PANEL: Telemetry Data (264px wide) ===
        self.telemetryPanel = BoxLayout(orientation='vertical', size_hint=(None, None), 
                                       size=(254, 500), pos=(765, 5), spacing=5)
        
        # UPS Section
        self.upsBox = BoxLayout(orientation='vertical', size_hint_y=None, height=125, padding=5, spacing=1)
        with self.upsBox.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0.1, 0.1, 0.15, 0.85)
            self.upsBox.bg_rect = RoundedRectangle(pos=self.upsBox.pos, size=self.upsBox.size, radius=[8])
            Color(0.0, 1.0, 1.0, 0.5)
            self.upsBox.border = Line(rounded_rectangle=(self.upsBox.x, self.upsBox.y, 
                                                         self.upsBox.width, self.upsBox.height, 8), width=1.5)
        self.upsBox.bind(pos=self._update_rect, size=self._update_rect)
        
        self.upsTitle = Label(text='[b][color=00FFFF]--- UPS ---[/color][/b]', font_name='DejaVuSans', markup=True, 
                             font_size=13, size_hint_y=None, height=20, halign='center')
        
        # Two-column layout: LED indicators (left) and data (right)
        self.upsContent = BoxLayout(orientation='horizontal', size_hint_y=1, spacing=3)
        
        # Left column: LED status indicators
        self.upsLedColumn = BoxLayout(orientation='vertical', size_hint_x=0.45, spacing=1)
        self.upsState = Label(text='Стан: --', font_name='DejaVuSans', font_size=10, color=rgb('DDDDDD'), markup=True,
                             halign='left', valign='top', padding=(5, 0))
        self.upsState.text_size = (100, None)
        self.upsLedColumn.add_widget(self.upsState)
        
        # Right column: Data values
        self.upsDataColumn = BoxLayout(orientation='vertical', size_hint_x=0.55, spacing=1)
        self.upsVoltage = Label(text='Напруга: --.- В', font_name='DejaVuSans', font_size=12, color=rgb('DDDDDD'),
                               size_hint_y=None, height=16, halign='left', padding=(5, 0))
        self.upsVoltage.text_size = (130, None)
        self.upsCurrent = Label(text='Струм: --- A', font_name='DejaVuSans', font_size=12, color=rgb('DDDDDD'),
                               size_hint_y=None, height=16, halign='left', padding=(5, 0))
        self.upsCurrent.text_size = (130, None)
        self.upsEnergy = Label(text='Енергія: ----- Wh', font_name='DejaVuSans', font_size=12, color=rgb('DDDDDD'),
                              size_hint_y=None, height=16, halign='left', padding=(5, 0))
        self.upsEnergy.text_size = (130, None)
        self.upsSource = Label(text='Джерело: [color=00FF00][AC][/color]', font_name='DejaVuSans', markup=True, 
                              font_size=12, color=rgb('DDDDDD'), size_hint_y=None, height=16, halign='left', padding=(5, 0))
        self.upsSource.text_size = (130, None)
        self.upsDataColumn.add_widget(self.upsVoltage)
        self.upsDataColumn.add_widget(self.upsCurrent)
        self.upsDataColumn.add_widget(self.upsEnergy)
        self.upsDataColumn.add_widget(self.upsSource)
        
        self.upsContent.add_widget(self.upsLedColumn)
        self.upsContent.add_widget(self.upsDataColumn)
        
        self.upsBox.add_widget(self.upsTitle)
        self.upsBox.add_widget(self.upsContent)
        
        # Kotel Section
        self.kotelBox = BoxLayout(orientation='vertical', size_hint_y=None, height=125, padding=5, spacing=1)
        with self.kotelBox.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0.1, 0.1, 0.15, 0.85)
            self.kotelBox.bg_rect = RoundedRectangle(pos=self.kotelBox.pos, size=self.kotelBox.size, radius=[8])
            Color(1.0, 0.67, 0.0, 0.5)
            self.kotelBox.border = Line(rounded_rectangle=(self.kotelBox.x, self.kotelBox.y, 
                                                          self.kotelBox.width, self.kotelBox.height, 8), width=1.5)
        self.kotelBox.bind(pos=self._update_rect, size=self._update_rect)
        
        self.kotelTitle = Label(text='[b][color=FFaa00]--- КОТЕЛ ---[/color][/b]', font_name='DejaVuSans', markup=True, 
                               font_size=13, size_hint_y=None, height=20, halign='center')
        
        # Two-column layout: LED indicators (left) and data (right)
        self.kotelContent = BoxLayout(orientation='horizontal', size_hint_y=1, spacing=3)
        
        # Left column: LED status indicators
        self.kotelLedColumn = BoxLayout(orientation='vertical', size_hint_x=0.45, spacing=1)
        self.kotelStatus = Label(text='Статус: --', font_name='DejaVuSans', font_size=10, color=rgb('DDDDDD'), markup=True,
                                halign='left', valign='top', padding=(5, 0))
        self.kotelStatus.text_size = (100, None)
        self.kotelLedColumn.add_widget(self.kotelStatus)
        
        # Right column: Data values
        self.kotelDataColumn = BoxLayout(orientation='vertical', size_hint_x=0.55, spacing=1)
        self.kotelTemp = Label(text='Температура: --.- °C', font_name='DejaVuSans', font_size=12, color=rgb('DDDDDD'),
                              size_hint_y=None, height=16, halign='left', padding=(5, 0))
        self.kotelTemp.text_size = (130, None)
        self.kotelHiLo = Label(text='Hi/Lo: -- / -- °C', font_name='DejaVuSans', font_size=12, color=rgb('DDDDDD'),
                              size_hint_y=None, height=16, halign='left', padding=(5, 0))
        self.kotelHiLo.text_size = (130, None)
        self.kotelRun = Label(text='Run/Stop: -- / -- °C', font_name='DejaVuSans', font_size=12, color=rgb('DDDDDD'),
                             size_hint_y=None, height=16, halign='left', padding=(5, 0))
        self.kotelRun.text_size = (130, None)
        self.kotelDelta = Label(text='Delta: -- °C', font_name='DejaVuSans', font_size=12, color=rgb('DDDDDD'),
                               size_hint_y=None, height=16, halign='left', padding=(5, 0))
        self.kotelDelta.text_size = (130, None)
        self.kotelDataColumn.add_widget(self.kotelTemp)
        self.kotelDataColumn.add_widget(self.kotelHiLo)
        self.kotelDataColumn.add_widget(self.kotelRun)
        self.kotelDataColumn.add_widget(self.kotelDelta)
        
        self.kotelContent.add_widget(self.kotelLedColumn)
        self.kotelContent.add_widget(self.kotelDataColumn)
        
        self.kotelBox.add_widget(self.kotelTitle)
        self.kotelBox.add_widget(self.kotelContent)
        
        # Water Tank Section
        self.waterBox = BoxLayout(orientation='vertical', size_hint_y=None, height=125, padding=5, spacing=1)
        with self.waterBox.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0.1, 0.1, 0.15, 0.85)
            self.waterBox.bg_rect = RoundedRectangle(pos=self.waterBox.pos, size=self.waterBox.size, radius=[8])
            Color(0.0, 0.67, 1.0, 0.5)
            self.waterBox.border = Line(rounded_rectangle=(self.waterBox.x, self.waterBox.y, 
                                                          self.waterBox.width, self.waterBox.height, 8), width=1.5)
        self.waterBox.bind(pos=self._update_rect, size=self._update_rect)
        
        self.waterTitle = Label(text='[b][color=00AAFF]--- ВОДА ---[/color][/b]', font_name='DejaVuSans', markup=True, 
                               font_size=14, size_hint_y=None, height=22, halign='center')
        self.waterPress = Label(text='Тиск: --- mBar', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                               size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.waterPress.text_size = (244, None)
        self.waterLimits = Label(text='Lim/D: --- / -- mBar', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                                size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.waterLimits.text_size = (244, None)
        self.waterLevel = Label(text='Рівень: -- %', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                               size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.waterLevel.text_size = (244, None)
        self.waterDIO = Label(text='DIN/OUT: -- / --', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                             size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.waterDIO.text_size = (244, None)
        self.waterBox.add_widget(self.waterTitle)
        self.waterBox.add_widget(self.waterPress)
        self.waterBox.add_widget(self.waterLimits)
        self.waterBox.add_widget(self.waterLevel)
        self.waterBox.add_widget(self.waterDIO)
        
        # Pump & Sensors Section
        self.auxBox = BoxLayout(orientation='vertical', size_hint_y=None, height=125, padding=5, spacing=1)
        with self.auxBox.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0.1, 0.1, 0.15, 0.85)
            self.auxBox.bg_rect = RoundedRectangle(pos=self.auxBox.pos, size=self.auxBox.size, radius=[8])
            Color(0.0, 1.0, 0.0, 0.5)
            self.auxBox.border = Line(rounded_rectangle=(self.auxBox.x, self.auxBox.y, 
                                                        self.auxBox.width, self.auxBox.height, 8), width=1.5)
        self.auxBox.bind(pos=self._update_rect, size=self._update_rect)
        
        self.auxTitle = Label(text='[b][color=00FF00]--- СЕНСОРИ ---[/color][/b]', font_name='DejaVuSans', markup=True, 
                             font_size=14, size_hint_y=None, height=22, halign='center')
        self.pumpInfo = Label(text='Насос: --- mA (OFF)', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                             size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.pumpInfo.text_size = (244, None)
        
        self.boilerTemp = Label(text='Бойлер: -- °C', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                                size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.boilerTemp.text_size = (244, None)
        self.coolantTemp = Label(text='Теплоносій: -- °C', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                                size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.coolantTemp.text_size = (244, None)

        self.solarCollectorTemp = Label(text='Сонячний колектор: -- °C', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                                       size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.solarCollectorTemp.text_size = (244, None)

        self.pumpTemp = Label(text='Темп. насоса: -- °C', font_name='DejaVuSans', font_size=11, color=rgb('DDDDDD'),
                              size_hint_y=None, height=18, halign='left', padding=(10, 0))
        self.pumpTemp.text_size = (244, None)


        self.auxBox.add_widget(self.auxTitle)
        self.auxBox.add_widget(self.pumpInfo)
        self.auxBox.add_widget(self.boilerTemp)
        self.auxBox.add_widget(self.coolantTemp)
        self.auxBox.add_widget(self.solarCollectorTemp)
        self.auxBox.add_widget(self.pumpTemp)

        
        # Add all sections to telemetry panel
        self.telemetryPanel.add_widget(self.upsBox)
        self.telemetryPanel.add_widget(self.kotelBox)
        self.telemetryPanel.add_widget(self.waterBox)
        self.telemetryPanel.add_widget(self.auxBox)
        
        

        self.add_widget(self.telemetryPanel)
    def serverUdpIncomingData(self, data):
        """Handle incoming Power Meter UDP data"""
        #print("Main PM:", data)
        try:
            # Перевіряємо чи віджети вже створені
            if not hasattr(self, 'pmTime'):
                return
                
            pm_data = json.loads(data) if isinstance(data, str) else data
            self.pmTime.text = pm_data.get('time', '--:--:--')
            
            source = pm_data.get('source', 'AC')
            if source == 'AC':
                self.pmSource.text = '[color=00FF00][AC][/color]'
            else:
                self.pmSource.text = '[color=FF0000][DC][/color]'
            
            voltage = pm_data.get('voltage', [0, 0, 0])
            self.pmVoltage.text = f'U: {voltage[0]}/{voltage[1]}/{voltage[2]} V'
            
            current = pm_data.get('current', [0, 0, 0])
            self.pmCurrent.text = f'I: {current[0]/1000:.1f}/{current[1]/1000:.1f}/{current[2]/1000:.1f} A'
            
            power = pm_data.get('total_power', 0)
            self.pmPower.text = f'P: {power/1000:.1f} kW'
        except Exception as e:
            print(f"Error parsing PM data: {e}")
    
    def batteryUdpIncomingData(self, data):
        """Handle incoming Inverter UDP data"""
        #print("Main Inverter:", data)
        try:
            inv_data = json.loads(data) if isinstance(data, str) else data
            
            # Перевіряємо чи віджети вже створені
            if not hasattr(self, 'invType'):
                return
            
            dev_type = inv_data.get('devType', 'CAN')
            self.invType.text = dev_type
            
            soc_status = inv_data.get('socStatusLoad', [0, 0])
            self.invSoc.text = f'SOC: {soc_status[0]} %'
            
            voltage = inv_data.get('socVoltage', 0) / 100.0  # Convert to volts
            self.invVoltage.text = f'U: {voltage:.1f} V'
            
            current = inv_data.get('socCurrent', 0) / 10.0  # Convert to amps
            self.invCurrent.text = f'I: {current:.1f} A'
            
            temp = inv_data.get('socTemperature', 0) / 10.0  # Convert to celsius
            self.invTemp.text = f'T: {temp:.1f} °C'
            self.gateway.inverterVoltage = voltage
            self.gateway.inverterCurrent = current
            self.gateway.inverterSoc = soc_status[0]

        except Exception as e:
            print(f"Error parsing Inverter data: {e}")

    def _update_rect(self, instance, value):
        """Update background rectangles when widget size/position changes"""
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
        if hasattr(instance, 'border'):
            instance.border.rounded_rectangle = (instance.x, instance.y, 
                                                instance.width, instance.height, 8)
        
    def temperatureGraphUpdate(self):
        """Update temperature graph with data from gateway"""
        self.mainPumpTempPoints.append(float(self.gateway.mainCirkulationPumpTemp))
        self.boilerTempPoints.append(float(self.gateway.boilerTemperature))
        self.solarCollectorPoints.append(float(self.gateway.solarCollectorTemp))
        self.coolantTempPoints.append(float(self.gateway.coolantTemperature))
        self.kotelTempPoints.append(float(self.gateway.kotelActTemp) / 100.0)
        
        # Keep only last 1000 points
        if len(self.mainPumpTempPoints) > 1000:
            self.mainPumpTempPoints.pop(0)
            self.boilerTempPoints.pop(0)
            self.solarCollectorPoints.pop(0)
            self.coolantTempPoints.pop(0)
            self.kotelTempPoints.pop(0)
        
        self.temperatureGraph.refresh_plots()
    
    def decode_ups_status(self, status_byte):
        """Decode UPS status byte into individual bit states"""
        bits = [
            ('Manual RUN', 0, '00FF00'),
            ('KOTEL', 1, '00FF00'),
            ('Solar module', 2, '00FF00'),
            ('BAT ERROR', 3, '0cf7f3'),
            ('Inv. ERR', 4, '0cf7f3'),
            ('Inv. overheat', 5, '0cf7f3'),
            ('Chrg. ERR', 6, '0cf7f3'),
            ('Chrg. Overheat', 7, '0cf7f3')
        ]
        status_text = ''
        for label, bit_num, color in bits:
            bit_val = (status_byte >> bit_num) & 1
            if bit_val:
                status_text += f'[color={color}]● {label}[/color]\n'
            else:
                status_text += f'[color=555555]○ {label}[/color]\n'
        return status_text.strip()
    
    def decode_kotel_status(self, status_byte):
        """Decode Kotel status byte into individual bit states"""
        bits = [
            ('Prerun', 0, 'FFAA00'),
            ('RUN', 1, '00FF00'),
            ('T1 ERROR', 2, 'FF0000'),
            ('T2 ERROR', 3, 'FF0000'),
            ('Flue Overheat', 4, 'FF6600'),
            ('REL1', 5, '00FF00'),
            ('DOOR', 6, 'FFFF00'),
            ('REL stat', 7, '00FF00')
        ]
        status_text = ''
        for label, bit_num, color in bits:
            bit_val = (status_byte >> bit_num) & 1
            if bit_val:
                status_text += f'[color={color}]● {label}[/color]\n'
            else:
                status_text += f'[color=555555]○ {label}[/color]\n'
        return status_text.strip()
    
    def updateTelemetryDisplay(self):
        """Update all telemetry display widgets with current gateway data"""
        # Update analog gauges
        self.voltmeter.value = self.gateway.inverterVoltage
        
       
        self.currentmeter.value = self.gateway.inverterCurrent  # Convert to amperes
        self.socmeter.value = self.gateway.inverterSoc
        
        # UPS Section
        self.upsVoltage.text = f'U: {self.gateway.batVoltage:.1f} В'
        self.upsCurrent.text = f'I: {(self.gateway.batCurrent / 100.0):.2f} A'
        self.upsEnergy.text = f'E: {self.gateway.batEnergyf:.1f} Wh'
        
        # Color-coded source indicator
        if self.gateway.currentSource == "DC":
            self.upsSource.text = 'Джерело: [color=FF0000][DC][/color]'
        else:
            self.upsSource.text = 'Джерело: [color=00FF00][AC][/color]'
        
        # Decode and display UPS status bits
        self.upsState.text = self.decode_ups_status(self.gateway.currentState)
        
        # Kotel Section
        
        self.kotelTemp.text = f'Котел: {self.gateway.kotelActTemp / 100.0:.1f} °C'
        self.kotelHiLo.text = f'Hi/Lo: {self.gateway.kotelTemHi} / {self.gateway.kotelTemLo} °C'
        self.kotelRun.text = f'R/S: {self.gateway.kotelTemRun} / {self.gateway.kotelTemStop} °C'
        self.kotelDelta.text = f'Delta: {self.gateway.kotelTemDelta} °C'
        
        # Decode and display Kotel status bits
        self.kotelStatus.text = self.decode_kotel_status(self.gateway.kotelStatus)
        
        # Water Tank Section
        self.waterPress.text = f'Тиск: {self.gateway.waterPress*10} mBar'
        self.waterLimits.text = f'Lim/D: {self.gateway.waterPressLoLim*10} / {self.gateway.waterPressDelta*10} mBar'
        self.waterLevel.text = f'Рівень: {self.gateway.waterLevel-127} %'
        self.waterDIO.text = f'DIN/OUT: {self.gateway.waterTankDIN:02X}h / {self.gateway.waterTankDOUT:02X}h'
        
        # Pump & Sensors Section
        self.pumpInfo.text = f'Насос: {self.gateway.pumpCurrent} mA ({self.gateway.pumpMode})'
        self.boilerTemp.text = f'Бойлер: {self.gateway.boilerTemperature} °C'
        self.coolantTemp.text = f'Теплоносій: {self.gateway.coolantTemperature} °C'
        self.solarCollectorTemp.text = f'Сонячний колектор: {self.gateway.solarCollectorTemp} °C'
        self.pumpTemp.text = f'Темп. насоса: {self.gateway.mainCirkulationPumpTemp} °C'

       

    def smartHomeGatewayUdpClient(self, can_message):
        self.gateway.canMsgParse(can_message)
        pass

    def update_time(self):
        """Update time and all telemetry displays every second"""
        self.SystemParam.systime = datetime.now().strftime('%H:%M:%S')
        self.action_bar.sysTime = self.SystemParam.systime
        self.action_bar.sysIp = get_active_ip_addresses_simple()
        
        # Update temperature graph and all telemetry displays
        self.temperatureGraphUpdate()
        self.updateTelemetryDisplay()



class BoxApp(App):
    def build(self):
        self.screen = MainScreen()
        return self.screen
    
    def on_stop(self):
        self.screen.stop_server()
        pass


if __name__ == '__main__':
    BoxApp().run()
