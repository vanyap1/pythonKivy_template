"""
Universal Gauge Widget
=====================

Defines a universal gauge widget that can be easily customized for different
meter types like voltmeter, speedometer, temperature gauge, etc.
Based on the SpeedMeter widget but with enhanced configurability.
"""

import os.path
from math import atan2, cos, pi, radians, sin

from kivy.core.text import Label as CoreLabel
from kivy.graphics import *
from kivy.properties import *
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

__all__ = ('UniversalGauge', )

__version__ = '1.0.0'

_redraw = tuple('pos size min max'.split())
_redraw_background = tuple('sectors sector_width shadow_color'.split())
_redraw_full_cadran = tuple(
    'tick subtick cadran_color display_first '
    'display_last value_font_size'.split())
_redraw_label = tuple(
    'label label_radius_ratio label_angle_ratio '
    'label_icon label_icon_scale label_font_size'.split())
_redraw_needle = tuple('needle_color'.split())

_image_dir = os.path.join(os.path.dirname(__file__), 'images')

_2pi = 2 * pi
_halfPi = pi / 2

_ig = tuple('sectors shadow outerCadran values label needle'.split())


class UniversalGauge(Widget):
    """A universal gauge widget that can be customized for various measurements."""

    # Basic properties
    min = NumericProperty(0)
    max = NumericProperty(100)
    value = NumericProperty(0)
    
    # Size properties
    size_gauge = NumericProperty(200)
    
    # Appearance properties
    needle_color = StringProperty('#ff4444')
    cadran_color = StringProperty('#ffffff')
    background_color = StringProperty('#000000')
    
    # Scale properties
    tick = NumericProperty(10)
    subtick = NumericProperty(2)
    display_first = BooleanProperty(True)
    display_last = BooleanProperty(True)
    
    # Angle properties
    start_angle = NumericProperty(-135, min=-360, max=360)
    end_angle = NumericProperty(135, min=-360, max=360)
    
    # Text properties
    label = StringProperty('')
    units = StringProperty('')
    meter_type = StringProperty('Gauge')
    label_font_size = NumericProperty(16, min=1)
    value_font_size = NumericProperty(12, min=1)
    size_text = NumericProperty(14, min=1)
    
    # Label positioning
    label_radius_ratio = NumericProperty(0.3, min=-1, max=1)
    label_angle_ratio = NumericProperty(0.5, min=0, max=1)
    
    # Advanced properties
    sectors = ListProperty()
    sector_width = NumericProperty(0, min=0)
    thickness = NumericProperty(1.5, min=0)
    shadow_color = StringProperty('')
    
    # Needle properties
    needle_image = StringProperty('needle.png')

    def __init__(self, **kwargs):
        # Extract custom parameters
        self.meter_type = kwargs.pop('meterType', 'Gauge')
        self.size_gauge = kwargs.pop('size_gauge', 200)
        self.size_text = kwargs.pop('size_text', 14)
        
        super(UniversalGauge, self).__init__(**kwargs)
        
        # Set widget size based on size_gauge
        self.size = (self.size_gauge, self.size_gauge)
        self.size_hint = (None, None)
        
        # Set font sizes based on size_text
        self.label_font_size = self.size_text + 2
        self.value_font_size = self.size_text
        
        # Initialize internal variables
        self.a = self.b = self.r2 = self.r = self.centerx = self.centery = 0
        self._shadow = None
        self.rotate = _X
        self._labelRectangle = -1
        self._needle_image = os.path.join(_image_dir, 'needle.png')
        
        # Set default label based on meter type
        if not self.label:
            self.label = f'{self.meter_type}\n{self.units}' if self.units else self.meter_type

        # Create instruction groups
        add = self.canvas.add
        for instructionGroupName in _ig:
            ig = InstructionGroup()
            setattr(self, '_%sIG' % instructionGroupName, ig)
            add(ig)

        self.extendedTouch = False
        
        # Bind events
        bind = self.bind
        for eventList, fn in (
                (_redraw, self._redraw),
                (_redraw_background, self._draw_background),
                (_redraw_full_cadran, self._draw_full_cadran),
                (_redraw_label, self._draw_label),
                (_redraw_needle, self._draw_needle),
        ):
            for event in eventList:
                bind(**{event: fn})

    def value_str(self, n):
        """Convert value to string representation on the dial."""
        return str(int(n))

    def _draw_sectors(self):
        self._sectorsIG.clear()
        add = self._sectorsIG.add
        l = self.sectors[:]
        if not l:
            return
        r = self.r
        centerx = self.centerx
        centery = self.centery
        d = r + r
        a = self.a
        b = self.b
        v0 = l.pop(0)
        a0 = -(a * v0 + b)
        sw = self.sector_width
        if sw:
            r -= sw
        else:
            centerx -= r
            centery -= r
            dd = (d, d)

        while l:
            color = l.pop(0)
            v1 = l.pop(0) if l else self.max
            a1 = -(a * v1 + b)
            add(Color(rgba=get_color_from_hex(color)))
            if sw:
                add(Line(circle=(centerx, centery, r, a0, a1),
                         width=sw, cap='none'))
            else:
                add(Ellipse(pos=(centerx, centery),
                            size=dd, angle_start=a0, angle_end=a1))
            a0 = a1

    def _set_shadow_value(self):
        if not self._shadow:
            return
        a0 = -(self.a * self.min + self.b)
        a1 = -(self.a * self.value + self.b)
        self._shadow.circle = (self.centerx, self.centery, self.r - 5, a0, a1)

    def _draw_shadow(self):
        self._shadowIG.clear()
        self._shadow = None
        if not self.shadow_color:
            return
        add = self._shadowIG.add
        add(Color(rgba=get_color_from_hex(self.shadow_color)))
        self._shadow = Line(width=5, cap='none')
        add(self._shadow)
        self._set_shadow_value()

    def _draw_outer_cadran(self):
        self._outerCadranIG.clear()
        add = self._outerCadranIG.add
        centerx = self.centerx
        centery = self.centery
        r = self.r
        theta0 = self.start_angle
        theta1 = self.end_angle
        add(Color(rgba=get_color_from_hex(self.cadran_color)))
        if theta0 == theta1:
            add(Line(circle=(centerx, centery, r), width=1.5))
        else:
            rt0 = radians(theta0)
            rt1 = radians(theta1)
            add(Line(points=(
                centerx + r * sin(rt0),
                centery + r * cos(rt0),
                centerx, centery,
                centerx + r * sin(rt1),
                centery + r * cos(rt1),
            ),
                     width=1.5,
            ))
            add(Line(circle=(centerx, centery, r, theta0, theta1), width=1.5))

    def _draw_values(self):
        self._valuesIG.clear()
        add = self._valuesIG.add
        centerx = self.centerx
        centery = self.centery
        r = self.r
        value_str = self.value_str
        
        # Create list of values to display
        value_list = list(range(self.min, self.max + 1, self.tick))
        if len(value_list) <= 1:
            return

        # Create labels
        values = []
        for i in value_list:
            label_text = value_str(i)
            label = CoreLabel(text=label_text, font_size=self.value_font_size)
            label.refresh()
            values.append(label)

        theta0 = self.start_angle
        theta1 = self.end_angle
        if theta0 == theta1:
            theta1 += 360
        deltaTheta = radians((theta1 - theta0) / float(len(values) - 1))
        theta = radians(theta0)
        r_10 = r - 10
        r_20 = r - 20
        subtick = int(self.subtick)
        if subtick:
            subDeltaTheta = deltaTheta / subtick
        else:
            subDeltaTheta = None
        
        # Draw ticks and values
        for idx, value in enumerate(values):
            first = idx == 0
            last = idx == len(values) - 1
            c = cos(theta)
            s = sin(theta)
            r_1 = r - 1
            
            if (not first and not last
                    or first and self.display_first
                    or last and self.display_last):
                # Draw the big tick
                add(Line(points=(
                    centerx + r_1 * s, centery + r_1 * c,
                    centerx + r_10 * s, centery + r_10 * c,
                ), width=2))
                
                # Numerical value
                t = value.texture
                tw, th = t.size
                add(Rectangle(
                    pos=(centerx + r_20 * s - tw / 2,
                         centery + r_20 * c - th / 2),
                    size=t.size,
                    texture=t))
            
            # Subtick
            if subDeltaTheta and not last:
                subTheta = theta + subDeltaTheta
                for n in range(subtick):
                    subc = cos(subTheta)
                    subs = sin(subTheta)
                    add(Line(points=(
                        centerx + r * subs, centery + r * subc,
                        centerx + r_10 * subs, centery + r_10 * subc),
                             width=0.75))
                    subTheta += subDeltaTheta
            theta += deltaTheta

    def _draw_label(self, *t):
        self._labelIG.clear()
        if not self.label:
            return

        theta = self.start_angle + (
            self.label_angle_ratio * (self.end_angle - self.start_angle))
        c = cos(radians(theta))
        s = sin(radians(theta))
        r = self.r
        r1 = r * self.label_radius_ratio
        
        label = CoreLabel(text=self.label, font_size=self.label_font_size)
        label.refresh()
        t = label.texture
        tw, th = t.size
        
        self._labelIG.add(
            Rectangle(
                pos=(self.centerx + r1 * s - tw / 2,
                     self.centery + r1 * c - th / 2),
                size=(tw, th),
                texture=t))

    def on_needle_image(self, *t):
        self._needle_image = self.needle_image
        full_path = os.path.join(_image_dir, self._needle_image)
        if os.path.isfile(full_path):
            self._needle_image = full_path
        self._draw_needle(*t)

    def _draw_needle(self, *t):
        self._needleIG.clear()
        add = self._needleIG.add
        add(PushMatrix())
        self.rotate = Rotate(origin=(self.centerx, self.centery))
        add(self.rotate)

        if self.value < self.min:
            self.value = self.min
        elif self.value > self.max:
            self.value = self.max
        needleSize = self.r
        s = needleSize * 2
        add(Color(rgba=get_color_from_hex(self.needle_color)))
        add(Rectangle(
            pos=(self.centerx - needleSize, self.centery - needleSize),
            size=(s, s),
            source=self._needle_image))
        add(PopMatrix())
        self.on_value()

    def _draw_background(self, *t):
        self._draw_sectors()
        self._draw_shadow()

    def _draw_full_cadran(self, *t):
        self._draw_outer_cadran()
        self._draw_values()

    def _redraw(self, *args):
        diameter = self.size_gauge
        sa = self.start_angle
        ea = self.end_angle

        r = self.r = diameter / 2
        self.r2 = r * r
        x, y = self.pos
        width, height = self.size
        self.centerx = x + width / 2
        self.centery = y + height / 2

        # Compute value -> angle mapping
        theta0 = sa
        theta1 = ea
        if theta0 == theta1:
            theta1 += 360
        self.a = (float(theta0) - theta1) / (self.max - self.min)
        self.b = -theta0 - self.a * self.min

        # Reverse mapping
        self.startTheta = _halfPi - radians(sa)
        self.endTheta = _halfPi - radians(ea)
        self.direct = self.startTheta < self.endTheta

        self.ra = (self.max - self.min) / ((self.endTheta - self.startTheta)
                                           if sa != ea else _2pi)
        self.rb = self.min - self.ra * self.startTheta

        # Draw
        self._draw_background()
        self._draw_full_cadran()
        self._draw_label()
        self._draw_needle()

    def on_value(self, *t):
        self.rotate.angle = self.a * self.value + self.b
        self._set_shadow_value()

    def get_value(self, pos):
        c = self.center
        x = pos[0] - c[0]
        y = pos[1] - c[1]
        r2 = x * x + y * y
        if r2 > self.r2:
            return
        theta = atan2(y, x)

        min_, max_ = ((self.startTheta, self.endTheta)
                      if self.direct
                      else (self.endTheta, self.startTheta))
        if theta < min_:
            theta += _2pi
        elif theta > max_:
            theta -= _2pi

        v = self.ra * theta + self.rb
        if v >= self.min and v <= self.max:
            return v
        if not self.extendedTouch:
            return

    def collide_point(self, x, y):
        return self.get_value(*(x, y)) is not None

    def on_start_angle(self, *t):
        if self.end_angle - self.start_angle > 360:
            self.start_angle = self.end_angle - 360
        self._redraw()

    def on_end_angle(self, *t):
        if self.end_angle - self.start_angle > 360:
            self.end_angle = self.start_angle + 360
        self._redraw()


