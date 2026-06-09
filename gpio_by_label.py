import gpiod
import time

# Шукаємо лінії в системі суто за їхніми DT-іменами
btn_line = gpiod.find_line("btn_user")
relay_line = gpiod.find_line("pcf_p3")
led_line = gpiod.find_line("pcf_p7")
if not btn_line:
    print("dev cannot find line for user button (btn_user). Check your DT configuration.")
    exit(1)
if not relay_line:
    print("dev cannot find line for relay (pcf_p3). Check your DT configuration.")
    exit(1)
if not led_line:
    print("dev cannot find line for LED (pcf_p7). Check your DT configuration.")
    exit(1)

# Запитуємо конфігурацію
btn_line.request(consumer="python_app", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)
relay_line.request(consumer="python_app", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])
led_line.request(consumer="python_app", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[1])

print(f"Successfully initialized GPIO lines: btn_user (input), pcf_p3 (output), pcf_p7 (output).")

# Тепер працюємо як зазвичай
led_state = 0
while True:
    btn_state = btn_line.get_value()
    relay_line.set_value(1 if btn_state == 0 else 0) # увімкнути реле, якщо натиснута кнопка
    led_state = not led_state  # інвертуємо стан світлодіода
    led_line.set_value(led_state)
    time.sleep(0.1)