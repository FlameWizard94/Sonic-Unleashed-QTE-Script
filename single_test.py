import cv2
import numpy as np
import pyautogui
import pygame
import threading
import time
from pyscreeze import ImageNotFoundException

#Eraser in gimp fucks with image accuracy


num_found = {'x':0, 'circle':0, 'square':0, 'triangle':0, 'l1':0, 'r1':0, 'pink':0}
accuracy = {'x':0, 'circle':0, 'square':0, 'triangle':0, 'l1':0, 'r1':0, 'pink':0}

def detect_image(name):
    global num_found
    global accuracy

    template = cv2.imread(f'buttons/playstation/{name}.png', 0)
    screen = np.array(pyautogui.screenshot())
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    template = cv2.resize(template, None, fx=0.3, fy=0.3)

    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= 0.81:  # Adjust confidence threshold
        print(f"{name} found at {max_loc}")
        pyautogui.screenshot(f'found/{name}_{num_found[name]}.png')
        num_found[name] += 1
        accuracy[name] += max_val
    else:
        print(f"{name} not found.")

    print(f'result: -- {max_val}\n')

def listen_for_input(event):
    input()
    event.set()

stop_event = threading.Event()

input_thread = threading.Thread(target=listen_for_input, args=(stop_event,))
input_thread.start()

while not stop_event.is_set():
    detect_image('square')
    time.sleep(3.02)

for name, v in accuracy.items():
    if v > 0:
        print(f'{name} accuracy: {v / num_found[name]}')

    else:
        print(f'{name} not found')