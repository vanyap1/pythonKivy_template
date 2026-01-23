from lib import LCD_1inch28
from PIL import Image as PILImage
from kivy.config import Config
Config.set("graphics", "multisamples", "4")
Config.set("graphics", "width", "240")
Config.set("graphics", "height", "240")
Config.set("graphics", "resizable", False)

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock


class MyBlueApp(App):
    def build(self):
        self.disp = LCD_1inch28.LCD_1inch28()
        self.disp.Init()
        self.disp.clear()

        root = FloatLayout(size=(240, 240))

        with root.canvas.before:
            Color(0.05, 0.06, 0.10, 1)
            self.bg_circle = Ellipse(pos=(0, 0), size=(240, 240))

        with root.canvas:
            Color(0.2, 0.2, 0.25, 1)
            self.ring_bg = Line(circle=(120, 120, 95, 0, 360), width=10)
            Color(0.2, 0.9, 0.6, 1)
            self.ring_fg = Line(
                circle=(120, 120, 95, 0, 0),
                width=10,
                cap="round",
                joint="round",
            )

        self.title_label = Label(
            text="NanoPi Duo2",
            font_size="14sp",
            color=(0.8, 0.9, 1, 1),
            font_name="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            pos_hint={"center_x": 0.5, "center_y": 0.7},
        )

        self.value = Label(
            text="00:00",
            font_size="28sp",
            color=(1, 1, 1, 1),
            font_name="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            pos_hint={"center_x": 0.5, "center_y": 0.52},
        )

        self.footer = Label(
            text="PROGRESS",
            font_size="12sp",
            color=(0.6, 0.8, 0.9, 1),
            font_name="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            pos_hint={"center_x": 0.5, "center_y": 0.22},
        )

        root.add_widget(self.title_label)
        root.add_widget(self.value)
        root.add_widget(self.footer)

        self.elapsed = 0
        return root

    def on_start(self):
        self._set_message("HELLO!", "READY", "LCD ONLINE")
        self._draw_screen(0)
        Clock.schedule_once(self._clear_greeting, 3.5)
        Clock.schedule_interval(self._tick, 1)
        Clock.schedule_interval(self._draw_screen, 0.25)

    def on_stop(self):
        self._set_message("GOODBYE", "BYE BYE", "POWERING DOWN")
        self._draw_screen(0)

    def _clear_greeting(self, dt):
        self.elapsed = 0
        self._set_message("NanoPi Duo2", "00:00", "PROGRESS")

    def _set_message(self, title, value, footer):
        self.title_label.text = title
        self.value.text = value
        self.footer.text = footer

    def _tick(self, dt):
        self.elapsed += 1
        minutes = self.elapsed // 60
        seconds = self.elapsed % 60
        self.value.text = f"{minutes:02d}:{seconds:02d}"

        progress = (self.elapsed % 60) / 60.0
        angle = 360 * progress
        self.ring_fg.circle = (120, 120, 95, 0, angle)

    def _draw_screen(self, dt):
        kivy_image = self.root.export_as_image()
        texture = kivy_image.texture
        texture.flip_vertical()
        pil_image = PILImage.frombytes("RGBA", texture.size, texture.pixels)
        pil_image = pil_image.convert("RGB")
        self.disp.ShowImage(pil_image)


if __name__ == "__main__":
    MyBlueApp().run()