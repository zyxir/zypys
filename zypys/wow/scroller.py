"""
This module scrolls the mouse for me while playing World of Warcraft.

It is toggled with a global shortcut.
"""

import random
import time
import threading
from pynput import keyboard
import win32api
import win32con
import win32gui


class ScrollerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.state = False
        self.hWnd = None
        self.stop = False

    def send_alt_g(self):
        print("press Alt-G")
        win32api.PostMessage(self.hWnd, win32con.WM_KEYDOWN, 0x12, 0)
        win32api.PostMessage(self.hWnd, win32con.WM_KEYDOWN, 0x47, 0)
        win32api.PostMessage(self.hWnd, win32con.WM_KEYUP, 0x47, 0)
        win32api.PostMessage(self.hWnd, win32con.WM_KEYUP, 0x12, 0)

    def scroll_down(self):
        print("scroll down")
        wheel_delta = -120 * max(1, random.gauss(3, 1))
        win32api.PostMessage(self.hWnd, win32con.WM_MOUSEWHEEL, wheel_delta, 0)

    def act(self):
        if self.hWnd is not None:
            if random.random() < 0.5:
                self.scroll_down()
            else:
                self.send_alt_g()
        else:
            print("\rno available window, do not scroll.")

    def run(self):
        while True:
            if self.stop:
                return
            sleep_time = max(0.01, random.gauss(0.4, 0.1))
            time.sleep(sleep_time)
            if self.state:
                self.act()


def start_listening():
    """Start listening for shortcut."""
    pressed = set()
    COMBINATIONS = [
        {
            "keys": [
                {keyboard.Key.f8},
            ],
            "action": "toggle",
        },
        {
            "keys": [
                {keyboard.Key.cmd, keyboard.KeyCode(char="q")},
                {keyboard.Key.cmd, keyboard.KeyCode(char="Q")},
            ],
            "action": "quit",
        },
    ]

    scroller_thread = ScrollerThread()
    scroller_thread.start()

    def on_press(key):
        pressed.add(key)

        for c in COMBINATIONS:
            for keys in c["keys"]:
                if keys.issubset(pressed):
                    action = c["action"]
                    if action == "quit":
                        scroller_thread.stop = True
                        return False
                    elif action == "toggle":
                        hWnd = win32gui.GetForegroundWindow()
                        if hWnd == scroller_thread.hWnd:
                            print("toggled")
                            scroller_thread.state = not scroller_thread.state
                        else:
                            print(f"window changed to {hWnd}")
                            scroller_thread.hWnd = hWnd
                            scroller_thread.state = True

    def on_release(key):
        if key in pressed:
            pressed.remove(key)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
        scroller_thread.join()


if __name__ == "__main__":
    start_listening()
