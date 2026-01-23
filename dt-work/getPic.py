import cv2

#sudo apt install -y python3-opencv
# Відкриваємо /dev/video1
cap = cv2.VideoCapture(1, cv2.CAP_V4L2)

# ВАЖЛИВО: На Allwinner краще спочатку встановити формат, 
# але оскільки ми вже налаштували його через bash-скрипт, 
# OpenCV має просто "підхопити" поточний стан.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"UYVY"))

# Очищуємо буфери (пропускаємо перші 20 кадрів)
# Це критично для 1080p, щоб дочекатися реальних даних від DMA
print("Прогрів камери...")
for _ in range(10):
    cap.grab() 

# Тепер читаємо актуальний кадр
ret, frame = cap.retrieve()

if ret and frame is not None:
    # Якщо кадр чорний, перевіримо чи є в ньому хоч якісь дані
    #if np.sum(frame) == 0:
    #    print("Попередження: Отримано порожній (чорний) кадр")
    #else:
    cv2.imwrite("framePy_fixed.png", frame)
    print(f"Успіх! Розмір кадру: {frame.shape[1]}x{frame.shape[0]}")
else:
    print("Не вдалося отримати кадр")

cap.release()