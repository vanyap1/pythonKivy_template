#!/usr/bin/env python3
import cv2
import sys

print("OpenCV version:", cv2.__version__)
print("Available backends:", cv2.videoio_registry.getBackends())

# Спробуємо відкрити камеру різними способами
print("\n=== Testing /dev/video0 with CAP_V4L2 ===")
cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L2)
print("isOpened():", cap.isOpened())

if cap.isOpened():
    print("Frame width:", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("Frame height:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print("FPS:", cap.get(cv2.CAP_PROP_FPS))
    print("Format:", cap.get(cv2.CAP_PROP_FORMAT))
    
    # Спробуємо зчитати кадр
    print("\n=== Reading frame ===")
    ret, frame = cap.read()
    print("Read successful:", ret)
    if ret:
        print("Frame shape:", frame.shape)
        print("Frame dtype:", frame.dtype)
    else:
        print("ERROR: Cannot read frame!")
    
    cap.release()
else:
    print("ERROR: Cannot open camera!")

print("\n=== Testing with default backend ===")
cap2 = cv2.VideoCapture('/dev/video4')
print("isOpened():", cap2.isOpened())
if cap2.isOpened():
    ret, frame = cap2.read()
    print("Read successful:", ret)
    if ret:
        print("Frame shape:", frame.shape)
    cap2.release()

print("\n=== Testing with index 4 ===")
cap3 = cv2.VideoCapture(4, cv2.CAP_V4L2)
print("isOpened():", cap3.isOpened())
if cap3.isOpened():
    ret, frame = cap3.read()
    print("Read successful:", ret)
    if ret:
        print("Frame shape:", frame.shape)
    cap3.release()
