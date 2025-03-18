import cv2
import numpy as np
import pyautogui
import vgamepad
import threading
import time
from pyscreeze import ImageNotFoundException
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to press a button on the virtual gamepad
def button_press(press, buttons, gamepad):
    press = press[0]  # Remove the number suffix (e.g., 'square69' -> 's')

    gamepad.press_button(button=buttons[press])
    gamepad.update()
    time.sleep(0.05)
    gamepad.release_button(button=buttons[press])
    gamepad.update()
    time.sleep(0.1)  # Avoid press overlap


# Function to detect a specific button
def detect_button(button, template, stop_event, distance):
    global num_found, current, searched, screenshot, logs, check
    while not stop_event.is_set():
        confidence = 0.84
        if button == 'circle':
            confidence -= 0.06
        with lock:
            # Wait until this button's searched value is 0
            while searched[button] == 1 and not stop_event.is_set():
                condition.wait(timeout=0.1)  

        elements = []
        #start = time.time()
        try:
            # Find all instances of a button
            for element in pyautogui.locateAll(template, screenshot, confidence=confidence):
                # Make sure same buttons aren't repeated (e.g., program thinks there's another one a pixel away)
                if all(map(lambda x: pow(element.left - x.left, 2) + pow(element.top - x.top, 2) > distance, elements)):
                    elements.append(element)
                

            with lock:
                # Add all instances of the button to current
                for element in elements:
                    if not any(abs(int(element.left) - current_button) < distance for current_button in current.values()): # Makes sure only new buttons are added
                        current[f"{button}{num_found[button]}"] = int(element.left)
                        num_found[button] += 1
                        check = 1 # If new button found, signal check for more

                        logs += f"found {button} at: {element.left}\n\n"

                searched[button] = 1
                condition.notify_all()

        except ImageNotFoundException:
            with lock:
                # Mark this button as searched
                searched[button] = 1
                condition.notify_all()
        #time.sleep(0.1)  # Small delay to avoid excessive CPU usage


# Function to process the current dictionary and press buttons in order
def process_current(buttons, gamepad, region):
    global current, searched, screenshot, logs, check

    while not stop_event.is_set():
        with lock:
            # Wait until all buttons have been searched
            while (not all(value == 1 for value in searched.values())) and not stop_event.is_set():
                condition.wait(timeout=0.1)  

            if check == 0:
                #If we double checked
                if current:
                    logs += f'Checked, Currently {current}\n\n'
                # Sort buttons by their x-coordinate (left to right)
                order = {k: v for k, v in sorted(current.items(), key=lambda item: item[1])}

                for button, place in order.items():
                    button_press(button, buttons, gamepad)
                    logs += f'{button} at {place} pressed\n\n'

                if order:
                    logs += f'\nOrder pressed: {list(order.keys())}\n\n'
                    logs += f'-----------------------------------------------------------------------------------------\n\n'

                time.sleep(0.5) # Forced wait. Without it script fucks up scenerios with 2 QTEs in a row. Teseted in Empire City DLC Act 1
                                # Mistakes 3rd button in the first QTE with the fourth button in the next one.
                                # Takes about 23 frames (less than half a second) between the last button press, and that button faidn away
                                

                # Clear current and reset searched
                current.clear()

                # Take a new screenshot
                snapshot = pyautogui.screenshot(region=region)
                screenshot = np.array(snapshot) 

                for button in searched:
                    searched[button] = 0
                condition.notify_all()  # Notify all waiting threads


            else:
                # Make a new screenshot to double check that there's no other buttons
                logs += f'Currently {current}\n\nDouble Checking\n\n'
                for button in searched.keys():
                    searched[button] = 0

                time.sleep(0.1) # Wait so screenshot has best chance of seeing other buttons
                snapshot = pyautogui.screenshot(region=region)
                screenshot = np.array(snapshot)
                check = 0
                condition.notify_all()

