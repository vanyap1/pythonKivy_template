import os
import select  # Потрібно для неблокуючої перевірки кнопок
import time
import gpiod
from evdev import InputDevice, ecodes

# gpiodetect
# gpioinfo gpiochip2
# sudo evtest /dev/input/by-path/platform-gpio-keys-event
# CAN
# sudo ip link set can0 up type can bitrate 500000
# candump can0
# cansniffer can0

# --- Налаштування кнопок (evdev) ---
DEVICE_PATH = '/dev/input/by-path/platform-gpio-keys-event'
BTN_0_CODE = 256
BTN_1_CODE = 257

# Ініціалізуємо пристрій введення (обробка помилки, якщо немає прав/файлу)
dev = None
try:
    dev = InputDevice(DEVICE_PATH)
except (PermissionError, FileNotFoundError) as e:
    print(f"Попередження: Не вдалося відкрити кнопки ({e}). Запустіть від sudo.")

# --- Ваші налаштування GPIO (gpiod) ---
CHIP = "gpiochip2"

OUTPUT_PINS = [
    ("PA0", 0),
    ("PA1", 1),
    ("PA2", 2),
    ("PA3", 3),
    ("PA4", 4),
    ("PA5", 5),
    ("PA6", 6),
    ("PA7", 7)
]

INPUT_PINS = [
    ("PB0", 8),
    ("PB1", 9),
    ("PB2", 10),
    ("PB3", 11),
    ("PB4", 12),
    ("PB5", 13),
    ("PB6", 14),
    ("PB7", 15)
]

chip = gpiod.Chip(CHIP)

out_lines = {name: chip.get_line(offset) for name, offset in OUTPUT_PINS}
in_lines = {name: chip.get_line(offset) for name, offset in INPUT_PINS}

for name, line in out_lines.items():
    line.request(consumer=name, type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

for name, line in in_lines.items():
    line.request(
        consumer=name,
        type=gpiod.LINE_REQ_DIR_IN,
        flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP,
    )

state = 0
pa7_state = 0  # Окрема змінна для стану PA7

while True:
    state = 0 if state else 1

    # --- Опитування кнопок без блокування циклу ---
    if dev:
        # Перевіряємо, чи є в буфері файлу якісь івенти прямо зараз
        r, w, x = select.select([dev], [], [], 0)
        if r:
            for event in dev.read():
                # Нас цікавить ТІЛЬКИ момент натискання (value == 1)
                if event.type == ecodes.EV_KEY and event.value == 1:
                    if event.code in (BTN_0_CODE, BTN_1_CODE):
                        pa7_state = 0 if pa7_state else 1  # Інвертуємо стан PA7
                        print(f"[Кнопка] PA7 інвертовано! Новий стан: {pa7_state}")

    # --- Керування виходами ---
    out_lines["PA0"].set_value(state)
    out_lines["PA1"].set_value(state)
    out_lines["PA2"].set_value(state)
    out_lines["PA3"].set_value(state)
    out_lines["PA4"].set_value(state)
    out_lines["PA5"].set_value(state)
    out_lines["PA6"].set_value(state)
    
    # PA7 більше не бере участі в блиманні, а керується окремою змінною pa7_state
    out_lines["PA7"].set_value(pa7_state)

    # --- Читання входів ---
    input_state = (
        f"{in_lines['PB0'].get_value()}"
        f"{in_lines['PB1'].get_value()}"
        f"{in_lines['PB2'].get_value()}"
        f"{in_lines['PB3'].get_value()}"
    )
    print(input_state)

    time.sleep(0.1)