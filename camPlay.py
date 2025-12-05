import struct
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import threading
import sys
import os
from datetime import datetime
from glob import glob

# Текст на екрані : фізичне призначення
BUTTON_MAPPING = {
    312: ("MENU", 312),       # L2 -> MENU
    310: ("SELECT", 310),     # L -> SELECT
    311: ("START", 311),      # R -> START
    306: ("Y", 306),          # C -> Y
    307: ("X", 307),          # X -> X
    304: ("A", 304),          # A -> A
    305: ("B", 305),          # B -> B
    308: ("L1", 308),         # Y -> L1
    314: ("L2", 314),         # SELECT -> L2
    315: ("R2", 315),         # START -> R2
    309: ("R1", 309),         # Z -> R1
    354: ("GOTO", 354),       # GOTO -> GOTO
    313: ("STIK Press", 313)  # R2 -> STIK Press
}

button_states = {}  # зберігає стан кнопок

class CameraGamepadApp(App):
    def build(self):
        # Головний layout - FloatLayout для накладання
        main_layout = FloatLayout()
        
        # Відео з камери / переглядач фото (фоновий шар)
        self.camera_widget = Image(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        main_layout.add_widget(self.camera_widget)
        
        # Help текст вверху екрану (жовтий, оверлей)
        self.help_widget = Label(
            size_hint=(1, None),
            height=0,  # Спочатку сховано
            pos_hint={'x': 0, 'top': 1},
            color=(1, 1, 0, 1),  # жовтий колір
            text="",
            font_size='12sp',
            markup=True
        )
        main_layout.add_widget(self.help_widget)
        
        # OSD текст внизу екрану (зелено-голубий, оверлей)
        self.info_widget = Label(
            size_hint=(1, None),
            height=30,
            pos_hint={'x': 0, 'y': 0},
            color=(0, 1, 0.8, 1),  # зелено-голубий колір
            text="Очікування даних з геймпада... | MENU+START = вихід"
        )
        main_layout.add_widget(self.info_widget)
        
        # Ініціалізація камери
        self.capture = cv2.VideoCapture('/dev/video4', cv2.CAP_V4L2)
        if not self.capture.isOpened():
            self.info_widget.text = "ERROR: Cannot open camera /dev/video0"
        else:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.info_widget.text = f"Camera: {actual_width}x{actual_height} | Press X for help"
            Clock.schedule_interval(self.update_camera, 1.0 / 30.0)
        
        # Ініціалізація стану кнопок
        for code in BUTTON_MAPPING.keys():
            button_states[code] = 0
        
        # Стан стіка та хрестовини
        self.stick_x = 0
        self.stick_y = 0
        self.hat_x = 0
        self.hat_y = 0
        
        # Стан трансформацій картинки
        self.flip_vertical = False
        self.rotation_angle = 0  # 0, 90, 180, 270
        
        # Для відстеження попереднього стану кнопок
        self.prev_r1_state = 0
        self.prev_r2_state = 0
        self.prev_l1_state = 0
        self.prev_l2_state = 0
        self.prev_b_state = 0
        self.prev_a_state = 0
        self.prev_y_state = 0
        self.prev_x_state = 0
        self.prev_hat_x = 0
        
        # Поточний кадр для збереження
        self.current_frame = None
        
        # Створюємо папку img якщо не існує
        self.img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        
        # Режим роботи: 'camera' або 'gallery'
        self.mode = 'camera'
        self.gallery_images = []
        self.gallery_index = 0
        
        # Стан показу допомоги
        self.show_help = False
        
        # Запуск потоку читання геймпада
        threading.Thread(target=self.read_gamepad, daemon=True).start()
        
        return main_layout
    
    def toggle_help(self):
        self.show_help = not self.show_help
        if self.show_help:
            self.help_widget.height = 80
            if self.mode == 'camera':
                help_text = "[b]CAMERA MODE:[/b]\n"
                help_text += "L1=Rotate 90° | L2=Reset rotation | R1=Flip vertical | R2=Reset flip\n"
                help_text += "B=Save photo | A=Open gallery | X=Toggle help | MENU+START=Exit\n"
                help_text += f"Screen: 640x480 | Mode: Camera | Flip: {self.flip_vertical} | Rotation: {self.rotation_angle}°"
            else:
                help_text = "[b]GALLERY MODE:[/b]\n"
                help_text += "D-Pad LEFT/RIGHT=Navigate photos | Y=Back to camera | X=Toggle help\n"
                help_text += f"Total images: {len(self.gallery_images)} | Current: {self.gallery_index + 1}\n"
                help_text += "MENU+START=Exit"
            self.help_widget.text = help_text
        else:
            self.help_widget.height = 0
            self.help_widget.text = ""
    
    def update_camera(self, dt):
        if self.mode == 'gallery':
            return  # В режимі галереї не оновлюємо камеру
            
        if not self.capture.isOpened():
            return
            
        ret, frame = self.capture.read()
        if ret:
            # Конвертуємо в grayscale (монохромне для тепловізора)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Беремо лише верхню половину (бо зображення дублюється)
            height = gray.shape[0]
            half_frame = gray[0:height//2, :]
            
            # Масштабуємо до 640x480
            scaled_frame = cv2.resize(half_frame, (640, 480), interpolation=cv2.INTER_LINEAR)
            
            # Застосовуємо flip якщо потрібно
            if self.flip_vertical:
                display_frame = scaled_frame.copy()
            else:
                display_frame = cv2.flip(scaled_frame, 0)
            
            # Застосовуємо поворот
            if self.rotation_angle == 90:
                display_frame = cv2.rotate(display_frame, cv2.ROTATE_90_CLOCKWISE)
            elif self.rotation_angle == 180:
                display_frame = cv2.rotate(display_frame, cv2.ROTATE_180)
            elif self.rotation_angle == 270:
                display_frame = cv2.rotate(display_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Зберігаємо поточний кадр
            self.current_frame = display_frame.copy()
            
            # Визначаємо розміри текстури залежно від повороту
            if self.rotation_angle in [90, 270]:
                texture_size = (480, 640)  # поміняні місцями для повороту 90/270
            else:
                texture_size = (640, 480)
            
            buf = display_frame.tobytes()
            texture = Texture.create(size=texture_size, colorfmt='luminance')
            texture.blit_buffer(buf, colorfmt='luminance', bufferfmt='ubyte')
            self.camera_widget.texture = texture
    
    def save_frame(self):
        if self.current_frame is not None:
            # Генеруємо ім'я файлу з поточною датою та часом
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"frame_{timestamp}.png"
            filepath = os.path.join(self.img_dir, filename)
            
            # Зберігаємо зображення
            cv2.imwrite(filepath, self.current_frame)
            self.update_info(f"Saved: {filename}")
    
    def enter_gallery_mode(self):
        # Завантажуємо список зображень
        self.gallery_images = sorted(glob(os.path.join(self.img_dir, '*.png')))
        
        if not self.gallery_images:
            self.update_info("No images in gallery")
            return
        
        self.mode = 'gallery'
        self.gallery_index = len(self.gallery_images) - 1  # Останнє зображення
        
        # Оновлюємо help якщо показано
        if self.show_help:
            self.toggle_help()
            self.toggle_help()
        
        self.show_gallery_image()
    
    def exit_gallery_mode(self):
        self.mode = 'camera'
        
        # Оновлюємо help якщо показано
        if self.show_help:
            self.toggle_help()
            self.toggle_help()
        
        self.update_info("Back to camera mode")
    
    def show_gallery_image(self):
        if not self.gallery_images:
            return
        
        img_path = self.gallery_images[self.gallery_index]
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        
        if img is not None:
            # Масштабуємо зображення до розміру екрану (зберігаючи пропорції)
            h, w = img.shape
            if h > w:
                # Вертикальне зображення
                texture_size = (480, 640)
            else:
                # Горизонтальне зображення
                texture_size = (640, 480)
            
            # Масштабуємо
            img_resized = cv2.resize(img, texture_size, interpolation=cv2.INTER_LINEAR)
            
            buf = cv2.flip(img_resized, 0).tobytes()
            texture = Texture.create(size=texture_size, colorfmt='luminance')
            texture.blit_buffer(buf, colorfmt='luminance', bufferfmt='ubyte')
            self.camera_widget.texture = texture
            
            filename = os.path.basename(img_path)
            file_size = os.path.getsize(img_path) / 1024  # KB
            self.update_info(f"Gallery [{self.gallery_index + 1}/{len(self.gallery_images)}]: {filename} ({file_size:.1f}KB) | Size: {w}x{h}")
    
    def gallery_next(self):
        if self.gallery_images:
            self.gallery_index = (self.gallery_index + 1) % len(self.gallery_images)
            self.show_gallery_image()
    
    def gallery_prev(self):
        if self.gallery_images:
            self.gallery_index = (self.gallery_index - 1) % len(self.gallery_images)
            self.show_gallery_image()
    
    def read_gamepad(self):
        try:
            with open("/dev/input/event1", "rb") as f:
                EVENT_SIZE = struct.calcsize("llHHi")
                while True:
                    data = f.read(EVENT_SIZE)
                    if not data:
                        continue
                    tv_sec, tv_usec, type, code, value = struct.unpack("llHHi", data)
                    
                    if type == 1 and code in BUTTON_MAPPING:
                        Clock.schedule_once(lambda dt, c=code, v=value: self.update_button(c, v))
                    elif type == 3:
                        if code == 2:
                            Clock.schedule_once(lambda dt, v=value: self.update_stick(v, 'y'))
                        elif code == 3:
                            Clock.schedule_once(lambda dt, v=value: self.update_stick(v, 'x'))
                        elif code == 16:
                            Clock.schedule_once(lambda dt, v=value: self.update_hat(v, 'x'))
                        elif code == 17:
                            Clock.schedule_once(lambda dt, v=value: self.update_hat(v, 'y'))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_info(f"Помилка геймпада: {e}"))
    
    def update_button(self, code, value):
        button_states[code] = value
        
        # X (код 307) - показати/сховати допомогу
        if code == 307 and value == 1 and self.prev_x_state == 0:
            self.toggle_help()
        self.prev_x_state = button_states.get(307, 0)
        
        # A (код 304) - відкрити галерею
        if code == 304 and value == 1 and self.prev_a_state == 0:
            if self.mode == 'camera':
                self.enter_gallery_mode()
        self.prev_a_state = button_states.get(304, 0)
        
        # Y (код 306) - повернутися до камери
        if code == 306 and value == 1 and self.prev_y_state == 0:
            if self.mode == 'gallery':
                self.exit_gallery_mode()
        self.prev_y_state = button_states.get(306, 0)
        
        # Кнопки для камери
        if self.mode == 'camera':
            # L1 (код 308) - поворот на 90 градусів за годинниковою стрілкою
            if code == 308 and value == 1 and self.prev_l1_state == 0:
                self.rotation_angle = (self.rotation_angle + 90) % 360
                self.update_info(f"Rotation: {self.rotation_angle}°")
                if self.show_help:
                    self.toggle_help()
                    self.toggle_help()
            self.prev_l1_state = button_states.get(308, 0)
            
            # L2 (код 314) - скинути поворот до 0
            if code == 314 and value == 1 and self.prev_l2_state == 0:
                self.rotation_angle = 0
                self.update_info("Rotation reset to 0°")
                if self.show_help:
                    self.toggle_help()
                    self.toggle_help()
            self.prev_l2_state = button_states.get(314, 0)
            
            # R1 (код 309) - перевернути вертикально (toggle при натисканні)
            if code == 309 and value == 1 and self.prev_r1_state == 0:
                self.flip_vertical = not self.flip_vertical
                flip_status = "ON" if self.flip_vertical else "OFF"
                self.update_info(f"Vertical flip: {flip_status}")
                if self.show_help:
                    self.toggle_help()
                    self.toggle_help()
            self.prev_r1_state = button_states.get(309, 0)
            
            # R2 (код 315) - скинути flip до звичайного (при натисканні)
            if code == 315 and value == 1 and self.prev_r2_state == 0:
                self.flip_vertical = False
                self.update_info("Flip reset to normal")
                if self.show_help:
                    self.toggle_help()
                    self.toggle_help()
            self.prev_r2_state = button_states.get(315, 0)
            
            # B (код 305) - зберегти кадр (при натисканні)
            if code == 305 and value == 1 and self.prev_b_state == 0:
                self.save_frame()
            self.prev_b_state = button_states.get(305, 0)
        
        # Перевіряємо одночасне натискання MENU і START
        if button_states.get(312, 0) and button_states.get(311, 0):
            self.update_info("Вихід: MENU+START")
            Clock.schedule_once(lambda dt: self.stop(), 0.5)
            return
        
        if self.mode == 'camera':
            self.update_info_display()
    
    def update_stick(self, value, axis):
        if axis == 'x':
            self.stick_x = value
        else:
            self.stick_y = value
        if self.mode == 'camera':
            self.update_info_display()
    
    def update_hat(self, value, axis):
        if axis == 'x':
            self.hat_x = value
            # D-Pad ліво/право для перегляду галереї
            if self.mode == 'gallery':
                if value == 1 and self.prev_hat_x != 1:  # Право
                    self.gallery_next()
                elif value == -1 and self.prev_hat_x != -1:  # Ліво
                    self.gallery_prev()
            self.prev_hat_x = value
        else:
            self.hat_y = value
        if self.mode == 'camera':
            self.update_info_display()
    
    def update_info_display(self):
        # Формуємо текст в один рядок
        pressed_buttons = [BUTTON_MAPPING[code][0] for code, state in button_states.items() if state]
        buttons_text = ", ".join(pressed_buttons) if pressed_buttons else "---"
        
        flip_status = "FLIP" if self.flip_vertical else "NORM"
        
        # Підраховуємо кількість збережених фото
        photo_count = len(glob(os.path.join(self.img_dir, '*.png')))
        
        info_text = f"BTN: {buttons_text} | Стік: X={self.stick_x} Y={self.stick_y} | D-Pad: X={self.hat_x} Y={self.hat_y} | {flip_status} | ROT:{self.rotation_angle}° | Photos:{photo_count}"
        
        self.update_info(info_text)
    
    def update_info(self, text):
        self.info_widget.text = text
    
    def on_stop(self):
        if hasattr(self, 'capture') and self.capture is not None:
            self.capture.release()
        sys.exit(0)

if __name__ == '__main__':
    CameraGamepadApp().run()