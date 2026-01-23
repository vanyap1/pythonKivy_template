from kivy.config import Config

Config.set('graphics', 'width', '240')
Config.set('graphics', 'height', '240')
Config.set('graphics', 'resizable', False)

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

class MyBlueApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        with layout.canvas.before:
            Color(0, 0, 0.5, 1)  
            self.rect = Rectangle(size=(240, 240), pos=layout.pos)
        
        layout.bind(size=self._update_rect, pos=self._update_rect)

        self.elapsed = 0
        self.label = Label(
            text="Таймер: 0 с",
            font_size='14sp',
            color=(1, 1, 1, 1),
            font_name="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        )

        layout.add_widget(self.label)
        
        return layout

    def on_start(self):
        Clock.schedule_interval(self._tick, 1)
        Clock.schedule_interval(self._save_snapshot, 1)

    def _save_snapshot(self, dt):
        self.root.export_to_png("kivy_test.png")

    def _tick(self, dt):
        self.elapsed += 1
        self.label.text = f"Таймер: {self.elapsed} с"

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

if __name__ == '__main__':
    MyBlueApp().run()