def setup():
    region = () # Where QTE buttons appear
    buttons = {} # Controller buttons
    images = {} # Where button images are stored
    gamepad  = None # Virtual controller that performs QTEs
    num_found = {} # Stores total buttons found during operation
    searched = {} # Track if each button has been searched (0 = searched, 1 = searched)
    logs = '' # You can see script info in the file QTE_logs
    button_type = None

    screen_width, screen_height = pyautogui.size() # Get the size of the primary monitor.

    x = int(screen_width * 0.2296875)
    y = int(screen_height * 0.39166666666666666)
    right = int(screen_width * 0.5104166666666666)
    down = int(screen_height * 0.1675925925925926)
    region = (x, y, right, down) # Where QTE buttons appear
    top_left = (x, y)
    top_right = (x + right, y)
    bottom_left = (x, y + down)
    bottom_right = (x + right, y + down)

    while button_type != 1 and button_type != 0:
        try:
            button_type = int(input(f"\nWhich buttons do you use?\nEnter 1 for Playstation\nEnter 0 for Xbox\n\n"))
        except:
            pass
        if button_type == 1:
            buttons = {
                's': vgamepad.DS4_BUTTONS.DS4_BUTTON_SQUARE,
                't': vgamepad.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
                'X': vgamepad.DS4_BUTTONS.DS4_BUTTON_CROSS,
                'c': vgamepad.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
                'r': vgamepad.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
                'l': vgamepad.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT
            }
            images = {
                'square': 'buttons/playstation/square.png',
                'triangle': 'buttons/playstation/triangle.png',
                'X': 'buttons/playstation/X.png',
                'circle': 'buttons/playstation/circle.png',
                'r1': 'buttons/playstation/r1.png',
                'l1': 'buttons/playstation/l1.png'
            }
            num_found = {'X': 0, 'circle': 0, 'square': 0, 'triangle': 0, 'r1': 0, 'l1': 0}
            searched = {'square': 0, 'circle': 0, 'X': 0, 'triangle': 0, 'r1': 0, 'l1': 0}
            gamepad = vgamepad.VDS4Gamepad()

            logs += f'Used Playstation Buttons\n\n'
            print('Using Playstation buttons\n')

        elif button_type == 0:
            buttons = {
                'a': vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_A,
                'b': vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_B,
                'X': vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_X,
                'y': vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                'r': vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                'l': vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER
            }
            images = {
                'a': 'buttons/xbox/a.png', 
                'b': 'buttons/xbox/b.png',  
                'X': 'buttons/xbox/x.png', 
                'y': 'buttons/xbox/y.png',  
                'rb': 'buttons/xbox/rb.png',  
                'lb': 'buttons/xbox/lb.png'   
            }
            num_found = {'a': 0, 'b': 0, 'X': 0, 'y': 0, 'rb': 0, 'lb': 0}
            searched = {'a': 0, 'b': 0, 'X': 0, 'y': 0, 'rb': 0, 'lb': 0}
            gamepad = vgamepad.VX360Gamepad()

            logs += f'Used Xbox Buttons\n\n'
            print('Using Xbox buttons\n')

        else:
            print("Please enter 1 for Playstation or 0 for Xbox")

    logs += f'Region searched: {region}\n'
    logs += f'Top left Corner: {top_left}\n'
    logs += f'Top Right Corner: {top_right}\n'
    logs += f'Bottom left Corner: {bottom_left}\n'
    logs += f'Bottom Right Corner: {bottom_right}\n\n'

    return region, buttons, images, gamepad, num_found, searched, logs


# Function to listen for user input to stop the script
def listen_for_input(event):
    input("\nPress Enter to stop the script\nDetecting...\n")
    event.set()
    with lock:
        condition.notify_all() 


def main():
    global current, lock, condition, check, region, buttons, images, gamepad, num_found, searched, logs, screenshot, stop_event

    pid = os.getpid()
    print(f'\nPID: {pid}')

    current = {}  # Dictionary to store buttons currently on screen
    lock = threading.Lock()  # Lock for thread-safe access to current and searched
    condition = threading.Condition(lock)  # Condition variable to coordinate threads
    check = 0  # Used to see if a double check should occur

    # Setup the gamepad, buttons, and region etc
    region, buttons, images, gamepad, num_found, searched, logs = setup()

    # Taking a screenshot and analyzing it ensures that each thread is looking at the same image
    snapshot = pyautogui.screenshot(region=region)
    screenshot = np.array(snapshot)

    stop_event = threading.Event()

    input_thread = threading.Thread(target=listen_for_input, args=(stop_event,), daemon=True)
    input_thread.start()

    # Create a thread pool for parallel button detection
    with ThreadPoolExecutor(max_workers=len(images)) as executor:
        # Submit tasks for each button
        futures = {
            executor.submit(detect_button, button, cv2.imread(image_path, 0), stop_event, pow(5, 2)): button
            for button, image_path in images.items()
        }

        # Start the thread to process the current dictionary
        process_thread = threading.Thread(target=process_current, args=(buttons, gamepad, region,), daemon=True)
        process_thread.start()

        # Wait for all button detection tasks to complete
        for future in as_completed(futures):
            button = futures[future]
            try:
                future.result()  
            except Exception as e:
                print(f"Error detecting button {button}: {e}")
        executor.shutdown(wait=False)  

    process_thread.join(timeout=1)

    for name, count in num_found.items():
        logs += f"{name}: {count} found\n"

    with open("QTE_logs.txt", "w") as f:
        f.write(logs)

    print("Done")

if __name__ == "__main__":
    main()