# Predefined gauge configurations
class VoltmeterGauge(UniversalGauge):
    """Pre-configured voltmeter gauge."""
    def __init__(self, **kwargs):
        kwargs.setdefault('min', 0)
        kwargs.setdefault('max', 50)
        kwargs.setdefault('tick', 5)
        kwargs.setdefault('needle_color', '#00ff00')
        kwargs.setdefault('meterType', 'Voltmeter')
        kwargs.setdefault('units', 'V')
        kwargs.setdefault('sectors', [0, '#00ff00', 30, '#ffff00', 40, '#ff0000'])
        super(VoltmeterGauge, self).__init__(**kwargs)


class TemperatureGauge(UniversalGauge):
    """Pre-configured temperature gauge."""
    def __init__(self, **kwargs):
        kwargs.setdefault('min', -20)
        kwargs.setdefault('max', 100)
        kwargs.setdefault('tick', 10)
        kwargs.setdefault('needle_color', '#ff4444')
        kwargs.setdefault('meterType', 'Temperature')
        kwargs.setdefault('units', '°C')
        kwargs.setdefault('sectors', [-20, '#0066ff', 0, '#00ff00', 60, '#ffff00', 80, '#ff0000'])
        super(TemperatureGauge, self).__init__(**kwargs)


class SOCGauge(UniversalGauge):
    """Pre-configured State of Charge gauge."""
    def __init__(self, **kwargs):
        kwargs.setdefault('min', 0)
        kwargs.setdefault('max', 100)
        kwargs.setdefault('tick', 10)
        kwargs.setdefault('needle_color', '#0066ff')
        kwargs.setdefault('meterType', 'SOC')
        kwargs.setdefault('units', '%')
        kwargs.setdefault('sectors', [0, '#ff0000', 20, '#ffff00', 50, '#00ff00'])
        super(SOCGauge, self).__init__(**kwargs)


