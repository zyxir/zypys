"""
This module automates key presses for me in World of Warcraft.

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
        self.state = ""
        self.hWnd = None
        self.stop = False

    def send_alt_g(self):
        print("press Alt-G")
        win32api.PostMessage(self.hWnd, win32con.WM_KEYDOWN, 0x12, 0)
        win32api.PostMessage(self.hWnd, win32con.WM_KEYDOWN, 0x47, 0)
        win32api.PostMessage(self.hWnd, win32con.WM_KEYUP, 0x47, 0)
        win32api.PostMessage(self.hWnd, win32con.WM_KEYUP, 0x12, 0)

    def send_g(self):
        print("Press G")
        win32api.PostMessage(self.hWnd, win32con.WM_KEYDOWN, 0x47, 0)
        win32api.PostMessage(self.hWnd, win32con.WM_KEYUP, 0x47, 0)

    def act(self):
        if self.hWnd is not None:
            if self.state == "mode1":
                self.send_alt_g()
            elif self.state == "mode2":
                self.send_g()
        else:
            print("\rno available window, do not scroll.")

    def run(self):
        while True:
            if self.stop:
                return
            sleep_time = max(0.7, random.gauss(1.0, 0.1))
            time.sleep(sleep_time)
            if self.state:
                self.act()


def start_listening():
    """Start listening for shortcut."""
    pressed = set()
    COMBINATIONS = [
        {
            "keys": [
                {keyboard.Key.f7},
            ],
            "action": "mode1",
        },
        {
            "keys": [
                {keyboard.Key.f8},
            ],
            "action": "mode2",
        },
        {
            "keys": [
                {keyboard.Key.f6},
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
                    elif action != "":
                        hWnd = win32gui.GetForegroundWindow()
                        if hWnd == scroller_thread.hWnd:
                            print(f"toggled ({action})")
                            if scroller_thread.state:
                                scroller_thread.state = ""
                            else:
                                scroller_thread.state = action
                        else:
                            print(f"window changed to {hWnd}, using {action}")
                            scroller_thread.hWnd = hWnd
                            scroller_thread.state = action

    def on_release(key):
        if key in pressed:
            pressed.remove(key)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
        scroller_thread.join()


if __name__ == "__main__":
    start_listening()
