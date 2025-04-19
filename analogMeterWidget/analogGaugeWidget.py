
from kivy.uix.scatter import Scatter
from kivy.properties import NumericProperty, BoundedNumericProperty
from kivy.uix.image import Image
from kivy.uix.label import Label

class analog_meter(Scatter):
    value = NumericProperty(10)
    size_gauge = BoundedNumericProperty(512, min=128, max=512, errorvalue=128)
    def __init__(self, **kwargs):
        super(analog_meter, self).__init__(**kwargs)
        self.bind(value=self._update)
        self._display = Scatter(
            size=(150, 86),
            do_rotation=False,
            do_scale=False,
            do_translation=False
        )
        self._needle = Scatter(
            size=(4, 67),
            do_rotation=False,
            do_scale=False,
            do_translation=False
        )
        self.lcd_display = Scatter(
            size=(150, 50),
            do_rotation=False,
            do_scale=False,
            do_translation=False
        )

        bg_image = Image(source='analogMeterWidget/analog_display_150.png', size=(150, 86), pos=(0, 0))
        _img_needle = Image(source="analogMeterWidget/arrow_small.png", size=(4, 134))

        lcd_bg = Image(source='analogMeterWidget/lcd_bg.png', size=(150, 50), pos=(0, -55))
        self.pressure_label = Label(text='000', font_name='analogMeterWidget/lcd.ttf', halign="center",
                                  font_size=36, pos=(25, -76), markup=True)
        
        
        self._display.add_widget(bg_image)
        self._needle.add_widget(_img_needle)

        self.lcd_display.add_widget(lcd_bg)
        self.lcd_display.add_widget(self.pressure_label)
        self.add_widget(self._display)
        self.add_widget(self._needle)
        self.add_widget(self.lcd_display)

    def _update(self, *args):
        niddle_angle = 78 - (self.value / 3.8461)
        self._needle.center_x = self._display.center_x
        self._needle.center_y = self._display.center_y - 32
        self._needle.rotation = niddle_angle
        if (self.value <= 160):
            text_color = 'ff0000'
        else:
            text_color = 'ffffff'
        self.pressure_label.text='[color=' + text_color + ']' +str(self.value/100) + ' Bar' + '[/color]'
        pass