class _X:
    pass


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.slider import Slider
    from kivy.uix.label import Label
    from kivy.clock import Clock
    import random

    class GaugeTestApp(App):
        def build(self):
            main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            
            # Gauge widgets layout
            gauges_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.8), spacing=20)
            
            # Different gauge types
            self.voltmeter = VoltmeterGauge(value=25, size_gauge=200, size_text=12)
            self.temperature = TemperatureGauge(value=45, size_gauge=200, size_text=12)
            self.soc_gauge = SOCGauge(value=75, size_gauge=200, size_text=12)
            
            # Custom gauge
            self.custom_gauge = UniversalGauge(
                value=50,
                min=0,
                max=200,
                tick=20,
                size_gauge=200,
                size_text=12,
                meterType="Speed",
                units="km/h",
                needle_color='#ff00ff',
                sectors=[0, '#00ff00', 60, '#ffff00', 120, '#ff0000']
            )
            
            gauges_layout.add_widget(self.voltmeter)
            gauges_layout.add_widget(self.temperature)
            gauges_layout.add_widget(self.soc_gauge)
            gauges_layout.add_widget(self.custom_gauge)
            
            main_layout.add_widget(gauges_layout)
            
            # Controls
            controls_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2), spacing=5)
            
            # Sliders for each gauge
            sliders = [
                ("Voltage", self.voltmeter, 0, 50),
                ("Temperature", self.temperature, -20, 100),
                ("SOC", self.soc_gauge, 0, 100),
                ("Speed", self.custom_gauge, 0, 200)
            ]
            
            self.sliders = {}
            for name, gauge, min_val, max_val in sliders:
                layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
                layout.add_widget(Label(text=name, size_hint_x=0.2))
                
                slider = Slider(min=min_val, max=max_val, value=gauge.value, size_hint_x=0.8)
                slider.bind(value=lambda instance, value, g=gauge: setattr(g, 'value', value))
                layout.add_widget(slider)
                
                self.sliders[name] = slider
                controls_layout.add_widget(layout)
            
            # Animation button
            btn_animate = Button(text='Animate All', size_hint_y=None, height=40)
            btn_animate.bind(on_press=self.animate_gauges)
            controls_layout.add_widget(btn_animate)
            
            main_layout.add_widget(controls_layout)
            
            return main_layout
        
        def animate_gauges(self, instance):
            """Animate all gauges with random values."""
            targets = {
                self.voltmeter: random.uniform(10, 45),
                self.temperature: random.uniform(0, 90),
                self.soc_gauge: random.uniform(20, 100),
                self.custom_gauge: random.uniform(30, 180)
            }
            
            def animate_step(dt):
                all_done = True
                for gauge, target in targets.items():
                    current = gauge.value
                    diff = target - current
                    if abs(diff) > 1:
                        gauge.value += diff * 0.1
                        all_done = False
                    else:
                        gauge.value = target
                
                # Update sliders
                for name, slider in self.sliders.items():
                    if name == "Voltage":
                        slider.value = self.voltmeter.value
                    elif name == "Temperature":
                        slider.value = self.temperature.value
                    elif name == "SOC":
                        slider.value = self.soc_gauge.value
                    elif name == "Speed":
                        slider.value = self.custom_gauge.value
                
                return not all_done
            
            Clock.schedule_interval(animate_step, 0.05)

    GaugeTestApp().run()
