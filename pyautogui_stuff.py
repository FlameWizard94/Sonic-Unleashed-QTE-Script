import pyautogui
import time
import threading


def data():
    screenWidth, screenHeight = pyautogui.size() # Get the size of the primary monitor.
    currentMouseX, currentMouseY = pyautogui.position() # Get the XY position of the mouse.
    print(f'''\nWidth: {screenWidth}\nHeigth: {screenHeight}\nMouse position: ({currentMouseX}, {currentMouseY})\nRGB: {pyautogui.pixel(currentMouseX, currentMouseY)}''')
    
# Use a threading.Event to control the loop
stop_event = threading.Event()

def listen_for_input(event):
    input()  # Wait for user input
    event.set()  # Set the event to signal the main loop to stop

# Start the input listener in a separate thread
input_thread = threading.Thread(target=listen_for_input, args=(stop_event,))
input_thread.start()

while not stop_event.is_set():  # Continue running until the event is set
    data()
    time.sleep(3)
