#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

'''
Gauge
=====

The :class:`Gauge` widget is a widget for displaying gauge.

.. note::

Source svg file provided for customing.

'''

__all__ = ('Gauge',)

__title__ = 'garden.gauge'
__version__ = '0.2'
__author__ = 'julien@hautefeuille.eu'

import kivy
kivy.require('1.6.0')
from kivy.config import Config
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import NumericProperty, BooleanProperty
from kivy.properties import StringProperty
from kivy.properties import BoundedNumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from os.path import join, dirname, abspath
import math


class Gauge(Widget):
    '''
    Gauge class

    '''
    graduationStepAngle = NumericProperty(2.25) # Кут повороту голки на одиницю виміру 
    unit = NumericProperty(1)  
    value = BoundedNumericProperty(0, min=0, max=100, errorvalue=0)
    path = dirname(abspath(__file__))
    file_gauge = StringProperty(join(path, "assets/gaugeBG2.png"))
    file_needle = StringProperty(join(path, "assets/needleB.png"))
    size_gauge = BoundedNumericProperty(128, min=128, max=256, errorvalue=128)
    graduation = StringProperty('0, 10, 20, 30, 40, 50, FF')
    size_text = NumericProperty(16)
    units = StringProperty('V') #°C
    meterType = StringProperty('Voltmeter')
    
    # Параметри для градуації шкали
    start_angle = NumericProperty(45)  # Початковий кут шкали (в градусах)
    end_angle = NumericProperty(315)     # Кінцевий кут шкали (в градусах)
    graduation_radius = NumericProperty(0.5)  # Відстань від центра (як частка радіуса)
    show_graduation = BooleanProperty(True)   # Показувати чи ні градуацію
    showProgress = BooleanProperty(False)  # Показувати чи ні прогрес бар
    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)

        self._gauge = Scatter(
            size=(self.size_gauge, self.size_gauge),
            do_rotation=False,
            do_scale=False,
            do_translation=False
        )

        _img_gauge = Image(
            source=self.file_gauge,
            size=(self.size_gauge, self.size_gauge)
        )

        self._needle = Scatter(
            size=(self.size_gauge, self.size_gauge),
            do_rotation=False,
            do_scale=False,
            do_translation=False
        )

        _img_needle = Image(
            source=self.file_needle,
            size=(self.size_gauge, self.size_gauge)
        )

        self._glab = Label(font_size=self.size_text, markup=True)
        self._meterType = Label(font_size=self.size_text, markup=True)
        self._progress = ProgressBar(max=100, height=20, value=self.value)
        
        # Список для зберігання міток градуації
        self._graduation_labels = []

        self._gauge.add_widget(_img_gauge)
        self._needle.add_widget(_img_needle)

        self.add_widget(self._gauge)
        self.add_widget(self._glab)
        self.add_widget(self._meterType)
        # Створюємо градуацію
        self._create_graduation()
        self.add_widget(self._needle)
        
        if self.showProgress:
            self.add_widget(self._progress)
        
        

        self.bind(pos=self._update)
        self.bind(size=self._update)
        self.bind(value=self._turn)
        self.bind(graduation=self._update_graduation)

    def _update(self, *args):
        '''
        Update gauge and needle positions after sizing or positioning.

        '''
        self._gauge.pos = self.pos
        self._needle.pos = (self.x, self.y)
        self._needle.center = self._gauge.center
        self._glab.center_x = self._gauge.center_x
        self._glab.center_y = self._gauge.center_y - (self.size_gauge / 4.8)
        
        self._meterType.center_x = self._gauge.center_x
        self._meterType.center_y = self._gauge.center_y - (self.size_gauge / 3.3)
        
        self._progress.x = self._gauge.x
        self._progress.y = self._gauge.y + (self.size_gauge / 4)
        self._progress.width = self.size_gauge
        
        # Позиціонуємо мітки градуації
        self._position_graduation_labels()

    def _turn(self, *args):
        '''
        Turn needle, 1 degree = 1 unit, 0 degree point start on 50 value.

        '''
        self._needle.center_x = self._gauge.center_x
        self._needle.center_y = self._gauge.center_y
        #self._needle.rotation = (50 * self.unit) - (self.value * self.unit)

        self._needle.rotation = 135 - (self.value * self.graduationStepAngle)

        self._glab.text = f"[b]{self.value:.1f} {self.units}[/b]"
        self._meterType.text = f"[b]{self.meterType}[/b]"
        self._progress.value = self.value

    def _create_graduation(self):
        '''
        Створює мітки градуації на основі значень з graduation
        '''
        if not self.show_graduation:
            return
        # Парсимо значення градуації
        try:
            grad_values = [x.strip() for x in self.graduation.split(',')]
        except ValueError:
            return
            
        # Очищуємо старі мітки
        self._clear_graduation()
    
        if len(grad_values) < 2:
            return
        # Реверсуємо масив для правильного відображення за годинниковою стрілкою
        grad_values = grad_values[::-1]

        # Обчислюємо кути для кожного значення
        total_angle = self.end_angle - self.start_angle
        num_steps = len(grad_values) - 1
        for i, value in enumerate(grad_values):
            # Обчислюємо кут для цього значення на основі позиції в списку
            if num_steps > 0:
                ratio = i / num_steps
            else:
                ratio = 0
            angle = self.start_angle + (ratio * total_angle)

            # Створюємо мітку
            label = Label(
                text=str(value),  # Просто конвертуємо в строку без перевірки на число
                font_size=self.size_text * 0.8,
                color=(1, 1, 1, 1),
                markup=True
            )
            self._graduation_labels.append((label, angle, value))
            self.add_widget(label)


    def _clear_graduation(self):
        '''
        Очищає існуючі мітки градуації
        '''
        for label, _, _ in self._graduation_labels:
            self.remove_widget(label)
        self._graduation_labels.clear()
    
    def _update_graduation(self, *args):
        '''
        Оновлює градуацію при зміні параметрів
        '''
        self._create_graduation()
        self._update()
    
    def _position_graduation_labels(self):
        '''
        Позиціонує мітки градуації навколо циферблата
        '''
        if not self.show_graduation:
            return
            
        center_x = self._gauge.center_x
        center_y = self._gauge.center_y
        radius = (self.size_gauge / 2) * self.graduation_radius
        
        for label, angle, value in self._graduation_labels:
            # Конвертуємо кут в радіани (Kivy використовує кути від 0° вправо)
            angle_rad = math.radians(angle - 90)  # -90 щоб 0° був вгорі
            
            # Обчислюємо позицію мітки
            x = center_x + radius * math.cos(angle_rad)
            y = center_y + radius * math.sin(angle_rad)
            
            # Центруємо мітку відносно обчисленої позиції
            label.center_x = x
            label.center_y = y


if __name__ == '__main__':
    from kivy.uix.slider import Slider

    class GaugeApp(App):
        increasing = NumericProperty(1)
        begin = NumericProperty(50)
        step = NumericProperty(1)

        def build(self):
            box = BoxLayout(orientation='horizontal', padding=5)
            self.gauge = Gauge(
                value=50, 
                size_gauge=256, 
                size_text=25,
                graduation='0, 25, 50, 75, 100',
                start_angle=-135,
                end_angle=135,
                graduation_radius=0.75,
                show_graduation=True,
                units='V',
                meterType='Voltmeter'
            )
            self.slider = Slider(orientation='vertical')

            stepper = Slider(min=1, max=25)
            stepper.bind(
                value=lambda instance, value: setattr(self, 'step', value)
            )

            box.add_widget(self.gauge)
            box.add_widget(stepper)
            box.add_widget(self.slider)
            Clock.schedule_interval(lambda *t: self.gauge_increment(), 0.03)
            return box

        def gauge_increment(self):
            begin = self.begin
            begin += self.step * self.increasing
            if begin > 0 and begin < 100:
                self.gauge.value = self.slider.value = begin
            else:
                self.increasing *= -1
            self.begin = begin

    GaugeApp().run()
