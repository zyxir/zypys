"""

This module automates key presses for me in World of Warcraft.


It is toggled with a global shortcut.
"""


import random
import enum
import time
import threading
from typing import Optional, Union
from pynput import keyboard
import win32api
import win32con
import win32gui


class Mode(enum.Enum):
    PAUSE = "Paused"
    PRESS_G = "Pressing G"
    PRESS_ALT_G = "Pressing Alt-G"


class Printer:
    def __init__(self):
        self.lastMsg: Optional[str] = None
        self.lastRepeat: int = 0

    def printMsg(self, msg: str):
        if msg == self.lastMsg:
            self.lastRepeat += 1
            print(f"\u001b[1F\u001b[0K{msg} (x{self.lastRepeat})")
        else:
            self.lastMsg = msg
            self.lastRepeat = 1
            print(msg)

printMsg = Printer().printMsg


class PresserThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.mode: Mode = Mode.PAUSE
        self.hwnd: Optional[int] = None
        self.stop: bool = False

    def wait(self):
        sleep_time = max(0.03, random.gauss(0.06, 0.01))
        time.sleep(sleep_time)

    def send_alt_g(self):
        if self.hwnd:
            printMsg("press Alt-G")
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, 0x12, 0)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, 0x47, 0)
            self.wait()
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, 0x47, 0)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, 0x12, 0)

    def send_g(self):
        if self.hwnd:
            printMsg("Press G")
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, 0x47, 0)
            self.wait()
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, 0x47, 0)

    def act(self):
        try:
            if self.mode == Mode.PRESS_G:
                self.send_g()
            elif self.mode == Mode.PRESS_ALT_G:
                self.send_alt_g()
        except Exception as e:
            printMsg("The following exception was encountered:")
            printMsg("----------------------------------------")
            printMsg(f"{e}")
            printMsg("----------------------------------------")
            printMsg("Pausing the script.")
            self.mode = Mode.PAUSE
            self.hwnd = None

    def run(self):
        while True:
            if self.stop:
                break
            sleep_time = max(1.0, random.gauss(1.3, 0.1))
            time.sleep(sleep_time)
            self.act()


def start_listening():
    """Start listening for shortcut."""
    printMsg("Start listening...")
    pressed = set()
    COMBINATIONS = [
        {
            "keys": [
                {keyboard.Key.f7},
            ],
            "action": Mode.PRESS_ALT_G,
        },
        {
            "keys": [
                {keyboard.Key.f8},
            ],
            "action": Mode.PRESS_G,
        },
        {
            "keys": [
                {keyboard.Key.f6},
            ],
            "action": "quit",
        },
    ]

    presser_thread = PresserThread()
    presser_thread.start()

    def on_press(key):
        pressed.add(key)

        for c in COMBINATIONS:
            for keys in c["keys"]:
                if keys.issubset(pressed):
                    action = c["action"]
                    dispatch(action)

    def dispatch(action: Union[str, Mode]) -> Optional[bool]:
        if action == "quit":
            presser_thread.stop = True
            printMsg("Quit")
            raise keyboard.Listener.StopException
        elif isinstance(action, Mode):
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == presser_thread.hwnd:
                if presser_thread.mode != Mode.PAUSE:
                    printMsg("Pause")
                    presser_thread.mode = Mode.PAUSE
                else:
                    printMsg(f"Turn on mode \"{action}\"")
                    presser_thread.mode = action
            else:
                printMsg(f"Window changed to {hwnd}, using mode \"{action}\"")
                presser_thread.hwnd = hwnd
                presser_thread.mode = action

    def on_release(key):
        if key in pressed:
            pressed.remove(key)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
        presser_thread.join()


if __name__ == "__main__":
    start_listening()
